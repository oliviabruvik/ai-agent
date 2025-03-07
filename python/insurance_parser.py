from typing import Dict, Any, Optional, List

def extract_member_id(coverage_data: Dict[str, Any]) -> str:
    """
    Extracts the member ID from FHIR Coverage resource.
    Prioritizes subscriber ID, then falls back to member number from identifiers.
    """
    try:
        # First try to get subscriberId
        if subscriber_id := coverage_data.get('subscriberId'):
            return subscriber_id
            
        # Fall back to member number in identifiers
        identifiers = coverage_data.get('identifier', [])
        for identifier in identifiers:
            if identifier.get('type', {}).get('coding', [{}])[0].get('code') == 'MB':
                if rendered_value := identifier.get('_value', {}).get('extension', [{}])[0].get('valueString'):
                    return rendered_value
                
        return ""
    except Exception as e:
        raise ValueError(f"Error extracting member ID: {str(e)}")

def extract_group_number(coverage_data: Dict[str, Any]) -> str:
    """
    Extracts the group number from FHIR Coverage resource.
    Looks in the class array for type 'group'.
    """
    try:
        classes = coverage_data.get('class', [])
        for class_info in classes:
            type_coding = class_info.get('type', {}).get('coding', [{}])[0]
            if type_coding.get('code') == 'group':
                return class_info.get('value', '')
        return ""
    except Exception as e:
        raise ValueError(f"Error extracting group number: {str(e)}")

def extract_insurance_provider(coverage_data: Dict[str, Any]) -> str:
    """
    Extracts the insurance provider name from FHIR Coverage resource.
    Gets the display name from the first payor.
    """
    try:
        payors = coverage_data.get('payor', [])
        if payors and (display := payors[0].get('display')):
            return display
        return ""
    except Exception as e:
        raise ValueError(f"Error extracting insurance provider: {str(e)}")

def extract_effective_date(coverage_data: Dict[str, Any]) -> str:
    """
    Extracts the effective date from FHIR Coverage resource.
    Gets the start date from the period.
    """
    try:
        if period := coverage_data.get('period', {}):
            return period.get('start', '')
        return ""
    except Exception as e:
        raise ValueError(f"Error extracting effective date: {str(e)}")

def parse_insurance_data(coverage_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Parses a FHIR Coverage resource and returns relevant insurance information.
    """
    try:
        if coverage_json.get('resourceType') != 'Coverage':
            raise ValueError("Invalid FHIR resource type. Expected 'Coverage'")
        
        return {
            'provider': extract_insurance_provider(coverage_json),
            'member_id': extract_member_id(coverage_json),
            'group_number': extract_group_number(coverage_json),
            'effective_date': extract_effective_date(coverage_json)
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing insurance data: {str(e)}")