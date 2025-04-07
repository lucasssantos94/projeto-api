from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.db import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
async def get_users():
    conn = await get_db()
    users = await conn.fetch("SELECT id, email, nickname, is_admin, avatar_url, created_at FROM users")
    return jsonify([dict(user) for user in users]), 200

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
async def update_user(user_id):
    current_user = get_jwt_identity()
    conn = await get_db()
    admin_check = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1", current_user)
    
    if not admin_check:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    nickname = data.get('nickname')
    is_admin = data.get('is_admin')
    
    await conn.execute("""
        UPDATE users SET nickname = $1, is_admin = $2 WHERE id = $3
    """, nickname, is_admin, user_id)
    
    return jsonify({'message': 'Usuário atualizado com sucesso'}), 200


@admin_bp.route('/books', methods=['GET'])
@jwt_required()
async def get_books():
    conn = await get_db()
    books = await conn.fetch("SELECT * FROM books")
    return jsonify([dict(book) for book in books]), 200

@admin_bp.route('/books/<int:book_id>', methods=['PATCH'])
@jwt_required()
async def update_book(book_id):
    current_user = get_jwt_identity()
    conn = await get_db()
    admin_check = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1", current_user)
    book = await conn.fetchrow("SELECT * FROM books WHERE id = $1", book_id)
    
    if not book:
        return jsonify({'error': 'Livro nao encontrado'}), 404
    
    if not admin_check:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    title = data.get('title')
    category = data.get('category')
    author = data.get('author')
    image_url = data.get('image_url')
    
    await conn.execute("""
        UPDATE books SET title = $1, category = $2, author = $3, image_url = $4 WHERE id = $5
    """,  data.get('title', book['title']),
             data.get('author', book['author']),
             data.get('category', book['category']),
             data.get('image_url', book['image_url']),
             book_id)
    
    return jsonify({'message': 'Livro atualizado com sucesso'}), 200

@admin_bp.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
async def delete_book(book_id):
    current_user = get_jwt_identity()
    conn = await get_db()
    admin_check = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1", current_user)
    
    if not admin_check:
        return jsonify({'error': 'Acesso negado'}), 403
    
    await conn.execute("DELETE FROM books WHERE id = $1", book_id)
    return jsonify({'message': 'Livro excluído com sucesso'}), 200
