from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
import logging
from langchain_docling.loader import DoclingLoader 
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)

class ProcessController(BaseController):

    def __init__(self , project_id):
        super().__init__() 


        self.project_id = project_id 
        self.project_path = ProjectController().get_project_path(self.project_id) 
      
    #extract the content of the file using langchain
    def get_file_content(self , file_id) :
        if file_id :
            self.file_path = os.path.join(
                self.project_path , 
                file_id
            )
        
            try:
                file_extension = os.path.splitext(self.file_path)[1].lower()

                if file_extension in (".txt", ".text"):
                    with open(self.file_path, "r", encoding="utf-8", errors="replace") as file:
                        return [
                            Document(
                                page_content=file.read(),
                                metadata={"source": file_id},
                            )
                        ]

                loader = DoclingLoader(self.file_path)
                return loader.load()  # the output will be in shape document(text =  , metadata = )
            except Exception as exc:
                logger.exception("Error while extracting file %s: %s", self.file_path, exc)
                return None
        return None 
    # split the content to chunks  
    def process_file_content(self , file_content :list , chunk_size : int =100  , overlap_size :int =20):

            text_spliter = RecursiveCharacterTextSplitter(
                 chunk_size = chunk_size , 
                 chunk_overlap = overlap_size , 
                 length_function=len
                 )


            file_content_text = [
                    rec.page_content
                 for rec in file_content 
            ]
            
            file_content_metadata = [
                    rec.metadata
                 for rec in file_content
            ]
        
         
            chunks = text_spliter.create_documents(
                file_content_text,
                 metadatas=file_content_metadata
            )
            
            return chunks 
  
