# Configuration (debug, DB path, etc.)
import os

class Config:
    """Base configuration"""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///patient_triage.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # PatientTriage specific
    TRIAGE_MODEL_PATH = 'ml/models/'
    MAX_QUEUE_SIZE = 100
    RETRIAGE_CHECK_INTERVAL_SEC = 30  # Check for re-triage alerts every 30 sec

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False