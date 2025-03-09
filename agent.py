import os
from mistralai import Mistral
import discord

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = "You are a helpful assistant. You have access to patient medical information and can answer questions about it."


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        self.client = Mistral(api_key=MISTRAL_API_KEY)
        self.patient_data = None

    def set_patient_data(self, patient_data):
        self.patient_data = patient_data

    async def run(self, message: discord.Message):
        user_message = message.content
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
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
            
            # Add diagnostic report information if available
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
                
                patient_context += diagnostic_context
            
            # Add allergy information if available
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
                
                patient_context += allergy_context
            
            # Add condition information if available
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
                
                patient_context += condition_context
            
            patient_context += "Use this information to answer the user's question if relevant."
            messages.append({"role": "system", "content": patient_context})
        
        messages.append({"role": "user", "content": user_message})

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )

        return response.choices[0].message.content
