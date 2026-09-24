from .BaseModel import BaseDataModel
from .db_schemes import Conversation
from sqlalchemy import select


class ConversationModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_conversation(self, conversation: Conversation):

        async with self.db_client() as session:
            async with session.begin():
                session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: int, project_id: int):

        async with self.db_client() as session:
            query = select(Conversation).where(
                Conversation.conversation_id == conversation_id,
                Conversation.conversation_project_id == project_id,
            )
            result = await session.execute(query)
            conversation = result.scalar_one_or_none()
        return conversation
