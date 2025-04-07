from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.db import get_db

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
async def get_users():
    current_user = get_jwt_identity()
    conn = await get_db()
    user = await conn.fetchrow("SELECT is_admin FROM users WHERE id = $1", current_user)
    
    if not user or not user['is_admin']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    users = await conn.fetch("SELECT id, email, nickname, is_admin, avatar_url, created_at FROM users")
    await conn.close()
    
    return jsonify([dict(user) for user in users]), 200

@users_bp.route('/<uuid:user_id>', methods=['GET'])
@jwt_required()
async def get_user(user_id):
    conn = await get_db()
    user = await conn.fetchrow("SELECT id, email, nickname, is_admin, avatar_url, created_at FROM users WHERE id = $1", user_id)
    await conn.close()
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify(dict(user)), 200


@users_bp.route('/<uuid:user_id>/books', methods=['GET'])  # Alterado para uuid
@jwt_required()
async def get_user_books(user_id):
    conn = await get_db()
    current_user = get_jwt_identity()
    
    books = await conn.fetch("SELECT * FROM books WHERE user_id = $1", user_id)
    await conn.close()
    
    if not books:
        return jsonify({'error': 'Livros do usuário nao encontrados'}), 404
    if str(user_id) != str(current_user):
        return jsonify({'error': 'Acesso Negado'}), 403
    
    return jsonify([dict(book) for book in books]), 200 
            
          
@users_bp.route('/update', methods=['PUT'])
@jwt_required()
async def update_user():
    data = request.get_json()
    nickname = data.get('nickname')
    avatar_url = data.get('avatar_url')
    
    if not nickname:
        return jsonify({'error': 'O nickname é obrigatório'}), 400
    
    current_user = get_jwt_identity()
    conn = await get_db()
    await conn.execute("""
        UPDATE users SET nickname = $1, avatar_url = $2 WHERE id = $3
    """, nickname, avatar_url, current_user)
    await conn.close()
    
    return jsonify({'message': 'Perfil atualizado com sucesso'}), 200


