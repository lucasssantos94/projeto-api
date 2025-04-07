from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from asyncpg.exceptions import UniqueViolationError
from app.core.db import get_db
import asyncpg
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
async def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        nickname = data.get('nickname')
        
        if not all([email, password, nickname]):
            return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
        
        if '@' not in email:
            return jsonify({'error': 'Email inválido'}), 400
        
        hashed_password = bcrypt.hash(password)
        conn = await get_db()

        try:
            await conn.execute(
                "INSERT INTO users (email, password, nickname) VALUES ($1, $2, $3)",
                email, hashed_password, nickname
            )
            await conn.close()
            return jsonify({'message': 'Cadastro realizado com sucesso!'}), 201
        
        except UniqueViolationError as e:
            msg = str(e).lower()
            if 'email' in msg:
                return jsonify({'error': 'Email já cadastrado'}), 409
            elif 'nickname' in msg:
                return jsonify({'error': 'Nickname já em uso'}), 409
            return jsonify({'error': 'Dados já cadastrados'}), 409

        except asyncpg.PostgresError as e:
            # Para capturar qualquer erro relacionado ao PostgreSQL
            print("PostgresError:", e)
            return jsonify({'error': 'Erro no banco de dados'}), 500
        
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return jsonify({'error': 'Erro interno no servidor'}), 500

@auth_bp.route('/login', methods=['POST'])
async def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    conn = await get_db()
    user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
    
    if not user:
        return jsonify({'error': 'Email não cadastrado'}), 401
    
    if not bcrypt.verify(password, user['password']):
        return jsonify({'error': 'senha incorreto'}), 401
    


    access_token = create_access_token(
        identity=user['id'],
        additional_claims={
            "role": user['role'],
            "nickname": user['nickname'], 
            "avatar_url": user['avatar_url'], 
            "email": user['email'],  
            "is_admin": user['role'] == "admin"  
        }
    )
    return jsonify({
        'access_token': access_token,
        'user_info': {  
            'id': user['id'],
            'nickname': user['nickname'],
            'avatar_url': user['avatar_url'],
            'email': user['email'],
            'is_admin': user['is_admin'] == "admin"
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
async def logout():
    return jsonify({'message': 'Logout realizado com sucesso!'}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Usuário {current_user} autenticado'}), 200
    
    