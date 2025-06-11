import openpyxl

def parse_excel_data(file_path):
    """
    Parses an Excel file to extract test case data.

    Args:
        file_path (str): The path to the Excel file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a test case.
              Returns an empty list if the required columns are not found or
              if the file cannot be opened.
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
    except FileNotFoundError:
        return {"status": "error", "message": "Error: Uploaded file not found by the parser."}
    except Exception as e:
        return {"status": "error", "message": f"Error: Could not open or process the Excel file. Details: {e}"}

    sheet = workbook.active
    raw_headers = [cell.value for cell in sheet[1]] # Get header row

    # Normalize headers to lower case for case-insensitive matching
    headers = [str(h).lower() if h is not None else "" for h in raw_headers]

    # Define expected headers (core and optional)
    # Using lowercase for matching against normalized headers
    core_expected_headers = {
        'test case id': 'Test Case ID', # value is the key we'll use in the output dict
        'description': 'Description',
        'expected outcome': 'Expected Outcome'
    }
    optional_expected_headers = {
        'category': 'Category',
        'priority': 'Priority',
        'tags': 'Tags'
    }

    header_to_column_index = {}
    # Map core headers
    for h_lower, h_actual_key in core_expected_headers.items():
        try:
            header_to_column_index[h_actual_key] = headers.index(h_lower) + 1 # openpyxl is 1-indexed
        except ValueError:
            # A core header is missing
            missing_core_headers_display = [core_expected_headers[lh] for lh in core_expected_headers if lh not in headers]
            missing_headers_str = ', '.join([f"'{h}'" for h in missing_core_headers_display])
            return {"status": "error", "message": f"Error: Missing required columns. Ensure {missing_headers_str} columns are present."}

    # Map optional headers
    for h_lower, h_actual_key in optional_expected_headers.items():
        try:
            header_to_column_index[h_actual_key] = headers.index(h_lower) + 1 # openpyxl is 1-indexed
        except ValueError:
            # Optional header is not present, that's fine. We won't add it to header_to_column_index.
            pass

    parsed_test_cases = []
    for row_num in range(2, sheet.max_row + 1):  # Start from row 2 (skip header)
        test_case_data = {}

        # Extract core fields
        test_case_id = sheet.cell(row=row_num, column=header_to_column_index['Test Case ID']).value
        # Basic validation: ensure Test Case ID is present
        if not test_case_id:
            continue # Skip rows where Test Case ID is missing

        test_case_data['Test Case ID'] = test_case_id
        test_case_data['Description'] = sheet.cell(row=row_num, column=header_to_column_index['Description']).value
        test_case_data['Expected Outcome'] = sheet.cell(row=row_num, column=header_to_column_index['Expected Outcome']).value

        # Extract optional fields if their columns were found
        if 'Category' in header_to_column_index:
            test_case_data['Category'] = sheet.cell(row=row_num, column=header_to_column_index['Category']).value
        else:
            test_case_data['Category'] = None

        if 'Priority' in header_to_column_index:
            test_case_data['Priority'] = sheet.cell(row=row_num, column=header_to_column_index['Priority']).value
        else:
            test_case_data['Priority'] = None

        if 'Tags' in header_to_column_index:
            tags_value = sheet.cell(row=row_num, column=header_to_column_index['Tags']).value
            if isinstance(tags_value, str):
                test_case_data['Tags'] = [tag.strip() for tag in tags_value.split(',') if tag.strip()]
            elif tags_value is None: # Cell is empty
                 test_case_data['Tags'] = []
            else: # E.g. if it's a number or other type, convert to string then process, or handle as error/default
                test_case_data['Tags'] = [str(tags_value).strip()] if str(tags_value).strip() else []
        else:
            test_case_data['Tags'] = [] # Default to empty list if 'Tags' column is missing

        parsed_test_cases.append(test_case_data)

    # If everything is successful, wrap the result in a dictionary
    return {"status": "success", "data": parsed_test_cases}

if __name__ == '__main__':
    # This is a placeholder for creating a dummy Excel file for testing.
    # In a real scenario, you would have an actual Excel file.
    # For now, we'll just print a message.
    print("Excel parser module. To test, create a dummy Excel file with columns 'Test Case ID', 'Description', 'Expected Outcome' and call parse_excel_data(your_file.xlsx)")
    # Example of how to create a dummy file (requires openpyxl to be installed)
    # from openpyxl import Workbook
    # dummy_file_path = 'dummy_test_cases.xlsx'
    # wb = Workbook()
    # ws = wb.active
    # ws.title = "TestCases"
    # ws.append(['Test Case ID', 'Description', 'Expected Outcome', 'Optional Parameters'])
    # ws.append(['TC001', 'Verify login functionality', 'User should be logged in successfully', '{"username": "testuser", "password": "password123"}'])
    # ws.append(['TC002', 'Check dashboard loading', 'Dashboard should load within 5 seconds', None])
    # ws.append([None, 'This row should be skipped', 'N/A', None]) # Test skipping row with no ID
    # ws.append(['TC003', 'Verify logout', 'User should be logged out', ''])
    # wb.save(dummy_file_path)
    # print(f"Created dummy file: {dummy_file_path}")
    # parsed_data = parse_excel_data(dummy_file_path)
    # if parsed_data:
    #     print("\nParsed Test Cases:")
    #     for tc in parsed_data:
    #         print(tc)
    # else:
    #     print("\nNo data parsed or an error occurred.")
