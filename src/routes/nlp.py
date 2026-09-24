from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controller import NLPController
from models import ResponseSignal, ConversationModel, MessageModel
from models.db_schemes.minirag.schemes import Conversation, Message
from tqdm.auto import tqdm



nlp_router = APIRouter(
    prefix = "/nlp"
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):

    
    
        project_model = await ProjectModel.create_instance(
             db_client=request.app.client_db)

        

        chunk_model = await ChunkModel.create_instance(
                db_client=request.app.client_db)


        project = await project_model.get_project_or_create(project_id=project_id)

        if not project:
            return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
    

        

        nlp_Controller = NLPController(vectordb_client=request.app.vectordb_client, 
                 embedding_client = request.app.embedding_model , 
                 generation_client = request.app.generation_model,
                 template_parser=request.app.template_parser,
        )

        has_records = True
        page_no = 1
        inserted_items_count = 0
        idx = 0

        # create collection if not exists
        collection_name = nlp_Controller.create_collection_name(project_id=project.project_id)

        _ = await request.app.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=request.app.embedding_client.embedding_size,
            do_reset=push_request.do_reset,
        )

        # setup batching
        total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)

        while has_records:
            page_chunks = await chunk_model.get_poject_chunks(project_id=project.project_id, page_no=page_no)
            if len(page_chunks):
                page_no += 1
            
            if not page_chunks or len(page_chunks) == 0:
                has_records = False
                break

            chunks_ids =  [p.chunk_id for p in page_chunks]
            idx += len(page_chunks)
            
            is_inserted = await nlp_Controller.index_into_vectordb(
                project=project,
                chunks=page_chunks,
                do_reset=bool(push_request.do_reset) and page_no == 2,
                chunks_ids=chunks_ids
            )

            if not is_inserted:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                    }
                )
            
            inserted_items_count += len(page_chunks)
            
        return JSONResponse(
            content={
                "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                "inserted_items_count": inserted_items_count
            }
        )

@nlp_router.get("/index/info/{project_id}")
async def get_collection_info(request:Request, project_id: int ):

        project_model = await ProjectModel.create_instance(
                     db_client=request.app.client_db)

        project = await project_model.get_project_or_create(project_id=project_id)

        nlp_Controller = NLPController(vectordb_client=request.app.vectordb_client, 
                 embedding_client = request.app.embedding_model , 
                 generation_client = request.app.generation_model,
                 template_parser=request.app.template_parser
        )

        collection_info = await nlp_Controller.get_vector_db_collection_info(project)

        return JSONResponse(
            content={
                "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
                "collection_info": collection_info
            }
        )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: int, search_request: SearchRequest):



        project_model = await ProjectModel.create_instance(
                     db_client=request.app.client_db)

        project = await project_model.get_project_or_create(project_id=project_id)

        nlp_Controller = NLPController(vectordb_client=request.app.vectordb_client, 
                 embedding_client = request.app.embedding_model , 
                 generation_client = request.app.generation_model,
        template_parser=request.app.template_parser,
    )

        results = await nlp_Controller.search_vector_db_collection(
            project=project, text=search_request.text, limit=search_request.limit
        )

        if not results:
            return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
                    }
                )
        
        return JSONResponse(
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
                "results": [ result.dict()  for result in results ]
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):


        project_model = await ProjectModel.create_instance(
                     db_client=request.app.client_db)

        project = await project_model.get_project_or_create(project_id=project_id)

        conversation_model = await ConversationModel.create_instance(
            db_client=request.app.client_db
        )
        message_model = await MessageModel.create_instance(
            db_client=request.app.client_db
        )

        if search_request.conversation_id is None:
            conversation = await conversation_model.create_conversation(
                Conversation(conversation_project_id=project.project_id)
            )
        else:
            conversation = await conversation_model.get_conversation(
                conversation_id=search_request.conversation_id,
                project_id=project.project_id,
            )

            if conversation is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "signal": ResponseSignal.CONVERSATION_NOT_FOUND_ERROR.value
                    },
                )

        previous_messages = await message_model.get_recent_messages(
            conversation_id=conversation.conversation_id,
            limit=20,
        )

        await message_model.create_message(
            Message(
                message_conversation_id=conversation.conversation_id,
                role="user",
                content=search_request.text,
            )
        )

        nlp_Controller = NLPController(vectordb_client=request.app.vectordb_client, 
                 embedding_client = request.app.embedding_model , 
                 generation_client = request.app.generation_model,
        template_parser=request.app.template_parser,
    )

        answer, full_prompt, chat_history = await nlp_Controller.answer_rag_question(
            project=project,
            query=search_request.text,
            chat_history=previous_messages,
            limit=search_request.limit,
        )

        if not answer:
            return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                    }
            )

        await message_model.create_message(
            Message(
                message_conversation_id=conversation.conversation_id,
                role="assistant",
                content=answer,
            )
        )
        
        return JSONResponse(
            content={
                "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
                "answer": answer,
                "full_prompt": full_prompt,
                "chat_history": chat_history,
                "conversation_id": conversation.conversation_id,
            }
        )
