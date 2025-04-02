from flask import Flask, request, jsonify, render_template
from flask_cors import CORS 
import asyncpg
import re
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

app = Flask(__name__)
app.config['ASYNC_MODE'] = True
CORS(app)
    

def validar_url(url):
    regex = r"^https:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
    return re.match(regex, url)

# Configuração do banco de dados Neon
DATABASE_URL = os.getenv('DATABASE_URL')

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=30, ssl="require")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id SERIAL PRIMARY KEY, 
                titulo TEXT NOT NULL, 
                categoria TEXT NOT NULL, 
                autor TEXT NOT NULL, 
                imagem_url TEXT NOT NULL
            )
        """)
        print('Database created')
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        if conn:
            await conn.close()

# Corrigindo a inicialização do event loop
async def async_init():
    await init_db()

def sync_init():
    asyncio.run(async_init())

# Inicialização do banco de dados
sync_init()

@app.route('/')
def home_page():
    return render_template('docs.html', title="Home")

@app.route('/livros', methods=['GET'])
async def listar_livros():
    try:
        app.logger.info("Tentando conectar ao banco de dados...")
        conn = await asyncpg.connect(DATABASE_URL)
        app.logger.info("Conexão bem-sucedida, executando query...")
        
        livros = await conn.fetch("SELECT * FROM livros ORDER BY id")
        app.logger.info(f"Encontrados {len(livros)} livros")
        
        livros_formatados = [{
            'id': livro['id'],
            'titulo': livro['titulo'],
            'categoria': livro['categoria'],
            'autor': livro['autor'],
            'imagem_url': livro['imagem_url']
        } for livro in livros]
        
        return jsonify(livros_formatados)
        
    except Exception as e:
        app.logger.error(f"Erro na rota /livros: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500
    finally:
        if 'conn' in locals():
            await conn.close()

@app.route('/doar', methods=['POST'])
async def doar_livro():
    dados = request.get_json() 
       
    titulo = dados.get('titulo')
    categoria = dados.get('categoria')
    autor = dados.get('autor')
    imagem_url = dados.get('imagem_url')
    
    if not all([titulo, categoria, autor, imagem_url]):
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    if not validar_url(imagem_url):
        return jsonify({'error': 'URL da imagem inválida'}), 400
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("""
            INSERT INTO livros (titulo, categoria, autor, imagem_url)
            VALUES ($1, $2, $3, $4)
        """, titulo, categoria, autor, imagem_url)
        
        return jsonify({'message': 'Livro doado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            await conn.close()

@app.route('/editar/<int:livro_id>', methods=['PUT'])
async def editar_livro(livro_id):
    dados = request.get_json()

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        livro = await conn.fetchrow("SELECT * FROM livros WHERE id = $1", livro_id)

        if not livro:
            return jsonify({'message': 'Livro não encontrado'}), 404

        titulo = dados.get('titulo', livro['titulo'])
        categoria = dados.get('categoria', livro['categoria'])
        autor = dados.get('autor', livro['autor'])
        imagem_url = dados.get('imagem_url', livro['imagem_url'])

        if imagem_url and not validar_url(imagem_url):
            return jsonify({'error': 'URL da imagem inválida'}), 400

        await conn.execute("""
            UPDATE livros 
            SET titulo = $1, categoria = $2, autor = $3, imagem_url = $4
            WHERE id = $5
        """, titulo, categoria, autor, imagem_url, livro_id)

        return jsonify({'message': 'Livro editado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            await conn.close()

@app.route('/deletar/<int:livro_id>', methods=['DELETE'])
async def deletar_livro(livro_id):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        livro = await conn.fetchrow("SELECT * FROM livros WHERE id = $1", livro_id)

        if not livro:
            return jsonify({'message': 'Livro não encontrado'}), 404

        await conn.execute("DELETE FROM livros WHERE id = $1", livro_id)
        return jsonify({'message': 'Livro deletado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            await conn.close()

@app.route('/livros/<string:buscar_livro>', methods=['GET'])
async def buscar_livro(buscar_livro):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        livros = await conn.fetch("""
            SELECT * FROM livros 
            WHERE LOWER(titulo) LIKE LOWER($1) 
            OR LOWER(autor) LIKE LOWER($1)
            ORDER BY id
        """, f"%{buscar_livro}%")
        
        livros_formatados = [{
            'id': livro['id'],
            'titulo': livro['titulo'],
            'categoria': livro['categoria'],
            'autor': livro['autor'],
            'imagem_url': livro['imagem_url']
        } for livro in livros]

        if not livros_formatados:
            return jsonify({'message': 'Nenhum livro encontrado'}), 404

        return jsonify(livros_formatados), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            await conn.close()

if __name__ == '__main__':
    app.run(debug=True)