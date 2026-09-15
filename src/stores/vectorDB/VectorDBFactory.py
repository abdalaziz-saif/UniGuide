from stores.vectorDB.providers.QdrantDBProvider import QdrantDBProvider
from stores.vectorDB.providers.PGVectorProvider import PGVectorProvider
from controller import BaseController
from .VectorDBEnums import VectorDBProvider, DistnaceMethode

class VectorDBFactory:

    def __init__(self, config: dict):

        self.config = config 
        self.basecontroller = BaseController()

    def create(self, provider: str):
        vectordb_path = self.basecontroller.database_file_path(db_name = self.config.VECTOR_DB_PATH)

        if provider ==  VectorDBProvider.QDRANT.value :

            return QdrantDBProvider(file_path = vectordb_path,
                                    distance_methode = self.config.VECTOR_DB_DISTANCE_METHOD)


        if provider == VectorDBEnums.PGVECTOR.value:
            
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        
        return None