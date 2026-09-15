
import os 
from fastapi import  APIRouter , UploadFile , File , Depends , status , Request 
from  fastapi.responses import JSONResponse 
from helpers.Config import get_settings , Settings 
from controller import DataController ,ProjectController , ProcessController
from models import ResponseSignal
from controller import NLPController

from models.db_schemes.minirag.schemes import DataChunk, Project, Asset

from .schemes.data import ProcessRequest
from models import ProjectModel , BaseModel , ChunkModel , AssetModel
from models.Enums.AssetTypeEnum import AssetTypeEnum
import aiofiles
import logging 

logger = logging.getLogger(__name__)

logger = logging.getLogger('uvicorn.error')

data_route = APIRouter(
    prefix = "/data"
)

@data_route.post('/upload_files/{project_id}') 
async def uploade(request : Request ,project_id: int, file: UploadFile = File(...), app_settings: Settings = Depends(get_settings)):

       #ihave to get the db client from the app to pass it to Project class  so iwill use Request  
       

        project_model = await ProjectModel.create_instance(
             db_client=request.app.client_db)

        project = await project_model.get_project_or_create(project_id = project_id)


       
       
        # we will split the logic of processing the file  { we will do it on Controller /  layer}  
        is_valid , status_code =  DataController().validate_uploaded_file(file = file) 
        
        if not is_valid : 
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content ={
                'signal' : status_code 
            }
        )

        #1  get the project path from project id 
        #2 generate unique file path name for the file to upload
            
        project_dir_path = ProjectController().get_project_path(project_id=project_id)
        file_path, file_id = DataController().generate_unique_filepath(
            orig_file_name=file.filename,
            project_id=project_id
        )
        # write the uploaded file as binary in  the  unique file Path that we made  
        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
        except Exception as e:

            logger.error(f"Error while uploading file: {e}")

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
                }
            )

    # STORE THE ASSET[FILE] INTO DATABASE   

        asset_model = await AssetModel.create_instance(
             db_client=request.app.client_db
        )

        asset_resource = Asset(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )

        asset_record =await asset_model.create_asset(asset_resource) 


        return JSONResponse(
                content={
                    "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                    "file_id": str(asset_record.asset_name),
            
                }
            )



@data_route.post('/process/{project_id}')        
async def process(project_id: int , processrequest: ProcessRequest , request :Request):
     
# get From the json request 
  # file_id = None 
    chunk_size = processrequest.chunk_size 
    overlap_size = processrequest.overlap_size 
    do_reset = processrequest.do_reset



# I cant get the file_id from user or from the asset collection directly  

    project_model = await ProjectModel.create_instance(
        request.app.client_db 
    )

    project = await project_model.get_project_or_create(
        project_id=project_id 
    )

    asset_model = await AssetModel.create_instance(
           request.app.client_db 
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,)
    
# if the user sent the file_id 
    
    project_files_ids = {}
    if processrequest.file_id :

        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.project_id ,
            asset_name=processrequest.file_id 
        ) 

        if asset_record is None :

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )
        else:
            project_files_ids = {
                asset_record.id : asset_record.asset_name
            }

    else :
# if user didnt pass the file_id  get all files thats in project_id 
#___________________________________

        project_files = await asset_model.get_all_project_assets(
            asset_project_id = project.project_id , asset_type = AssetTypeEnum.FILE.value
        )

        project_files_ids = {
            record.asset_id: record.asset_name
            for record in project_files
        }

        if len(project_files_ids) == 0:
             return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.NO_FILES_ERROR.value,
                }
            )

    no_records = 0 
    no_files   = 0 

    chunk_model = await ChunkModel.create_instance(
            request.app.client_db 
        )
    
# check if do_reset is True to delete all chunk realted with project_id 
    if do_reset == 1 :

        # delete associated vectors collection
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        _= await chunk_model.delete_chunks_by_project_id(project_id = project.project_id)



    for asset_id , file_id in project_files_ids.items():
    
        # process file content  & Chunks it 

        process_controller = ProcessController(project_id=project_id)
        file_content = process_controller.get_file_content(file_id)

        
        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue
            
        file_chunks = process_controller.process_file_content(
                file_content=file_content ,
                    chunk_size=chunk_size, 
                    overlap_size=overlap_size )
            
        if file_chunks == None or len(file_chunks) == 0 : 
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content = {
                    "signal" : ResponseSignal.PROCESSING_FAILED.value
                }
            ) 

# save the chunked data to database 
#__________________________________

        file_chunks_records = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i+1,
                    chunk_project_id=project.project_id,
                    chunk_asset_id = asset_id
            
                )
                for i, chunk in enumerate(file_chunks)
            ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )