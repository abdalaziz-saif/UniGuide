from stores.vectorDB.providers.QdrantDBProvider import QdrantDBProvider
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

        return None 
    