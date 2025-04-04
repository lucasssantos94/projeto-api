from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.db import get_db

books_bp = Blueprint('books', __name__)

@books_bp.route('/', methods=['GET'])
async def get_books():
    conn = await get_db()
    books = await conn.fetch("SELECT * FROM books")
    return jsonify([dict(book) for book in books]), 200

@books_bp.route('/', methods=['POST'])
@jwt_required()
async def add_book():
    data = request.get_json()
    user_id = get_jwt_identity()
    title = data.get('title')
    author = data.get('author')
    category = data.get('category')
    image_url = data.get('image_url')
    
    if not title or not author or not category or not image_url:
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    conn = await get_db()
    book = await conn.fetchrow(
        """
        INSERT INTO books (title, author, category, image_url, user_id)
        VALUES ($1, $2, $3, $4, $5) RETURNING *        
        """,
        title, author, category, image_url, user_id
    )
    return jsonify(dict(book)), 201
    
    
    # if not validar_url(image_url):
    #     return jsonify({'error': 'URL da imagem inválida'}), 400
    
   