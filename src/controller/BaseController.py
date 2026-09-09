
from helpers.Config  import get_settings   
import os 
import random 
import string 

class BaseController : 

    def __init__(self):

        self.app_settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__)) #get base file dirs of the project 
        self.files_dir = os.path.join(self.base_dir , self.app_settings.FILES_DIR) # get the files dir path

        # get the vector db filepath 
        self.database_dir = os.path.join(self.base_dir,  "assets/database")

    # generate random string to added to file_path name 
    def generate_random_string(self, length: int=12):
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def database_file_path(self , db_name):

         path = os.path.join(
              self.files_dir ,
              db_name 
         ) 

         if not os.path.exists(path):
              os.makedirs(path)

         return path 