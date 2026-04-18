import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '../data/database/GSMS_data.db')
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'gwm-sales-secret-key'

    db.init_app(app)

    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Import models and create tables
    with app.app_context():
        from app import models
        db.create_all()

    return app
