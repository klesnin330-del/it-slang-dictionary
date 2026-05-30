import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'diplom-secret-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dictionary.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False