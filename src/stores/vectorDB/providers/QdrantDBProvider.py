from pydoc import text

from ..VectorInterface import VectorDBInterface 
from qdrant_client import QdrantClient
from qdrant_client.models  import VectorParams  ,PointStruct
import logging
from typing import List
from models.db_schemes import RetrievedDocument 






class QdrantDBProvider(VectorDBInterface):

    async def  __init__(self, file_path: str, distance_methode: str):

        self.client = None
        self.file_path = file_path
        self.distance_methode = distance_methode
        self.logger = logging.getLogger('uvicorn')

    async def  connect(self):
        self.client = QdrantClient(path= self.file_path)

    async def  disconnect(self):
        self.client = None 


    async def  is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)
        
    async def  list_all_collections(self) -> List:
        return self.client.get_collections()

    async def  delete_collection(self, collection_name: str): 

        if self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name=collection_name)

    async def  get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)

    async def  create_collection(self, collection_name, embedding_size, do_reset = False):

        if do_reset : 
           _= self.delete_collection(collection_name) 

        if not self.is_collection_existed(collection_name):
            _= self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=embedding_size, distance=self.distance_methode),
            )

            return True 

        return False 

    async def  insert_one(self, collection_name, text, vector, metadata = None, record_id = None):

        if not self.is_collection_existed(collection_name):
            self.logger.error ("collection is not exist")
            return False     

        try : 
            _=self.client.upsert(
                collection_name=collection_name,
                points=[
                PointStruct(
                    id = record_id,
                        vector= vector,
                        payload={
                            'text' :text ,
                            'metadata' : metadata
                        },
                )] 
            )
        except Exception as e: 
            self.logger.error(f"Error while inserting record : {e}")
            return False


        return True 


    async def   insert_many(self, collection_name, texts, vectors, metadata = None, record_ids = None, batch_size = 50):


        if metadata == None :
            metadata = [None] * len(texts)

        if record_ids == None : 
            record_ids = list(range(0, len(texts)))


        for i in range (0, len(texts), batch_size):

            batch_texts = texts[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            batch_record_ids = record_ids[i:i+batch_size]

            points = [
                PointStruct(
                    id=record_id,
                    vector=vector,
                    payload={
                        'text': text, 'metadata': item_metadata
                    }
                )
                for record_id, vector, text, item_metadata in zip(
                    batch_record_ids, batch_vectors, batch_texts, batch_metadata
                )
            ]
            try :
               _=  self.client.upsert(
                collection_name=collection_name,
                points=points
               )
            except Exception as e : 
                self.logger.error(f"Error while inserting records : {e}")
                return False

            return True

    async def  search_by_vector(self, collection_name: str, vector: list, limit: int = 5):

            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=collection_name,
                    query=vector,
                    limit=limit,
                )
                results = response.points
            else:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=vector,
                    limit=limit,
                )

            if not results or len(results)== 0 :
                return None 


            return [

                RetrievedDocument(
                    **{
                        "score": result.score , 
                        "text": result.payload['text']
                    }
                )

                for result in results 
            ]