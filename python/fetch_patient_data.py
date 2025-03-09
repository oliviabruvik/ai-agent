import json
import sys
import traceback
from dotenv import load_dotenv
from pathlib import Path
from python.patient_info_parser import parse_patient_data
from python.insurance_parser import parse_insurance_data
from python.epic_fhir_client import EpicFHIRClient
from python.parse_diagnostic_data import parse_diagnostic_report
from python.allergy_parser import parse_allergy_data
from python.condition_parser import parse_condition_data
import os

def log_error(message, error=None):
    error_data = {
        "error": message,
        "type": error.__class__.__name__ if error else None,
        "details": str(error) if error else None,
        "traceback": traceback.format_exc() if error else None
    }
    print(json.dumps(error_data), file=sys.stderr)

def fetch_patient_data():
    """
    Fetches patient data from the Epic FHIR API.
    Returns a dictionary with patient and insurance information.
    """
    try:
        # Load environment variables
        load_dotenv()

        # Get and validate environment variables
        EPIC_TOKEN_URL = os.getenv('EPIC_TOKEN_URL')
        CLIENT_ID = os.getenv('CLIENT_ID')
        FHIR_BASE_URL = os.getenv('FHIR_BASE_URL')

        if not all([EPIC_TOKEN_URL, CLIENT_ID, FHIR_BASE_URL]):
            missing = [var for var, val in {
                'EPIC_TOKEN_URL': EPIC_TOKEN_URL,
                'CLIENT_ID': CLIENT_ID,
                'FHIR_BASE_URL': FHIR_BASE_URL
            }.items() if not val]
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Initialize the FHIR client
        client = EpicFHIRClient(FHIR_BASE_URL, CLIENT_ID)
        
        # Fetch coverage data
        coverage_data = client.make_api_call(
            "eS72vnDj387lBv1vJqjUKhGFkkNw3RVMhZzABgnZ0kwk3",
            ["Coverage"],
            "system/Coverage.create system/Coverage.read"
        )
        
        # Fetch patient data
        patient_data = client.make_api_call(
            "eq081-VQEgP8drUUqCWzHfw3",
            ["Patient"],
            "system/Patient.create system/Patient.read"
        )

        # Fetch diagnostic data
        diagnostic_data = client.make_api_call(
            "eJK6xuoJozQ27K0SXMs-xhg3",
            ["DiagnosticReport"],
            "system/DiagnosticReport.create system/DiagnosticReport.read"
        )

        # Fetch allergy data
        allergy_data = client.make_api_call(
            "eDDkI1cAyDYgpTJheyIFMmg3",
            ["AllergyIntolerance"],
            "system/AllergyIntolerance.create system/AllergyIntolerance.read"
        )

        # Fetch condition data
        condition_data = client.make_api_call(
            "eyby2d7PoIFFgrpFtF.ntLg3",
            ["Condition"],
            "system/Condition.create system/Condition.read"
        )
        
        # Parse the patient and insurance data
        parsed_patient = {}
        parsed_insurance = {}
        
        if "Patient" in patient_data:
            parsed_patient = parse_patient_data(patient_data["Patient"])
        else:
            raise ValueError("No Patient resource found in response")
            
        if "Coverage" in coverage_data:
            parsed_insurance = parse_insurance_data(coverage_data["Coverage"])
        else:
            raise ValueError("No Coverage resource found in response")
        
        # Parse the diagnostic data
        parsed_diagnostic_data = parse_diagnostic_report(diagnostic_data)
        
        # Parse the allergy data
        parsed_allergy_data = parse_allergy_data(allergy_data)
        
        # Parse the condition data
        parsed_condition_data = parse_condition_data(condition_data)
        
        # Add the parsed data to the patient data
        patient_data['diagnostic_report'] = parsed_diagnostic_data
        patient_data['allergy'] = parsed_allergy_data
        patient_data['condition'] = parsed_condition_data
        
        # Format the data for the frontend
        formatted_data = {
            "name": parsed_patient["name"],
            "dob": parsed_patient["birth_date"],
            "mrn": parsed_patient["mrn"],
            "provider": parsed_insurance["provider"],
            "memberId": parsed_insurance["member_id"],
            "groupNumber": parsed_insurance["group_number"],
            "effectiveDate": parsed_insurance["effective_date"],
            "diagnostic_report": parsed_diagnostic_data,
            "allergies": parsed_allergy_data,
            "conditions": parsed_condition_data
        }

        return formatted_data
        
    except Exception as e:
        log_error("Failed to fetch patient data", e)
        return {"error": str(e)}

# This allows the script to be run directly
if __name__ == "__main__":
    result = fetch_patient_data()
    print(json.dumps(result)) 