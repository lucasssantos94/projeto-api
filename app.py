from flask import Flask, request, jsonify, render_template
import sqlite3
import re

app = Flask(__name__)

def init_db():
   with sqlite3.connect('database.db') as conn:
       conn.execute("""CREATE TABLE IF NOT EXISTS livros (
           id INTEGER PRIMARY KEY, 
           titulo TEXT NOT NULL, 
           categoria TEXT NOT NULL, 
           autor TEXT NOT NULL, 
           imagem_url TEXT NOT NULL)""")
       print('Database created')
       
init_db()

@app.route('/')
def home_page():
    return render_template('docs.html', title="Home")

@app.route('/livros', methods=['GET'])
def listar_livros():
    with sqlite3.connect('database.db') as conn:        
        livros = conn.execute("SELECT * FROM livros").fetchall()
        
    livros_formatados = []
    for livro in livros:
        livros_formatados.append({
            'id': livro[0],
            'titulo': livro[1],
            'categoria': livro[2],
            'autor': livro[3],
            'imagem_url': livro[4]
        })
        
    return jsonify(livros_formatados)

def validar_url(url):
    regex = r"^https:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
    return re.match(regex, url)


@app.route('/doar', methods=['POST'])
def doar_livro():
    dados = request.get_json() 
       
    titulo = dados.get('titulo')
    categoria = dados.get('categoria')
    autor = dados.get('autor')
    imagem_url = dados.get('imagem_url')
    
    if not all([titulo, categoria, autor, imagem_url]):
        return jsonify({'error': 'Todos os campos devem ser preenchidos'}), 400
    
    if not validar_url(imagem_url):
        return jsonify({'error': 'URL da imagem inválida'}), 400
    
    with sqlite3.connect('database.db') as conn:
        conn.execute("""INSERT INTO livros (titulo, categoria, autor, imagem_url)
                     VALUES (?,?,?,?)""", (titulo, categoria, autor, imagem_url))
        
        conn.commit()
        
    return jsonify({'message': 'Livro doado com sucesso!'}), 201 


@app.route('/editar/<int:livro_id>', methods=['PUT'])
def editar_livro(livro_id):
    dados = request.get_json()

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT titulo, categoria, autor, imagem_url FROM livros WHERE id = ?", (livro_id,))
        livro = cursor.fetchone()

        if not livro:
            return jsonify({'message': 'Livro não encontrado'}), 404

        titulo = dados.get('titulo', livro[0])
        categoria = dados.get('categoria', livro[1])
        autor = dados.get('autor', livro[2])
        imagem_url = dados.get('imagem_url', livro[3])

        cursor.execute("""
            UPDATE livros 
            SET titulo = ?, categoria = ?, autor = ?, imagem_url = ?
            WHERE id = ?
        """, (titulo, categoria, autor, imagem_url, livro_id))

        conn.commit()

    return jsonify({'message': 'Livro editado com sucesso!'}), 200

@app.route('/deletar/<int:livro_id>', methods=['DELETE'])
def deletar_livro(livro_id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
        livro = cursor.fetchone()

        if not livro:
            return jsonify({'message': 'Livro nao encontrado'}), 404

        cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
        conn.commit()

    return jsonify({'message': 'Livro deletado com sucesso!'}), 200
    

if __name__ == '__main__':
    app.run(debug=True)

