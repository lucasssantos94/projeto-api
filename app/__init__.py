from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import asyncio

from app.core.db import init_db
from app.core.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    JWTManager(app)
    
    asyncio.run(init_db())
    
    return app
