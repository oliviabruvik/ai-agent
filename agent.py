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
                "Use this information to answer the user's question if relevant."
            )
            messages.append({"role": "system", "content": patient_context})
        
        messages.append({"role": "user", "content": user_message})

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )

        return response.choices[0].message.content
