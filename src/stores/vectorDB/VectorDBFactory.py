from stores.vectorDB.providers.QdrantDBProvider import QdrantDBProvider
from stores.vectorDB.providers.PGVectorProvider import PGVectorProvider
from controller import BaseController
from .VectorDBEnums import VectorDBEnums
from sqlalchemy.orm import sessionmaker

class VectorDBFactory:

    def __init__(self, config: dict, db_client: sessionmaker=None):

        self.config = config 
        self.basecontroller = BaseController()
        self.db_client = db_client

    def create(self, provider: str):
        vectordb_path = self.basecontroller.database_file_path(db_name = self.config.VECTOR_DB_PATH)
        provider_name = str(provider).upper()

        if provider_name == VectorDBEnums.QDRANT.value:

            return QdrantDBProvider(
                file_path=vectordb_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )


        if provider_name == VectorDBEnums.PGVECTOR.value:
            
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )
        
        return None