from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.db import get_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def home():
    return render_template('doc-api.html')