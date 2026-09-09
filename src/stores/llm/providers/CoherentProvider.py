from ..LLMInterface import llm_interface 
from ..LLMEnums import CoHereEnums,DocumentTypeEnum
import logging
import cohere


class CohereProvider(llm_interface):

    def __init__(self , api_key: str , api_url: str=None,
                       default_input_max_characters: int=1000,
                       default_generation_max_output_tokens: int=1000,
                       default_generation_temperature: float=0.1):

        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.embedding_model_id = None 

        self.generation_model_id = None 
        self.embedding_size = None

        self.client = cohere.Client(
            api_key = self.api_key,
            base_url = self.api_url
        )

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id):
        self.generation_model_id = model_id 

    def set_embedding_model(self, model_id, embedding_size = None):
        self.embedding_model_id = model_id 
        self.embedding_size = embedding_size 

    def process_text(self , text):
        return text[:self.default_input_max_characters]


    def generate_text(self, prompt, chat_history = [], max_output_tokens = None, temperature = None):

        if not self.client :
            self.logger.error("cohere client is not set")
            return None 

        if not self.generation_model_id:
            self.logger.error("Chohere generation model is not set")
            return None 

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature 
        
        response = self.client.chat(
            model = self.generation_model_id,
            chat_history = chat_history,
            message = self.process_text(prompt),
            temperature = temperature,
            max_tokens = max_output_tokens
        )

        if not response or not response.text:
            self.logger.error("Error while generating text with CoHere")
            return None
        
        return response.text
    
    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None


        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        response = self.client.embed(
            model = self.embedding_model_id,
            texts = [self.process_text(text)],
            input_type = input_type,
            embedding_types=['float'],
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding text with CoHere")
            return None
        
        return response.embeddings.float[0] 

    def embed_texts(self, texts: list[str], document_type: str = None):
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None

        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[self.process_text(text) for text in texts],
            input_type=input_type,
            embedding_types=['float'],
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding texts with CoHere")
            return None

        return response.embeddings.float

    def construct_prompt(self, prompt: str, role: str):
        return {
            'role' : role,
            'text': self.process_text(prompt)
        }   