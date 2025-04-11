from flask import Blueprint, request, jsonify, url_for, current_app, flash, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from asyncpg.exceptions import UniqueViolationError
from app.core.db import get_db
from app.email.email_service import send_reset_email, generate_reset_token, verify_reset_token
import asyncpg
import datetime
import logging
from uuid import UUID

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
async def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        nickname = data.get('nickname')
        avatar_url = data.get('avatar_url')
        is_admin = data.get('is_admin')
        
        if not all([email, password, nickname]):
            return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
        
        if '@' not in email:
            return jsonify({'error': 'Email inválido'}), 400
        
        hashed_password = bcrypt.hash(password)
        conn = await get_db()

        try:
            await conn.execute(
                "INSERT INTO users (email, password, nickname, avatar_url, is_admin) VALUES ($1, $2, $3, $4, $5)",
                email, hashed_password, nickname, avatar_url, is_admin
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
            logger.error(f"Erro no banco de dados: {str(e)}")
            return jsonify({'error': 'Erro no banco de dados'}), 500
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
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
    await conn.close()
    
    if not user:
        return jsonify({'error': 'Email não cadastrado'}), 401
    
    if not bcrypt.verify(password, user['password']):
        return jsonify({'error': 'Senha incorreta'}), 401

    access_token = create_access_token(
        identity=user['id'],
        additional_claims={            
            "nickname": user['nickname'], 
            "avatar_url": user['avatar_url'], 
            "email": user['email'],  
            "is_admin": user['is_admin'] 
        }
    )
    return jsonify({
        'access_token': access_token,
        'user_info': {  
            'id': str(user['id']),
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

@auth_bp.route('/forgot-password', methods=['POST'])
async def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    
    conn = None
    try:
        conn = await get_db()
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        
        if user:
            logger.info(f"Iniciando processo de reset para {email}")
            
            user_id_str = str(user['id'])
            await send_reset_email(
                current_app._get_current_object(),
                user['email'],
                user['nickname'],
                user_id_str
            )
        
        return jsonify({'message': 'Se o email existir, enviaremos instruções'}), 200
        
    except Exception as e:
        logger.error(f"Erro no reset de senha: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro no servidor'}), 500
    finally:
        if conn:
            await conn.close()

@auth_bp.route('/reset-password/<token>', methods=['POST'])
async def reset_password(token):
    conn = None  # ← importante para evitar erro no finally
    data = request.get_json()
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([new_password, confirm_password]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'As senhas não coincidem'}), 400

    try:
        try:
            user_id = verify_reset_token(current_app._get_current_object(), token)
        except Exception as e:
            logger.error(f"Erro ao verificar token: {str(e)}", exc_info=True)
            return jsonify({'error': 'Link inválido ou expirado'}), 400

        if not user_id:
            return jsonify({'error': 'Link inválido ou expirado'}), 400

        conn = await get_db()
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # com passlib
        from passlib.hash import bcrypt
        hashed_password = bcrypt.hash(new_password)

        await conn.execute(
                "UPDATE users SET password = $1 WHERE id = $2",
                hashed_password, user_id
        )

        return jsonify({'message': 'Senha redefinida com sucesso!'}), 200

    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro ao redefinir senha'}), 500

    finally:
        if conn:
            await conn.close()
