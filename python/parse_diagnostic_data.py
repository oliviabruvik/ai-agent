"""
Module for parsing FHIR DiagnosticReport resources and extracting relevant information.
"""

def parse_diagnostic_report(diagnostic_data):
    """
    Parse a FHIR DiagnosticReport resource and extract relevant information.
    
    Args:
        diagnostic_data (dict): The DiagnosticReport data returned from the API
        
    Returns:
        dict: A dictionary containing the parsed diagnostic report information
    """
    # Check if we have valid diagnostic data
    if not diagnostic_data or 'DiagnosticReport' not in diagnostic_data:
        return {
            'error': 'No diagnostic report data available'
        }
    
    report = diagnostic_data['DiagnosticReport']
    
    # Extract basic information
    parsed_data = {
        'id': report.get('id', 'Unknown'),
        'status': report.get('status', 'Unknown'),
        'issued_date': report.get('issued', 'Unknown'),
        'effective_date': report.get('effectiveDateTime', 'Unknown'),
    }
    
    # Extract the report type/name
    if 'code' in report and 'text' in report['code']:
        parsed_data['report_name'] = report['code']['text']
    elif 'code' in report and 'coding' in report['code'] and report['code']['coding']:
        coding = report['code']['coding'][0]
        parsed_data['report_name'] = coding.get('display', coding.get('code', 'Unknown Test'))
    else:
        parsed_data['report_name'] = 'Unknown Test'
    
    # Extract category information
    if 'category' in report and report['category']:
        categories = []
        for category in report['category']:
            if 'text' in category:
                categories.append(category['text'])
            elif 'coding' in category and category['coding'] and 'display' in category['coding'][0]:
                categories.append(category['coding'][0]['display'])
        parsed_data['categories'] = categories if categories else ['Unknown']
    
    # Extract patient information
    if 'subject' in report and 'display' in report['subject']:
        parsed_data['patient_name'] = report['subject']['display']
    
    # Extract provider information
    if 'performer' in report and report['performer']:
        performers = []
        for performer in report['performer']:
            if 'display' in performer:
                performers.append(performer['display'])
        parsed_data['providers'] = performers if performers else ['Unknown']
    
    # Extract result references
    if 'result' in report and report['result']:
        results = []
        for result in report['result']:
            if 'display' in result:
                results.append(result['display'])
        parsed_data['result_references'] = results if results else ['No results available']
    
    # Extract identifiers
    if 'identifier' in report and report['identifier']:
        identifiers = []
        for identifier in report['identifier']:
            if 'value' in identifier:
                id_type = 'Unknown'
                if 'type' in identifier and 'text' in identifier['type']:
                    id_type = identifier['type']['text']
                identifiers.append({
                    'type': id_type,
                    'value': identifier['value']
                })
        parsed_data['identifiers'] = identifiers if identifiers else ['No identifiers available']
    
    return parsed_data


def get_diagnostic_summary(diagnostic_data):
    """
    Create a human-readable summary of the diagnostic report.
    
    Args:
        diagnostic_data (dict): The DiagnosticReport data returned from the API
        
    Returns:
        str: A formatted string summarizing the diagnostic report
    """
    parsed_data = parse_diagnostic_report(diagnostic_data)
    
    if 'error' in parsed_data:
        return parsed_data['error']
    
    summary = [
        f"Diagnostic Report: {parsed_data.get('report_name', 'Unknown Test')}",
        f"Status: {parsed_data.get('status', 'Unknown')}",
        f"Date: {parsed_data.get('effective_date', 'Unknown')}",
        f"Issued: {parsed_data.get('issued_date', 'Unknown')}"
    ]
    
    if 'categories' in parsed_data:
        summary.append(f"Categories: {', '.join(parsed_data['categories'])}")
    
    if 'patient_name' in parsed_data:
        summary.append(f"Patient: {parsed_data['patient_name']}")
    
    if 'providers' in parsed_data:
        summary.append(f"Providers: {', '.join(parsed_data['providers'])}")
    
    if 'result_references' in parsed_data:
        summary.append("Results:")
        for result in parsed_data['result_references']:
            summary.append(f"  - {result}")
    
    return "\n".join(summary) 