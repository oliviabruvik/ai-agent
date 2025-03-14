import requests
import os
import time
import uuid
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class EpicFHIRClient:
    def __init__(self, base_url: str, client_id: str):
        self.base_url = base_url
        self.client_id = client_id
        self.token_url = os.getenv('EPIC_TOKEN_URL')
        
        # Read private key from file
        private_key_path = os.getenv('PRIVATE_KEY_PATH')
        try:
            with open(private_key_path, 'r') as f:
                self.private_key = f.read().strip()
        except Exception as e:
            raise Exception(f"Error reading private key file: {str(e)}")
    
    def _generate_jwt_assertion(self, scope: str) -> str:
        """
        Generates a JWT client assertion for Epic OAuth 2.0 token endpoint
        """
        if not self.private_key:
            raise Exception("Missing private key")
            
        now = int(time.time())
        payload = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_url,
            "exp": now + 300,  # Token expires in 5 minutes
            "iat": now,
            "jti": str(uuid.uuid4()),
            "scope": scope
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def _get_access_token(self, scope: str) -> str:
        """
        Gets an access token using JWT client assertion
        """
        assertion_jwt = self._generate_jwt_assertion(scope)
        
        data = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion_jwt,
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        
        return response.json()["access_token"]

    def make_api_call(self, patient_id: str, request_types: List[str], scope: str) -> Dict[str, Any]:
        """
        Makes multiple FHIR API calls for different resource types
        """
        patient_data = {}
        access_token = self._get_access_token(scope)
        
        for request_type in request_types:
            endpoint_url = f"{self.base_url}/{request_type}/{patient_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/fhir+json"
            }

            response = requests.get(endpoint_url, headers=headers)
            response.raise_for_status()
            patient_data[request_type] = response.json()
            
        return patient_data