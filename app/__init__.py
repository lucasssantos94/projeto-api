from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import asyncio

from app.core.db import init_db
from app.core.config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    JWTManager(app)
    
    asyncio.run(init_db())
    
    if not app.debug:
        import logging
        logging.basicConfig(level=logging.INFO)
        app.logger = logging.getLogger(__name__)
    
    mail.init_app(app)
    
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.books.routes import books_bp
    from app.admin.routes import admin_bp
    from app.users.routes import users_bp
    
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(users_bp, url_prefix='/users') 
    
    return app
