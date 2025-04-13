from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.db import get_db

books_bp = Blueprint('books', __name__)

@books_bp.route('/', methods=['GET'])
async def get_books():
    conn = await get_db()
    books = await conn.fetch("SELECT * FROM books")
    return jsonify([dict(book) for book in books]), 200


@books_bp.route('/<string:search>', methods=['GET'])
async def search_books(search):
    conn = await get_db()
    books = await conn.fetch("SELECT * FROM books WHERE LOWER(title) ILIKE LOWER($1) OR LOWER(author) ILIKE LOWER($1)", f"%{search}%")
    
    if not books:
        return jsonify({'error': 'Livro nao encontrado'}), 404
    
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
    
    if not all([title, author, category, image_url]):
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



@books_bp.route('/<int:book_id>', methods=['PUT'])
@jwt_required()
async def update_book(book_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    title = data.get('title')
    author = data.get('author')
    category = data.get('category')
    image_url = data.get('image_url')
    
    conn = await get_db();
    book = await conn.fetchrow(
        "select * from books where id = $1 ",
        book_id
    )       
    
    if not book:
        return jsonify({'error': 'Livro nao encontrado'}), 404
    
    if str(book['user_id']) != str(user_id): 
        return jsonify({'error': 'Permissão negada'}), 403
    
    
    updated_book = await conn.fetchrow(
          """
        UPDATE books SET title = $1, author = $2, category = $3, image_url = $4
        WHERE id = $5 RETURNING *
        """, data.get('title', book['title']),
             data.get('author', book['author']),
             data.get('category', book['category']),
             data.get('image_url', book['image_url']),
             book_id
    )
    return jsonify(dict(updated_book)), 200
    
    
@books_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
async def delete_book(book_id):
    user_id = get_jwt_identity()
    conn = await get_db()
    book = await conn.fetchrow(
        "select * from books where id = $1 ",
        book_id
    )
    if not book:
        return jsonify({'error': 'Livro nao encontrado'}), 404
    
    if str(book['user_id']) != str(user_id):
        return jsonify({'error': 'Permissão negada'}), 403
    
    await conn.execute("DELETE FROM books WHERE id = $1", book_id)
    return jsonify({'message': 'Livro deletado com sucesso!'}), 200
