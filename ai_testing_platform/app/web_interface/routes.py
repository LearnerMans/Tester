import os
from flask import Blueprint, request, redirect, url_for, render_template, current_app
from werkzeug.utils import secure_filename
from ..test_case_management.excel_parser import parse_excel_data
from .. import db # Import db instance from app package
from ..models.test_case import TestCase # Import TestCase model

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
                        expected_outcome=tc_data['Expected Outcome']
                        # Optional fields like category, priority, tags will be added later
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

    try:
        query = TestCase.query

        if filter_test_case_id:
            query = query.filter(TestCase.id.ilike(f"%{filter_test_case_id}%"))

        if filter_description_keyword:
            query = query.filter(TestCase.description.ilike(f"%{filter_description_keyword}%"))

        all_test_cases_db = query.order_by(TestCase.id).all() # Added order_by for consistent results

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
                           filter_description_keyword=filter_description_keyword)

@web_interface_blueprint.route('/', methods=['GET'])
def index():
    return redirect(url_for('web_interface.show_test_cases'))
