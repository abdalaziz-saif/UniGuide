from fastapi import FastAPI , APIRouter 
from routes import data
from routes import base
from routes import nlp
from motor.motor_asyncio import AsyncIOMotorClient  
from helpers import get_settings 
from stores.llm import LLMFactory
from stores.llm.template.template_parser import Templateparser
from stores.vectorDB import VectorDBFactory
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


app = FastAPI()

# make motor connect directly when startup the app 
@app.on_event('startup') 
async def on_start_up():
    settings = get_settings()

    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

    app.db_engine = create_async_engine(
        postgres_conn,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
    app.client_db = sessionmaker(
        app.db_engine, class_=AsyncSession, expire_on_commit=False
    )

    llm_provider_factory = LLMFactory(settings)

    # generation model
    app.generation_model = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_model.set_generation_model(settings.GENERATION_MODEL_ID)
    app.generation_client = app.generation_model

    # embedding model
    app.embedding_model = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_model.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE)
    app.embedding_client = app.embedding_model

    # vector db client
    app.vectordb_client = VectorDBFactory(
        config=settings,
        db_client=app.client_db,
    ).create(provider=settings.VECTOR_DB_BACKEND)
    if app.vectordb_client is None:
        raise RuntimeError(f"Unsupported vector DB backend: {settings.VECTOR_DB_BACKEND}")
    await app.vectordb_client.connect()


    #Generationn Template 
    app.template_parser = Templateparser(
        language=settings.PRIMARY_LANGUAGE,
        default_language=settings.DEFAULT_LANGUAGE
    )
    

# turn it off when shutdown app 
@app.on_event('shutdown')
async def on_shutdown():
    await app.vectordb_client.disconnect()
  
# include the base_route in the main app
app.include_router(base.base_route)
app.include_router(data.data_route)
app.include_router(nlp.nlp_router)