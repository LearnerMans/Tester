import os
from flask import Blueprint, request, redirect, url_for, render_template, current_app, session, flash, abort
from werkzeug.utils import secure_filename
from ..test_case_management.excel_parser import parse_excel_data
from .. import db # Import db instance from app package
from ..models.test_case import TestCase # Import TestCase model
# AIConnector is already imported and ai_connector instance is created
from ..conversation_ai_integration.ai_connector import AIConnector

web_interface_blueprint = Blueprint('web_interface', __name__, template_folder='../../templates')

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# No longer using global loaded_test_cases list

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@web_interface_blueprint.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return redirect(url_for('web_interface.show_test_cases', error="No file part"))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('web_interface.show_test_cases', error="No selected file"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = current_app.config['UPLOAD_FOLDER']
        # The directory should be created by create_app, but a check doesn't hurt
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)

        try:
            file.save(file_path)
        except Exception as e:
             return redirect(url_for('web_interface.show_test_cases', error=f"Error saving file: {str(e)}"))

        parsed_result = parse_excel_data(file_path)

        if isinstance(parsed_result, str) and parsed_result.startswith("Error:"):
            return redirect(url_for('web_interface.show_test_cases', error=parsed_result))
        elif isinstance(parsed_result, list):
            try:
                # Clear existing test cases from the table before adding new ones
                # This is a simple approach. For more complex scenarios, consider
                # updating existing records or providing user choice.
                db.session.query(TestCase).delete()

                for tc_data in parsed_result:
                    # Ensure all required fields are present in tc_data
                    if not all(k in tc_data for k in ['Test Case ID', 'Description', 'Expected Outcome']):
                        # Log this or handle as a partial success/failure
                        current_app.logger.warning(f"Skipping incomplete test case data: {tc_data}")
                        continue

                    new_test_case = TestCase(
                        id=str(tc_data['Test Case ID']), # Ensure ID is string
                        description=tc_data['Description'],
                        expected_outcome=tc_data['Expected Outcome'],
                        category=tc_data.get('Category'), # Use .get() for optional fields
                        priority=tc_data.get('Priority'),
                        tags=tc_data.get('Tags', []) # Default to empty list if 'Tags' key is missing
                    )
                    db.session.add(new_test_case)

                db.session.commit()
                return redirect(url_for('web_interface.show_test_cases', success="File uploaded and test cases saved to database."))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error: {str(e)}")
                return redirect(url_for('web_interface.show_test_cases', error=f"Database error: {str(e)}"))
        else:
            return redirect(url_for('web_interface.show_test_cases', error="An unexpected error occurred during parsing"))

    else:
        return redirect(url_for('web_interface.show_test_cases', error="Invalid file type. Please upload .xlsx or .xls files."))

@web_interface_blueprint.route('/show_test_cases', methods=['GET'])
def show_test_cases():
    error_message = request.args.get('error')
    success_message = request.args.get('success')

    # Get filter parameters from request arguments
    filter_test_case_id = request.args.get('filter_test_case_id', '').strip()
    filter_description_keyword = request.args.get('filter_description_keyword', '').strip()
    filter_category = request.args.get('filter_category', '').strip()
    filter_priority = request.args.get('filter_priority', '').strip()

    try:
        query = TestCase.query

        if filter_test_case_id:
            query = query.filter(TestCase.id.ilike(f"%{filter_test_case_id}%"))

        if filter_description_keyword:
            query = query.filter(TestCase.description.ilike(f"%{filter_description_keyword}%"))

        if filter_category:
            query = query.filter(TestCase.category.ilike(f"%{filter_category}%"))

        if filter_priority:
            query = query.filter(TestCase.priority.ilike(f"%{filter_priority}%"))

        all_test_cases_db = query.order_by(TestCase.id).all()

        test_cases_for_template = [tc.to_dict() for tc in all_test_cases_db]

    except Exception as e:
        current_app.logger.error(f"Error fetching or filtering test cases from DB: {str(e)}")
        error_message = f"Error processing test cases: {str(e)}"
        test_cases_for_template = []

    return render_template('show_test_cases.html',
                           test_cases=test_cases_for_template,
                           error=error_message,
                           success=success_message,
                           filter_test_case_id=filter_test_case_id,
                           filter_description_keyword=filter_description_keyword,
                           filter_category=filter_category,
                           filter_priority=filter_priority)

@web_interface_blueprint.route('/', methods=['GET'])
def index():
    # Redirect to show_test_cases, which is the main page for test case management
    return redirect(url_for('web_interface.show_test_cases'))

# Instantiate connector globally or within app context if it needs app config
# For now, a simple global instance is fine as it's stateless until methods are called.
ai_connector = AIConnector()

@web_interface_blueprint.route('/configure_ai', methods=['GET', 'POST'])
def configure_ai():
    if request.method == 'POST':
        api_endpoint = request.form.get('api_endpoint', '').strip()
        # Important: For API keys, always retrieve them fresh from the form on POST.
        # Do not rely on a previously loaded key from config if the user intends to update it.
        api_key = request.form.get('api_key', '').strip()

        # Validate the input from the form
        is_valid_input = ai_connector.check_connection(api_endpoint, api_key)

        if is_valid_input:
            # If input is valid, attempt to save it
            save_success = ai_connector.save_config(api_endpoint, api_key)
            if save_success:
                flash("Configuration saved successfully.", "success")
                # Optionally, store a general success status in session if needed for other parts of app
                session['ai_config_status'] = "Configuration saved."
            else:
                flash("Error saving configuration to file.", "error")
                session['ai_config_status'] = "Error saving configuration."
        else:
            # Input itself was invalid (e.g., missing endpoint or key)
            flash("Validation failed. API Endpoint and API Key are required.", "error")
            session['ai_config_status'] = "Validation failed. Missing credentials."

        return redirect(url_for('web_interface.configure_ai'))

    # GET request
    # Load current config to display in the form
    config = ai_connector.load_config()
    current_endpoint = config.get('api_endpoint', '')
    # For security, we don't pass the actual API key to the template for display in a password field.
    # We can indicate if a key is already stored.
    api_key_is_present = True if config.get('api_key') else False

    # Get status from session (e.g., result of last POST)
    # This can be augmented or replaced by more specific feedback if needed.
    current_status_from_session = session.pop('ai_config_status', None) # Pop to show only once per action

    return render_template('configure_ai.html',
                           current_endpoint=current_endpoint,
                           api_key_is_present=api_key_is_present,
                           current_status=current_status_from_session # Display flashed/session status
                           )

@web_interface_blueprint.route('/run_test/<string:test_case_id>', methods=['GET'])
def run_test(test_case_id):
    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        current_app.logger.error(f"Test case with ID {test_case_id} not found.")
        abort(404) # Not Found

    # AIConnector instance 'ai_connector' is already available globally in this file
    response_from_ai = ai_connector.start_conversation(test_case.description)

    if response_from_ai and response_from_ai.get('status') == 'success':
        # Basic console logging for the initial successful interaction
        log_message = (
            f"\n--- Test Run Log ---\n"
            f"Test Case ID: {test_case.id}\n"
            f"User's Initial Message: {test_case.description}\n"
            f"AI's Response: {response_from_ai.get('message_from_ai')}\n"
            f"Conversation ID: {response_from_ai.get('conversation_id')}\n"
            f"API Endpoint Used: {response_from_ai.get('api_endpoint_used')}\n"
            f"Raw Response (first 100 chars for brevity): {response_from_ai.get('raw_response', '')[:100]}...\n"
            f"--- End Log ---\n"
        )
        # Using current_app.logger.info if available and configured, otherwise print.
        # For this environment, let's assume current_app.logger is available.
        # If not, print() would be the fallback.
        try:
            current_app.logger.info(log_message)
        except RuntimeError: # If outside of application context or logger not set up
            print(log_message)

    return render_template('run_test_result.html',
                           test_case=test_case.to_dict(), # Pass as dict for consistency
                           response=response_from_ai)
