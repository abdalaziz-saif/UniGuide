from dis import Instruction
from email.policy import default
import json
from controller import BaseController
from models.db_schemes.data_chunk import DataChunk
from models.db_schemes.project import Project
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
        self.template_parser = self.template_parser


    def create_collection_name (self, project_id):
        return f"collection_{project_id}".strip()

    def reset_vectordb_collection(self, project:Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.load(
            json.dumb(collection_info, default=lambda x: x.__dict__)
        )

    def index_into_vectordb(self,project: Project,chunks: list[DataChunk], chunks_ids: list[int], do_reset: bool=False) :

         
       # crate collection name 
        collection_name = self.create_collection_name(project_id=project.project_id)

        # embedding text  
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]

        vectors = [

               self.embedding_client.embed_text(text ,DocumentTypeEnum.DOCUMENT.value )
            for text in texts 
        ]

        # crate collection if not exist 
        _=self.vectordb_client.create_collection( collection_name = collection_name, 
                                                 embedding_size=self.embedding_client.embedding_size , 
                                                 do_reset = do_reset)


        # insert vectores into collection
        _= self.vectordb_client.insert_many(collection_name=collection_name, 
                                            texts=texts, 
                                            vectors=vectors, 
                                            metadata =metadata, 
                                            record_ids=chunks_ids)

        return True 

    def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):

        # get collection_name 
        collection_name = self.create_collection_name(project_id=project.project_id)

        # convert the text into vecotr  
        vector = self.embedding_client.embed_text(text ,DocumentTypeEnum.QUERY.value)

        # seart on vectore database 
        results = self.vectordb_client.search_by_vector(collection_name=collection_name, vector=text, limit=limit)


        if not results:
            return False

        return results


    def answer_rag_question(self, project: Project, query: str, limit: int = 10):


        answer, full_prompt, chat_history = None, None, None

        # step1: retrieve related documents
        retrieved_documents = self.search_vector_db_collection(
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
                    "chunk_text": doc.text,
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

