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
        # Return a specific error message string that can be passed to the user
        return "Error: Uploaded file not found by the parser."
    except Exception as e:
        # Return a generic error message for other openpyxl errors
        return f"Error: Could not open or process the Excel file. Details: {e}"

    sheet = workbook.active
    headers = [cell.value for cell in sheet[1]]  # Get header row

    required_header_names = ['Test Case ID', 'Description', 'Expected Outcome']
    present_headers = {header: False for header in required_header_names}

    header_to_column_index = {}

    for col_idx, header_value in enumerate(headers):
        if header_value in present_headers:
            present_headers[header_value] = True
            header_to_column_index[header_value] = col_idx + 1 # openpyxl is 1-indexed

    missing_headers = [header for header, is_present in present_headers.items() if not is_present]
    if missing_headers:
        return f"Error: Missing required columns. Ensure {', '.join(f\"'{h}'\" for h in required_header_names)} columns are present."

    parsed_test_cases = []
    for row_num in range(2, sheet.max_row + 1):  # Start from row 2 (skip header)
        test_case_id = sheet.cell(row=row_num, column=header_to_column_index['Test Case ID']).value
        description = sheet.cell(row=row_num, column=header_to_column_index['Description']).value
        expected_outcome = sheet.cell(row=row_num, column=header_to_column_index['Expected Outcome']).value

        # Basic validation: ensure Test Case ID is present
        if not test_case_id:
            # Skip rows where Test Case ID is missing (or log as appropriate)
            continue

        test_case = {
            'Test Case ID': test_case_id,
            'Description': description,
            'Expected Outcome': expected_outcome
            # 'Optional Parameters' will be handled in a future implementation.
        }
        parsed_test_cases.append(test_case)

    return parsed_test_cases

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
