import os
from typing import Dict, Any, Optional, List
from mistralai import Mistral
#from mistralai.models.chat_completion import ChatMessage
import discord
from dotenv import load_dotenv
import functools
import json
import logging
import hashlib
import redis
import faiss
import requests
import numpy as np
import pickle
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Cache paths
CACHE_DIR = "cache"
EMBEDDINGS_CACHE = os.path.join(CACHE_DIR, "embeddings.pkl")
CHUNKS_CACHE = os.path.join(CACHE_DIR, "chunks.pkl")

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize Redis cache
cache = redis.Redis(host='localhost', port=6379, db=0)

# Function: retrieve from semantic cache
def check_cache(query):
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    cached_response = cache.get(query_hash)
    if cached_response:
        return cached_response.decode('utf-8')  # Decode bytes to string
    return None

# Function: Store in Semantic Cache
def store_in_cache(prompt, response):
    query_hash = hashlib.sha256(prompt.encode()).hexdigest()
    if isinstance(response, str):
        response = response.encode('utf-8')  # Ensure response is in bytes
    cache.set(query_hash, response, ex=3600)


MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """I am a specialized medical assistant with access to patient health records. I can help you with:
How may I assist you with supporting your workflow as a doctor today?"""

class MistralAgent:
    def __init__(self):

        # Get api key
        load_dotenv()
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        if not MISTRAL_API_KEY:
            raise ValueError("No Mistral API key found. Please set MISTRAL_API_KEY in your .env file")
        
        # Initiate client
        self.client = Mistral(api_key=MISTRAL_API_KEY)

        # Initiate patient data
        self.patient_data: Optional[Dict[str, Any]] = None

        # Load or create RAG components
        self.chunks = self.load_or_create_chunks()
        self.index = self.load_or_create_index()
        
        # Define tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "retrieve_allergy_info",
                    "description": "Get allergy information for a patient. No parameters needed as this function uses the currently loaded patient data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_diagnostic_report_info",
                    "description": "Get diagnostic report information for a patient. No parameters needed as this function uses the currently loaded patient data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_condition_info",
                    "description": "Get condition information for a patient. No parameters needed as this function uses the currently loaded patient data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_relevant_info_for_ICD_code",
                    "description": "Retrieve relevant information for generating an ICD-10 code. No parameters needed as this function uses the currently loaded patient data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_patient_info",
                    "description": "Retrieve patient context. No parameters needed as this function uses the currently loaded patient data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
            },
        ]

        self.names_to_functions = {
            'retrieve_allergy_info': self.retrieve_allergy_info,
            'retrieve_diagnostic_report_info': self.retrieve_diagnostic_report_info,
            'retrieve_condition_info': self.retrieve_condition_info,
            'retrieve_relevant_info_for_ICD_code': self.retrieve_relevant_info_for_ICD_code,
            'retrieve_patient_info': self.retrieve_patient_info,
        }

    def load_or_create_chunks(self):
        """Load chunks from cache or create new ones"""
        if os.path.exists(CHUNKS_CACHE):
            logger.info("Loading chunks from cache...")
            with open(CHUNKS_CACHE, 'rb') as f:
                return pickle.load(f)
        
        logger.info("Creating new chunks...")
        chunks = self.create_chunks()
        with open(CHUNKS_CACHE, 'wb') as f:
            pickle.dump(chunks, f)
        return chunks

    def load_or_create_index(self):
        """Load index and embeddings from cache or create new ones"""
        if os.path.exists(EMBEDDINGS_CACHE):
            logger.info("Loading embeddings from cache...")
            with open(EMBEDDINGS_CACHE, 'rb') as f:
                text_embeddings = pickle.load(f)
        else:
            logger.info("Creating new embeddings...")
            text_embeddings = np.array([self.get_text_embedding(chunk) for chunk in self.chunks])
            with open(EMBEDDINGS_CACHE, 'wb') as f:
                pickle.dump(text_embeddings, f)

        d = text_embeddings.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(text_embeddings)
        return index

    def create_chunks(self):
        response = requests.get('https://www.opm.gov/healthcare-insurance/healthcare/plan-information/plans/pdf/2025/brochures/71-005.pdf')
        text = response.text
        chunk_size = 2048
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        logger.info(f"Taking the first 1 out of {len(chunks)} chunks")
        return chunks[:1]
    
    def get_text_embedding(self, input):
        embeddings_batch_response = self.client.embeddings.create(
            model="mistral-embed",
            inputs=input
        )
        return embeddings_batch_response.data[0].embedding
    
    def set_patient_data(self, patient_data: Dict[str, Any]) -> None:
        self.patient_data = patient_data

    def retrieve_allergy_info(self, **kwargs) -> str:
        """Get allergy information for the current patient.
        
        This function uses the currently loaded patient data and ignores any parameters passed to it.
        """
        if 'allergies' in self.patient_data:
            allergies = self.patient_data['allergies']
            allergy_context = (
                "Allergy Information:\n"
                f"Allergy: {allergies.get('allergy_name', 'Unknown')}\n"
                f"Status: {allergies.get('clinical_status', 'Unknown')}\n"
                f"Onset Date: {allergies.get('onset_date', 'Unknown')}\n"
            )
            
            if 'reactions' in allergies:
                allergy_context += "Reactions:\n"
                for reaction in allergies['reactions']:
                    if 'description' in reaction:
                        allergy_context += f"  - {reaction['description']}\n"
                    if 'manifestations' in reaction:
                        allergy_context += f"    Manifestations: {', '.join(reaction['manifestations'])}\n"
            return allergy_context
        else:
            return "No allergy information available for this patient."
        
    def retrieve_diagnostic_report_info(self, **kwargs) -> str:
        """Get diagnostic report information for the current patient.
        
        This function uses the currently loaded patient data and ignores any parameters passed to it.
        """
        if 'diagnostic_report' in self.patient_data:
            dr = self.patient_data['diagnostic_report']
            diagnostic_context = (
                "Diagnostic Report Information:\n"
                f"Report Name: {dr.get('report_name', 'Unknown')}\n"
                f"Status: {dr.get('status', 'Unknown')}\n"
                f"Date: {dr.get('effective_date', 'Unknown')}\n"
            )
            
            if 'categories' in dr:
                diagnostic_context += f"Categories: {', '.join(dr['categories'])}\n"
            
            if 'providers' in dr:
                diagnostic_context += f"Providers: {', '.join(dr['providers'])}\n"
            
            if 'result_references' in dr:
                diagnostic_context += "Results:\n"
                for result in dr['result_references']:
                    diagnostic_context += f"  - {result}\n"
            
            return diagnostic_context
        else:
            return "No diagnostic report information available for this patient."
        
    def retrieve_condition_info(self, **kwargs) -> str:
        """Get condition information for the current patient.
        
        This function uses the currently loaded patient data and ignores any parameters passed to it.
        """
        if 'conditions' in self.patient_data:
            conditions = self.patient_data['conditions']
            condition_context = (
                "Medical Condition Information:\n"
                f"Condition: {conditions.get('condition_name', 'Unknown')}\n"
                f"Status: {conditions.get('clinical_status', 'Unknown')}\n"
                f"Onset Date: {conditions.get('onset_date', 'Unknown')}\n"
            )
            
            if 'notes' in conditions:
                condition_context += "Clinical Notes:\n"
                for note in conditions['notes']:
                    condition_context += f"  {note}\n"
            
            return condition_context
        else:
            return "No condition information available for this patient."
        
    def retrieve_relevant_info_for_ICD_code(self, **kwargs) -> str:
        """Retrieve relevant information for generating an ICD-10 code.
        
        This function uses the currently loaded patient data and ignores any parameters passed to it.
        """
        
        retrieve_condition_info = self.retrieve_condition_info()
        retrieve_diagnostic_report_info = self.retrieve_diagnostic_report_info()
        retrieve_allergy_info = self.retrieve_allergy_info()

        return f"Retrieved information for ICD-10 code generation:\n" \
            f"Condition Info: {retrieve_condition_info}\n" \
            f"Diagnostic Report Info: {retrieve_diagnostic_report_info}\n" \
            f"Allergy Info: {retrieve_allergy_info}\n"
    
    def retrieve_patient_info(self, **kwargs) -> str:
        """Retrieve patient context.
        
        This function uses the currently loaded patient data and ignores any parameters passed to it.
        """
        
        return f"""
            Name: {self.patient_data.get('name', 'Unknown')}\n
            Date of Birth: {self.patient_data.get('dob', 'Unknown')}\n
            Medical Record Number: {self.patient_data.get('mrn', 'Unknown')}\n
            Insurance Provider: {self.patient_data.get('provider', 'Unknown')}\n
            Member ID: {self.patient_data.get('memberId', 'Unknown')}\n
            Group Number: {self.patient_data.get('groupNumber', 'Unknown')}\n
            Effective Date: {self.patient_data.get('effectiveDate', 'Unknown')}\n\n
            Use this information to answer the user's question if relevant.
        """
    
    def generate_prompt(self, user_message, retrieved_chunk):
        prompt = f"""
            Context information is below.
            ---------------------
            Patient Information: {self.retrieve_patient_info()}
            Insurance Information: {retrieved_chunk}
            ---------------------
            Given the context information and not prior knowledge, answer the query.
            Query: {user_message}
            Answer:
        """
        return prompt

    async def run_mistral_tools(self, messages, model = MISTRAL_MODEL):
        logger.info("Making initial API call with tools...")
        response = await self.client.chat.complete_async(
            model = model,
            messages = messages,
            tools = self.tools,
            tool_choice = "auto"
        )

        # Check if the model made tool calls
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            
            # Process all tool calls
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                
                # Handle empty arguments case
                try:
                    function_params = json.loads(tool_call.function.arguments or '{}')
                except json.JSONDecodeError:
                    function_params = {}
                
                logger.info(f"Called tool function: {function_name} with params: {function_params}")
                
                # Call the function and get result
                function_result = self.names_to_functions[function_name](**function_params)
                messages.append({
                    "role": "tool",
                    "name": function_name,
                    "content": function_result,
                    "tool_call_id": tool_call.id
                })

        return messages

    async def run(self, message: discord.Message) -> str:
        
        # Get user message
        user_message = message.content

        # Check cache for existing response
        cached_response = check_cache(user_message)
        if cached_response:
            logger.info("Returning cached response...")
            return cached_response

        # Get the top 2 chunks
        question_embeddings = np.array([self.get_text_embedding(user_message)])
        D, I = self.index.search(question_embeddings, k=2) # distance, index
        retrieved_chunk = [self.chunks[i] for i in I.tolist()[0]]

        # Create prompt
        prompt = self.generate_prompt(user_message, retrieved_chunk)

        # Create messages
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        messages = await self.run_mistral_tools(messages)

        #response = self.run_mistral(messages, MISTRAL_MODEL)
        response = await self.client.chat.complete_async(
            model = MISTRAL_MODEL,
            messages = messages
        )
        response = response.choices[0].message.content

        # Store response in cache
        store_in_cache(user_message, response)
        return response