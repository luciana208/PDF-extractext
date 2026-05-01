import os

class Settings:
    # Estas variables coinciden con lo que busca mongo_connection.py
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "pdf_extraction_db")

settings = Settings()