from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME : str 
    APP_VERSION : str
    OPENAI_API_KEY : str 
    
    FILE_ALLOWED_TYPES : list  
    FILE_MAX_SIZE :int 
    FILES_DIR : str
    FILE_DEFAULT_CHUNK_SIZE :int 

    POSTGRES_USERNAME: str="postgres"
    POSTGRES_PASSWORD: str="PASSWORD"
    POSTGRES_HOST: str="localhost"
    POSTGRES_PORT: int=5432
    POSTGRES_MAIN_DATABASE: str="minirag"

    GENERATION_BACKEND :str
    EMBEDDING_BACKEND  :str
    
    OPENAI_API_KEY :str
    OPENAI_API_URL :str
    COHERE_API_KEY :str 
    
    GENERATION_MODEL_ID :str
    EMBEDDING_MODEL_ID :str 
    EMBEDDING_MODEL_SIZE :int
    
    INPUT_DAFAULT_MAX_CHARACTERS :int
    GENERATION_DAFAULT_MAX_TOKENS :int
    GENERATION_DAFAULT_TEMPERATURE :float 

    VECTOR_DB_BACKEND : str  
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str 

    # ========================= Generation Language Config =========================
    PRIMARY_LANGUAGE : str
    DEFAULT_LANGUAGE : str 


def get_settings():
    return Settings()