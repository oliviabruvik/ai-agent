import os
from typing import Dict, Any, Optional, List
from mistralai import Mistral
#from mistralai.models.chat_completion import ChatMessage
import discord
from dotenv import load_dotenv
import functools
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """I am a specialized medical assistant with access to patient health records. I can help you with:
- Viewing the medical information of your patients
- Understanding your diagnoses and conditions
- Checking the allergies and medications of your patients
- Reviewing recent diagnostic reports
- Answering questions about your patients' healthcare coverage

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
            }
        ]

        self.names_to_functions = {
            'retrieve_allergy_info': self.retrieve_allergy_info,
            'retrieve_diagnostic_report_info': self.retrieve_diagnostic_report_info,
            'retrieve_condition_info': self.retrieve_condition_info,
            'retrieve_relevant_info_for_ICD_code': self.retrieve_relevant_info_for_ICD_code,
        }

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

    async def run(self, message: discord.Message) -> str:
        
        user_message = message.content
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        logger.info("Getting tools...")

        if self.patient_data:
            patient_context = (
                "You have access to the following patient information:\n"
                f"Name: {self.patient_data.get('name', 'Unknown')}\n"
                f"Date of Birth: {self.patient_data.get('dob', 'Unknown')}\n"
                f"Medical Record Number: {self.patient_data.get('mrn', 'Unknown')}\n"
                f"Insurance Provider: {self.patient_data.get('provider', 'Unknown')}\n"
                f"Member ID: {self.patient_data.get('memberId', 'Unknown')}\n"
                f"Group Number: {self.patient_data.get('groupNumber', 'Unknown')}\n"
                f"Effective Date: {self.patient_data.get('effectiveDate', 'Unknown')}\n\n"
            )
            
            patient_context += "Use this information to answer the user's question if relevant."
            messages.append({"role": "system", "content": patient_context})
        
        messages.append({"role": "user", "content": user_message})

        # First API call with tools
        logger.info("Making initial API call with tools...")
        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
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

            # Make final API call with all tool results
            logger.info("Making final API call with tool results...")
            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages
            )

        return response.choices[0].message.content