"""
Module for parsing FHIR Condition resources and extracting relevant information.
"""

def parse_condition_data(condition_data):
    """
    Parse a FHIR Condition resource and extract relevant information.
    
    Args:
        condition_data (dict): The Condition data returned from the API
        
    Returns:
        dict: A dictionary containing the parsed condition information
    """
    # Check if we have valid condition data
    if not condition_data or 'Condition' not in condition_data:
        return {
            'error': 'No condition data available'
        }
    
    condition = condition_data['Condition']
    
    # Extract basic information
    parsed_data = {
        'id': condition.get('id', 'Unknown'),
        'onset_date': condition.get('onsetDateTime', 'Unknown'),
        'recorded_date': condition.get('recordedDate', 'Unknown'),
    }
    
    # Extract clinical status
    if 'clinicalStatus' in condition and 'text' in condition['clinicalStatus']:
        parsed_data['clinical_status'] = condition['clinicalStatus']['text']
    elif 'clinicalStatus' in condition and 'coding' in condition['clinicalStatus'] and condition['clinicalStatus']['coding']:
        parsed_data['clinical_status'] = condition['clinicalStatus']['coding'][0].get('display', 'Unknown')
    else:
        parsed_data['clinical_status'] = 'Unknown'
    
    # Extract verification status
    if 'verificationStatus' in condition and 'text' in condition['verificationStatus']:
        parsed_data['verification_status'] = condition['verificationStatus']['text']
    elif 'verificationStatus' in condition and 'coding' in condition['verificationStatus'] and condition['verificationStatus']['coding']:
        parsed_data['verification_status'] = condition['verificationStatus']['coding'][0].get('display', 'Unknown')
    else:
        parsed_data['verification_status'] = 'Unknown'
    
    # Extract category
    if 'category' in condition and condition['category']:
        categories = []
        for category in condition['category']:
            if 'text' in category:
                categories.append(category['text'])
            elif 'coding' in category and category['coding'] and 'display' in category['coding'][0]:
                categories.append(category['coding'][0]['display'])
        parsed_data['categories'] = categories if categories else ['Unknown']
    
    # Extract condition code/name
    if 'code' in condition and 'text' in condition['code']:
        parsed_data['condition_name'] = condition['code']['text']
    elif 'code' in condition and 'coding' in condition['code'] and condition['code']['coding']:
        parsed_data['condition_name'] = condition['code']['coding'][0].get('display', 'Unknown Condition')
    else:
        parsed_data['condition_name'] = 'Unknown Condition'
    
    # Extract patient information
    if 'subject' in condition and 'display' in condition['subject']:
        parsed_data['patient_name'] = condition['subject']['display']
    
    # Extract notes
    if 'note' in condition and condition['note']:
        notes = []
        for note in condition['note']:
            if 'text' in note:
                notes.append(note['text'])
        parsed_data['notes'] = notes if notes else ['No notes available']
    
    return parsed_data


def get_condition_summary(condition_data):
    """
    Create a human-readable summary of the condition information.
    
    Args:
        condition_data (dict): The Condition data returned from the API
        
    Returns:
        str: A formatted string summarizing the condition information
    """
    parsed_data = parse_condition_data(condition_data)
    
    if 'error' in parsed_data:
        return parsed_data['error']
    
    summary = [
        f"Condition: {parsed_data.get('condition_name', 'Unknown Condition')}",
        f"Status: {parsed_data.get('clinical_status', 'Unknown')} ({parsed_data.get('verification_status', 'Unknown')})",
        f"Onset Date: {parsed_data.get('onset_date', 'Unknown')}",
        f"Recorded Date: {parsed_data.get('recorded_date', 'Unknown')}"
    ]
    
    if 'categories' in parsed_data:
        summary.append(f"Categories: {', '.join(parsed_data['categories'])}")
    
    if 'notes' in parsed_data:
        summary.append("Clinical Notes:")
        for note in parsed_data['notes']:
            summary.append(f"  {note}")
    
    return "\n".join(summary) 