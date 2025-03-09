"""
Module for parsing FHIR AllergyIntolerance resources and extracting relevant information.
"""

def parse_allergy_data(allergy_data):
    """
    Parse a FHIR AllergyIntolerance resource and extract relevant information.
    
    Args:
        allergy_data (dict): The AllergyIntolerance data returned from the API
        
    Returns:
        dict: A dictionary containing the parsed allergy information
    """
    # Check if we have valid allergy data
    if not allergy_data or 'AllergyIntolerance' not in allergy_data:
        return {
            'error': 'No allergy intolerance data available'
        }
    
    allergy = allergy_data['AllergyIntolerance']
    
    # Extract basic information
    parsed_data = {
        'id': allergy.get('id', 'Unknown'),
        'onset_date': allergy.get('onsetDateTime', 'Unknown'),
        'recorded_date': allergy.get('recordedDate', 'Unknown'),
    }
    
    # Extract clinical status
    if 'clinicalStatus' in allergy and 'text' in allergy['clinicalStatus']:
        parsed_data['clinical_status'] = allergy['clinicalStatus']['text']
    elif 'clinicalStatus' in allergy and 'coding' in allergy['clinicalStatus'] and allergy['clinicalStatus']['coding']:
        parsed_data['clinical_status'] = allergy['clinicalStatus']['coding'][0].get('display', 'Unknown')
    else:
        parsed_data['clinical_status'] = 'Unknown'
    
    # Extract verification status
    if 'verificationStatus' in allergy and 'text' in allergy['verificationStatus']:
        parsed_data['verification_status'] = allergy['verificationStatus']['text']
    elif 'verificationStatus' in allergy and 'coding' in allergy['verificationStatus'] and allergy['verificationStatus']['coding']:
        parsed_data['verification_status'] = allergy['verificationStatus']['coding'][0].get('display', 'Unknown')
    else:
        parsed_data['verification_status'] = 'Unknown'
    
    # Extract category
    if 'category' in allergy and allergy['category']:
        parsed_data['category'] = allergy['category']
    
    # Extract allergy code/name
    if 'code' in allergy and 'text' in allergy['code']:
        parsed_data['allergy_name'] = allergy['code']['text']
    elif 'code' in allergy and 'coding' in allergy['code'] and allergy['code']['coding']:
        parsed_data['allergy_name'] = allergy['code']['coding'][0].get('display', 'Unknown Allergy')
    else:
        parsed_data['allergy_name'] = 'Unknown Allergy'
    
    # Extract patient information
    if 'patient' in allergy and 'display' in allergy['patient']:
        parsed_data['patient_name'] = allergy['patient']['display']
    
    # Extract reaction information
    if 'reaction' in allergy and allergy['reaction']:
        reactions = []
        for reaction in allergy['reaction']:
            reaction_info = {}
            
            # Get description
            if 'description' in reaction:
                reaction_info['description'] = reaction['description']
            
            # Get manifestations
            if 'manifestation' in reaction:
                manifestations = []
                for manifestation in reaction['manifestation']:
                    if 'text' in manifestation:
                        manifestations.append(manifestation['text'])
                    elif 'coding' in manifestation and manifestation['coding'] and 'code' in manifestation['coding'][0]:
                        manifestations.append(manifestation['coding'][0]['code'])
                
                if manifestations:
                    reaction_info['manifestations'] = manifestations
            
            if reaction_info:
                reactions.append(reaction_info)
        
        if reactions:
            parsed_data['reactions'] = reactions
    
    return parsed_data


def get_allergy_summary(allergy_data):
    """
    Create a human-readable summary of the allergy information.
    
    Args:
        allergy_data (dict): The AllergyIntolerance data returned from the API
        
    Returns:
        str: A formatted string summarizing the allergy information
    """
    parsed_data = parse_allergy_data(allergy_data)
    
    if 'error' in parsed_data:
        return parsed_data['error']
    
    summary = [
        f"Allergy: {parsed_data.get('allergy_name', 'Unknown Allergy')}",
        f"Status: {parsed_data.get('clinical_status', 'Unknown')} ({parsed_data.get('verification_status', 'Unknown')})",
        f"Onset Date: {parsed_data.get('onset_date', 'Unknown')}",
        f"Recorded Date: {parsed_data.get('recorded_date', 'Unknown')}"
    ]
    
    if 'category' in parsed_data:
        summary.append(f"Category: {', '.join(parsed_data['category'])}")
    
    if 'reactions' in parsed_data:
        summary.append("Reactions:")
        for reaction in parsed_data['reactions']:
            if 'description' in reaction:
                summary.append(f"  - {reaction['description']}")
            if 'manifestations' in reaction:
                summary.append(f"    Manifestations: {', '.join(reaction['manifestations'])}")
    
    return "\n".join(summary) 