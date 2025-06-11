import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance. This will be configured and initialized with the app in create_app.
db = SQLAlchemy()

def create_app():
    # Configure static_folder to point to 'app/static' relative to 'run.py' (project root)
    # However, Flask's first argument __name__ (which becomes app.name 'app') means it will look for 'static'
    # folder inside the 'app' package directory (ai_testing_platform/app/static) by default if static_folder is not set.
    # So, by convention, if our static files are in ai_testing_platform/app/static,
    # and our app is named 'app' (from Flask(__name__)), then no explicit static_folder might be needed.
    # Let's explicitly set it for clarity and robustness, assuming 'app' is the application package.
    # The app.root_path will be 'ai_testing_platform/app'.
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',  # This will resolve to ai_testing_platform/app/static
                template_folder='../templates') # Templates are in ai_testing_platform/templates

    # Secret Key for session management
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_default_secret_key_123!@#')

    # Configure Upload Folder (relative to project root, 'ai_testing_platform/' directory where run.py is)
    # app.root_path is 'ai_testing_platform/app'
    upload_folder_path = os.path.abspath(os.path.join(app.root_path, '..', 'uploads'))
    app.config['UPLOAD_FOLDER'] = upload_folder_path

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configure SQLAlchemy
    # The database file will be created in ai_testing_platform/instance/test_cases.db
    # Flask's instance_folder_path is automatically managed and is a good place for DBs.
    db_path = os.path.join(app.instance_path, 'test_cases.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure instance folder exists for SQLite DB
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass # Potentially already exists

    # Initialize extensions
    db.init_app(app)

    # Import and register blueprints
    # The web_interface_blueprint might have its own static_folder defined (e.g. for blueprint-specific static files)
    # but url_for('static', filename='css/main.css') in base.html will use the app-level static folder.
    from .web_interface.routes import web_interface_blueprint
    app.register_blueprint(web_interface_blueprint)

    # Import models here to ensure they are known to SQLAlchemy before create_all
    from .models import test_case

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
