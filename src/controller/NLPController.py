from dis import Instruction
from email.policy import default
import json
from controller import BaseController
from models.db_schemes.minirag.schemes import DataChunk, Project

from stores.vectorDB import VectorDBFactory
from models.ChunkModel import ChunkModel
from stores.llm.LLMEnums import DocumentTypeEnum

class NLPController(BaseController):


    def __init__(self, vectordb_client, generation_client, 
                 embedding_client,template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser


    def create_collection_name (self, project_id):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()

    async def reset_vectordb_collection(self, project:Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name)

    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )

    async def index_into_vectordb(self,project: Project,chunks: list[DataChunk], chunks_ids: list[int], do_reset: bool=False) :

         
       # crate collection name 
        collection_name = self.create_collection_name(project_id=project.project_id)

        # embedding text  
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]

      
        try:

            vectors = self.embedding_client.embed_text(
                texts, DocumentTypeEnum.DOCUMENT.value
            )
        except Exception as exc:
            self.logger.error(f"Embedding failed for collection {collection_name}: {exc}")
            return False

        if not vectors or len(vectors) != len(texts):
            self.logger.error(
                f"Embedding returned empty or mismatched vectors for collection {collection_name}: "
                f"expected={len(texts)}, received={None if vectors is None else len(vectors)}"
            )
            return False

        # crate collection if not exist 
        _= await self.vectordb_client.create_collection( collection_name = collection_name, 
                                                 embedding_size=self.embedding_client.embedding_size , 
                                                 do_reset = do_reset)


        # insert vectores into collection
        _= await self.vectordb_client.insert_many(collection_name=collection_name, 
                                            texts=texts, 
                                            vectors=vectors, 
                                            metadata =metadata, 
                                            record_ids=chunks_ids)

        return True 

    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 5):

        # get collection_name 
        collection_name = self.create_collection_name(project_id=project.project_id)

        query_vector = None 
        # convert the text into vecotr  
        vectors = self.embedding_client.embed_text(text ,DocumentTypeEnum.QUERY.value)

        if not vectors or len(vectors) == 0 : 
            return False 

        if isinstance(vectors[0], (list, tuple)):
            query_vector = vectors[0]
        else:
            query_vector = vectors

        if not query_vector:
            return False 

         
        # seart on vectore database 
        results = await self.vectordb_client.search_by_vector(collection_name=collection_name, vector=query_vector, limit=limit)


        if not results:
            return False

        return results


    async def answer_rag_question(self, project: Project, query: str, limit: int = 10):


        answer, full_prompt, chat_history = None, None, None

        # step1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, chat_history
        
        # step2: Construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt = self.template_parser.get("rag", "footer_prompt")

        # step3: Construct Generation Client Prompts
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ]

        full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history

