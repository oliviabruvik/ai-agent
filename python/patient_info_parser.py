from typing import Dict, Any, Optional, List, Tuple

def extract_mrn(patient_data: Dict[str, Any]) -> str:
    """
    Extracts the MRN (Medical Record Number) from FHIR Patient resource.
    Looks for identifier with type 'MR' or containing 'MRN' in the text.
    """
    try:
        identifiers = patient_data.get('identifier', [])
        for identifier in identifiers:
            # Check for explicit MR type coding
            type_coding = identifier.get('type', {}).get('coding', [{}])[0]
            if type_coding.get('code') == 'MR':
                return identifier.get('value', '')
            
            # Check for MRN in type text
            type_text = identifier.get('type', {}).get('text', '').upper()
            if 'MRN' in type_text or 'MEDICAL RECORD' in type_text:
                return identifier.get('value', '')
            
            # For EPIC, often INTERNAL or EPI types are used for MRN
            if identifier.get('type', {}).get('text') in ['INTERNAL', 'EPI']:
                return identifier.get('value', '').strip()
                
        return ""
    except Exception as e:
        raise ValueError(f"Error extracting MRN: {str(e)}")

def extract_patient_name(patient_data: Dict[str, Any]) -> str:
    """
    Extracts the patient's full name from FHIR Patient resource.
    Prioritizes 'official' name, falls back to 'usual' or first available name.
    """
    try:
        names = patient_data.get('name', [])
        if not names:
            raise ValueError("No name found in patient data")
        
        # First try to find the official name
        official_name = next((name for name in names if name.get('use') == 'official'), None)
        if official_name and official_name.get('text'):
            return official_name['text']
        
        # Then try usual name
        usual_name = next((name for name in names if name.get('use') == 'usual'), None)
        if usual_name and usual_name.get('text'):
            return usual_name['text']
        
        # Fall back to first available name
        if names[0].get('text'):
            return names[0]['text']
        
        # If no text field, try to construct from parts
        first_name = names[0].get('given', [''])[0]
        family_name = names[0].get('family', '')
        suffix = names[0].get('suffix', [''])[0] if names[0].get('suffix') else ''
        
        full_name = f"{first_name} {family_name}"
        if suffix:
            full_name = f"{full_name} {suffix}"
            
        return full_name.strip()
        
    except Exception as e:
        raise ValueError(f"Error extracting patient name: {str(e)}")

def extract_birth_date(patient_data: Dict[str, Any]) -> str:
    """
    Extracts the patient's birth date from FHIR Patient resource.
    """
    try:
        birth_date = patient_data.get('birthDate')
        if not birth_date:
            raise ValueError("No birth date found in patient data")
        return birth_date
    except Exception as e:
        raise ValueError(f"Error extracting birth date: {str(e)}")

def parse_patient_data(fhir_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Parses a FHIR Patient resource and returns relevant patient information.
    """
    try:
        if fhir_json.get('resourceType') != 'Patient':
            raise ValueError("Invalid FHIR resource type. Expected 'Patient'")
        
        return {
            'name': extract_patient_name(fhir_json),
            'birth_date': extract_birth_date(fhir_json),
            'mrn': extract_mrn(fhir_json)
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing patient data: {str(e)}")