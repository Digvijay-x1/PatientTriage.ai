# Flask main app

from flask import Flask
from flask_cors import CORS

from config import DevelopmentConfig
from db import db


def create_app(config_class=DevelopmentConfig):
    """Application factory"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS for React frontend
    CORS(
        app,
        origins=["http://localhost:5173"],
    )

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///patient_triage.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the SAME db instance used by the models
    db.init_app(app)

    # Import models so SQLAlchemy knows about all tables
    from models.patient import Patient
    from models.triage_assessment import TriageAssessment
    from models.coordinator_decision import CoordinatorDecision
    from models.audit_log import AuditLog
    from models.retriage_alert import RetriageAlert

    # Register blueprints
    from routes.patient_intake import intake_bp
    from routes.triage import triage_bp
    from routes.coordinator_review import coordinator_bp
    from routes.audit_trail import audit_bp
    from routes.retriage import retriage_bp
    

    app.register_blueprint(intake_bp)
    app.register_blueprint(triage_bp)
    app.register_blueprint(coordinator_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(retriage_bp)
    

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()

    from services.retriage_scheduler import start_retriage_monitor

    start_retriage_monitor(app)

    app.run(
        debug=True,
        port=5000,
        use_reloader=False,  
    )