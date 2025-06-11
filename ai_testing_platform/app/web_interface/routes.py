import os
from flask import Blueprint, request, redirect, url_for, render_template, current_app, session, flash, abort, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from ..test_case_management.excel_parser import parse_excel_data
from .. import db
from ..models.test_case import TestCase
from ..conversation_ai_integration.ai_connector import AIConnector
import openpyxl # Added
from io import BytesIO # Added

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

        parsed_response = parse_excel_data(file_path) # Renamed variable

        if parsed_response.get("status") == "success":
            parsed_data_list = parsed_response.get("data", [])
            if not parsed_data_list: # Handle case where parsing is "success" but data is empty
                 return redirect(url_for('web_interface.show_test_cases', warning="File parsed successfully, but no test cases found."))
            try:
                db.session.query(TestCase).delete() # Clear existing test cases

                for tc_data in parsed_data_list:
                    # Basic validation, parser should ensure these keys exist for success items
                    if not all(k in tc_data for k in ['Test Case ID', 'Description', 'Expected Outcome']):
                        current_app.logger.warning(f"Skipping incomplete test case data from parser: {tc_data}")
                        continue

                    new_test_case = TestCase(
                        id=str(tc_data['Test Case ID']),
                        description=tc_data['Description'],
                        expected_outcome=tc_data['Expected Outcome'],
                        category=tc_data.get('Category'),
                        priority=tc_data.get('Priority'),
                        tags=tc_data.get('Tags', [])
                    )
                    db.session.add(new_test_case)

                db.session.commit()
                return redirect(url_for('web_interface.show_test_cases', success="File uploaded and test cases saved to database."))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error after parsing: {str(e)}")
                return redirect(url_for('web_interface.show_test_cases', error=f"Database error: {str(e)}"))
        elif parsed_response.get("status") == "error":
            error_message = parsed_response.get("message", "An unspecified error occurred during Excel parsing.")
            return redirect(url_for('web_interface.show_test_cases', error=error_message))
        else:
            # This case should ideally not be reached if parse_excel_data is consistent
            return redirect(url_for('web_interface.show_test_cases', error="An unexpected return format from the Excel parser."))

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


    evaluations_summary = session.get('all_test_evaluations', {})

    return render_template('show_test_cases.html',
                           test_cases=test_cases_for_template,
                           error=error_message,
                           success=success_message,
                           filter_test_case_id=filter_test_case_id,
                           filter_description_keyword=filter_description_keyword,
                           filter_category=filter_category,
                           filter_priority=filter_priority,
                           all_test_evaluations=evaluations_summary)

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
    session.clear() # Clear any previous conversation data
    session['conversation_history'] = []
    session['current_test_case_id'] = test_case_id # Store current test case ID

    initial_messages = [{"role": "user", "content": test_case.description}]
    response_from_ai = ai_connector.send_messages_to_llm(initial_messages)

    if response_from_ai and response_from_ai.get('status') == 'success':
        session['conversation_history'].append(initial_messages[0])
        session['conversation_history'].append({"role": "assistant", "content": response_from_ai.get('message_from_ai')})
        # Using interaction_id from the response as the conversation_id for this session
        session['current_conversation_id'] = response_from_ai.get('interaction_id')
        session.modified = True

        # Basic console logging for the initial successful interaction
        log_message = (
            f"--- Test Run Log (Initial Turn) ---\n"
            f"Test Case ID: {test_case.id}\n"
            f"Conversation ID: {session.get('current_conversation_id')}\n" # Use .get() for safety
            f"Interaction ID: {response_from_ai.get('interaction_id')}\n"
            f"User Message: {test_case.description}\n"
            f"AI Response: {response_from_ai.get('message_from_ai')}\n"
            f"API Endpoint Used: {response_from_ai.get('api_endpoint_used')}\n"
            f"Raw Response (first 100 chars): {response_from_ai.get('raw_response', '')[:100]}...\n"
            f"--- End Log ---"
        )
        try:
            current_app.logger.info(log_message)
        except RuntimeError: # Fallback if logger isn't available (e.g. context issues)
            print(log_message)

    # Instead of rendering run_test_result.html directly, redirect to show_conversation
    # This makes show_conversation the single point of display for conversations.
    # We can flash the initial response to be shown on the conversation page.
    if response_from_ai.get('status') == 'success':
        flash(f"Initial response: {response_from_ai.get('message_from_ai')}", "info") # Flash the first AI message
    elif response_from_ai.get('status') == 'error':
        flash(f"Error starting conversation: {response_from_ai.get('message')}", "error")

    # Redirect to show_conversation, which will display history from session
    # The conversation_id in the URL here is the one generated by the first interaction.
    if session.get('current_conversation_id'):
        return redirect(url_for('web_interface.show_conversation',
                                test_case_id=test_case_id,
                                conversation_id=session.get('current_conversation_id')))
    else:
        # If no conversation_id was set (e.g. initial AI call failed badly)
        # redirect back to test cases or an error page. For now, test cases.
        flash("Failed to initiate conversation with AI.", "error")
        return redirect(url_for('web_interface.show_test_cases'))


@web_interface_blueprint.route('/continue_test/<string:test_case_id>/<string:conversation_id>', methods=['POST'])
def continue_test(test_case_id, conversation_id):
    # Validate session and conversation ID
    if not session.get('conversation_history') or conversation_id != session.get('current_conversation_id') or test_case_id != session.get('current_test_case_id'):
        flash("Invalid session or conversation ID. Please start a new test.", "error")
        return redirect(url_for('web_interface.show_test_cases'))

    user_follow_up_message = request.form.get('follow_up_message', '').strip()
    if not user_follow_up_message:
        flash("Follow-up message cannot be empty.", "warning")
        return redirect(url_for('web_interface.show_conversation',
                                test_case_id=test_case_id,
                                conversation_id=conversation_id))

@web_interface_blueprint.route('/download_excel_template')
def download_excel_template():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "TestCases"

    headers = ['Test Case ID', 'Description', 'Expected Outcome', 'Category', 'Priority', 'Tags']
    sheet.append(headers)

    sample_data = [
        ('TC_001', 'Verify user login with valid credentials.', 'User should be successfully logged in and redirected to the dashboard.', 'Authentication', 'High', 'smoke, login'),
        ('TC_002', 'Check system response to invalid login attempt.', 'An appropriate error message "Invalid username or password" should be displayed. User should not be logged in.', 'Authentication', 'Medium', 'negative, login, security'),
        ('TC_003', 'Submit a support ticket.', 'Support ticket should be successfully submitted and a confirmation ID received.', 'Support', 'High', 'core, ticketing'),
        ('TC_004', 'Verify search functionality with a known keyword.', 'Relevant results matching the keyword should be displayed.', 'Search', 'Medium', ''),
        ('TC_005', 'Attempt to access a restricted page without authentication.', 'User should be redirected to the login page or shown an access denied message.', 'Security', 'High', 'auth, permissions')
    ]

    for row_data in sample_data:
        sheet.append(row_data)

    # Adjust column widths for better readability (optional)
    for col_idx, header in enumerate(headers, 1):
        column_letter = openpyxl.utils.get_column_letter(col_idx)
        if header == 'Description' or header == 'Expected Outcome':
            sheet.column_dimensions[column_letter].width = 50
        elif header == 'Test Case ID':
            sheet.column_dimensions[column_letter].width = 15
        else:
            sheet.column_dimensions[column_letter].width = 20


    excel_stream = BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)

    return send_file(
        excel_stream,
        as_attachment=True,
        download_name='test_case_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@web_interface_blueprint.route('/show_evaluation_result/<string:test_case_id>/<string:conversation_id>', methods=['GET'])
def show_evaluation_result(test_case_id, conversation_id):
    # Validate session and conversation ID
    if test_case_id != session.get('current_test_case_id') or \
       conversation_id != session.get('current_conversation_id'):
        flash("Invalid or expired session for viewing evaluation results. Please start a new test.", "error")
        return redirect(url_for('web_interface.show_test_cases'))

    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        current_app.logger.error(f"Test case {test_case_id} not found when showing evaluation result.")
        abort(404)

    conversation_history = session.get('conversation_history', [])
    evaluation_result = session.get('last_evaluation_result', {})

    if not evaluation_result:
        flash("Evaluation result not found. Please run the evaluation first.", "warning")
        return redirect(url_for('web_interface.evaluate_test_interaction',
                                test_case_id=test_case_id,
                                conversation_id=conversation_id))

    # Clear the last_evaluation_result from session after displaying it once?
    # Or keep it until a new evaluation for this conversation_id is run?
    # For now, let's keep it, so refresh works. A "Run New Evaluation" button might clear it.
    # session.pop('last_evaluation_result', None) # Example if we want to clear after one view

    return render_template('show_evaluation_result.html',
                           test_case=test_case.to_dict(),
                           conversation_history=conversation_history,
                           conversation_id=conversation_id,
                           evaluation_result=evaluation_result)

    conversation_history = session['conversation_history']
    new_user_message = {"role": "user", "content": user_follow_up_message}
    conversation_history.append(new_user_message)

    response_from_ai = ai_connector.send_messages_to_llm(conversation_history)

    if response_from_ai and response_from_ai.get('status') == 'success':
        conversation_history.append({"role": "assistant", "content": response_from_ai.get('message_from_ai')})
        flash(f"AI's response: {response_from_ai.get('message_from_ai')}", "info")
         # Log this turn
        log_message = (
            f"--- Test Run Log (Follow-up Turn) ---\n"
            f"Test Case ID: {test_case_id}\n"
            f"Conversation ID: {conversation_id}\n"
            f"Interaction ID: {response_from_ai.get('interaction_id')}\n"
            f"User Message: {user_follow_up_message}\n" # This is from request.form earlier in the route
            f"AI Response: {response_from_ai.get('message_from_ai')}\n"
            f"API Endpoint Used: {response_from_ai.get('api_endpoint_used')}\n"
            f"Raw Response (first 100 chars): {response_from_ai.get('raw_response', '')[:100]}...\n"
            f"--- End Log ---"
        )
        try:
            current_app.logger.info(log_message)
        except RuntimeError: # Fallback
            print(log_message)
    else:
        # AI call failed, remove the user's last message to keep history clean for retry if desired
        # This was already here and is good practice.
        conversation_history.pop()
        error_msg = response_from_ai.get('message', 'An unknown error occurred with the AI.')
        flash(f"Error in AI response: {error_msg}", "error")

    session['conversation_history'] = conversation_history
    session.modified = True

    return redirect(url_for('web_interface.show_conversation',
                            test_case_id=test_case_id,
                            conversation_id=conversation_id))

@web_interface_blueprint.route('/show_conversation/<string:test_case_id>/<string:interaction_id>', methods=['GET'])
def show_conversation(test_case_id, interaction_id):
    # Validate that the test_case_id and interaction_id from the URL match what's in the session,
    # to prevent users from accessing conversations not tied to their current session context.
    # This is a basic check; more robust session/conversation management might be needed for multi-user scenarios.
    if test_case_id != session.get('current_test_case_id') or \
       interaction_id != session.get('current_conversation_id'):
        flash("Invalid or expired conversation. Please start a new test.", "error")
        return redirect(url_for('web_interface.show_test_cases'))

    conversation_history = session.get('conversation_history', [])
    test_case = TestCase.query.get(test_case_id)

    if not test_case:
        current_app.logger.error(f"Test case {test_case_id} not found during show_conversation.")
        abort(404)

    # Flashed messages will be available directly in the template via get_flashed_messages()
    # No need to explicitly pass them here if using the standard flash pattern.

    return render_template('run_test_result.html',
                           test_case=test_case.to_dict(),
                           conversation_history=conversation_history,
                           current_conversation_id=interaction_id, # or session.get('current_conversation_id')
                           # raw_response_initial can be cleared or managed if needed
                           # For FR-012, focusing on history and follow-up form.
                           # The 'response' object from the initial call is not directly passed anymore.
                           # Flashed messages will handle latest AI response/error.
                           )

@web_interface_blueprint.route('/prepare_evaluation/<string:test_case_id>/<string:conversation_id>', methods=['GET'])
def prepare_evaluation(test_case_id, conversation_id):
    # Validate session and conversation ID (similar to show_conversation)
    if test_case_id != session.get('current_test_case_id') or \
       conversation_id != session.get('current_conversation_id'):
        flash("Invalid or expired session for evaluation. Please start a new test.", "error")
        return redirect(url_for('web_interface.show_test_cases'))

    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        current_app.logger.error(f"Test case {test_case_id} not found during prepare_evaluation.")
        abort(404)

    conversation_history = session.get('conversation_history', [])
    if not conversation_history:
        flash("Cannot prepare evaluation for an empty conversation.", "warning")
        # Redirect back to the conversation view, as something is amiss if history is empty here
        return redirect(url_for('web_interface.show_conversation',
                                test_case_id=test_case_id,
                                conversation_id=conversation_id))

    # This route now handles both displaying the confirmation (GET)
    # and triggering the evaluation (POST)
    if request.method == 'GET':
        return render_template('prepare_evaluation.html',
                               test_case=test_case.to_dict(),
                               conversation_history=conversation_history,
                               conversation_id=conversation_id)

    elif request.method == 'POST':
        # Trigger the evaluation
        if not test_case or not conversation_history: # Should be caught by GET, but double check
            flash("Missing test case data or conversation history for evaluation.", "error")
            return redirect(url_for('web_interface.show_test_cases'))

        evaluation_result = ai_connector.evaluate_conversation(
            conversation_history=conversation_history,
            expected_outcome=test_case.expected_outcome,
            test_case_description=test_case.description
        )

        session['last_evaluation_result'] = evaluation_result

        # Store verdict summary in session for display on test list page
        if evaluation_result.get('status') == 'success' or evaluation_result.get('verdict'):
            session.setdefault('all_test_evaluations', {})
            current_evals = session['all_test_evaluations'] # Get a mutable copy
            current_evals[test_case_id] = {
                'verdict': evaluation_result.get('verdict', 'Error'),
                'reasoning': evaluation_result.get('reasoning', 'N/A'),
                'timestamp': datetime.utcnow().isoformat()
            }
            session['all_test_evaluations'] = current_evals # Reassign to notify session of change

        session.modified = True # Ensure all session changes are saved

        # Log the evaluation attempt and its outcome (briefly)
        log_message = (
            f"--- LLM Evaluation Triggered ---\n"
            f"Test Case ID: {test_case_id}\n"
            f"Conversation ID: {conversation_id}\n"
            f"Evaluation Status: {evaluation_result.get('status')}\n"
            f"Verdict: {evaluation_result.get('verdict', 'N/A') if evaluation_result.get('status') == 'success' else 'Evaluation Error'}\n"
            f"--- End Evaluation Log ---"
        )
        try:
            current_app.logger.info(log_message)
        except RuntimeError:
            print(log_message)

        if evaluation_result.get('status') == 'success':
            flash(f"Evaluation completed. Verdict: {evaluation_result.get('verdict')}", "success")
        else:
            flash(f"Evaluation failed: {evaluation_result.get('message')}", "error")

        return redirect(url_for('web_interface.show_evaluation_result',
                                test_case_id=test_case_id,
                                conversation_id=conversation_id))
