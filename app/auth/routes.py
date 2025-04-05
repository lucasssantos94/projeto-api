from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from asyncpg import UniqueViolationError
from app.core.db import get_db
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
async def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    nickname = data.get('nickname')
    if not all([email, password, nickname]):
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    hashed_password = bcrypt.hash(password)
    try:
        conn = await get_db()
        await conn.execute(
            """
            INSERT INTO users (email, password, nickname)
            VALUES ($1, $2, $3)
            """,
            email, hashed_password, nickname
        )
        return jsonify({'message': 'Cadastro realizado com sucesso!'}), 201
    except UniqueViolationError:
        return jsonify({'error': 'Email ja cadastrado'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
async def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    conn = await get_db()
    user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
    if not user or not bcrypt.verify(password, user['password']):
        return jsonify({'error': 'Email ou senha incorretos'}), 401
    
    access_token = create_access_token(identity=user['id'], expires_delta=datetime.timedelta(hours=2))
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
async def logout():
    return jsonify({'message': 'Logout realizado com sucesso!'}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Usuário {current_user} autenticado'}), 200
    
    