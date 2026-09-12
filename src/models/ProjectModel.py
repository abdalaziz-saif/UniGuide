from .BaseModel import BaseDataModel
from .db_schemes import Project
from .Enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):

    def __init__(self , db_client):
        super().__init__(db_client=db_client)

        self.db_client = db_client

# buz of the problem that index function is async and init is not iwill make create_instance func

    @classmethod 
    async def create_instance(cls ,db_client):
         instance = cls(db_client)
         return instance 


         
# create a  project inside the collection 
    async def create_project(self, project : Project):

        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)


    async def get_project_or_create(self, project_id):

        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                if project is None:
                    project_rec = Project(
                        project_id = project_id
                    )

                    project = await self.create_project(project=project_rec)
                    return project
                else:
                    return project


    async def get_all_projects(self, page: int=1, page_size: int=10):

        async with self.db_client() as session:
            async with session.begin():

                total_documents = await session.execute(select(
                    func.count( Project.project_id )
                ))

                total_documents = total_documents.scalar_one()

                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                query = select(Project).offset((page - 1) * page_size ).limit(page_size)
                projects = await session.execute(query).scalars().all()

                return projects, total_pages
