import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance. This will be configured and initialized with the app in create_app.
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configure Upload Folder
    # app.root_path is ai_testing_platform/app
    # os.path.abspath(os.path.join(app.root_path, '..', 'uploads')) ensures it's an absolute path
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
    from .web_interface.routes import web_interface_blueprint
    app.register_blueprint(web_interface_blueprint)

    # Import models here to ensure they are known to SQLAlchemy before create_all
    from .models import test_case

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
