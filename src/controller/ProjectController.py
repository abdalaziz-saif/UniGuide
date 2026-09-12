from .BaseController import BaseController
import os


class ProjectController(BaseController):

    def __init__(self):
        super().__init__()

    # get the project path from project id 
    def get_project_path(self, project_id: str):
        project_path = os.path.join(
            self.files_dir,
            str(project_id) 
        )

        if not os.path.exists(project_path) : 
            os.makedirs(project_path)

        return project_path 