import app2
from flask import render_template, app


@app.route('/')
@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    book = get_book(book_id)
    if not book:
        return render_template('error.html', message='Libro no encontrado.')
    return render_template('delete_confirmation.html', book=book)

@app.route('/delete/confirm/<int:book_id>', methods=['POST'])
def delete_book_confirmed(book_id):
    delete_book_from_db(book_id) # Renombramos la función original
    return redirect(url_for('index'))

# Renombrar la función original para evitar colisión
def delete_book_from_db(book_id):
    key = f"{BOOK_KEY_PREFIX}{book_id}"
    return db.delete(key)

import os
from flask import Flask, render_template, request, redirect, url_for
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key')

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

db = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

BOOK_KEY_PREFIX = 'book:'

# -------------------- Funciones para Interactuar con KeyDB --------------------

def get_next_book_id():
    """Genera el siguiente ID único para un libro."""
    return db.incr('next_book_id')
# DÓNDE SE UTILIZA:
# - En la función add_book() cuando se registra un nuevo libro para asignarle un ID único.

def save_book(book_id, title, author, genre):
    """Guarda la información de un libro en KeyDB."""
    key = f"{BOOK_KEY_PREFIX}{book_id}"
    book_data = {
        'title': title,
        'author': author,
        'genre': genre
    }
    db.hmset(key, book_data)
# DÓNDE SE UTILIZA:
# - En la función add_book() para guardar la información del nuevo libro.
# - En la función update_book() para guardar la información actualizada del libro.

def get_book(book_id):
    """Recupera la información de un libro de KeyDB por su ID."""
    key = f"{BOOK_KEY_PREFIX}{book_id}"
    book_data = db.hgetall(key)
    if book_data:
        return {
            'id': book_id,
            'title': book_data.get(b'title').decode('utf-8'),
            'author': book_data.get(b'author').decode('utf-8'),
            'genre': book_data.get(b'genre').decode('utf-8')
        }
    return None
# DÓNDE SE UTILIZA:
# - En la función edit_book() para obtener la información del libro que se va a editar y mostrarla en el formulario.

def get_all_books():
    """Recupera la información de todos los libros de KeyDB."""
    keys = db.keys(f"{BOOK_KEY_PREFIX}*")
    books = []
    for key in keys:
        book_id = key.decode('utf-8').split(':')[1]
        book = get_book(book_id)
        if book:
            books.append(book)
    return books
# DÓNDE SE UTILIZA:
# - En la función index() para obtener la lista de todos los libros y mostrarla en la página principal.
# - En la función search_books() para tener la lista completa de libros para realizar la búsqueda.

def update_book(book_id, title, author, genre):
    """Actualiza la información de un libro existente en KeyDB."""
    key = f"{BOOK_KEY_PREFIX}{book_id}"
    book_data = {
        'title': title,
        'author': author,
        'genre': genre
    }
    return db.hmset(key, book_data)
# DÓNDE SE UTILIZA:
# - En la función edit_book() para guardar los cambios realizados en la información de un libro.

def delete_book(book_id):
    """Elimina un libro de KeyDB por su ID."""
    key = f"{BOOK_KEY_PREFIX}{book_id}"
    return db.delete(key)
# DÓNDE SE UTILIZA:
# - En la función delete_book_route() para eliminar el libro seleccionado por el usuario.

def search_books(query):
    """Busca libros por título, autor o género."""
    query = query.lower()
    all_books = get_all_books()
    results = []
    for book in all_books:
        if query in book['title'].lower() or \
           query in book['author'].lower() or \
           query in book['genre'].lower():
            results.append(book)
    return results
# DÓNDE SE UTILIZA:
# - En la función search_book_route() para realizar la búsqueda de libros basada en la consulta del usuario.

# -------------------- Rutas y Funciones de Vista (Qué se muestra en cada página) --------------------

@app.route('/')
def index():
    """Muestra la página principal con la lista de todos los libros."""
    books = get_all_books()
    return render_template('index.html', books=books)
# QUÉ DEBES CREAR:
# - Debes crear el archivo 'index.html' dentro de la carpeta 'templates' para mostrar la lista de libros.

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    """Muestra el formulario para agregar un nuevo libro y procesa el envío del formulario."""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        book_id = get_next_book_id()
        save_book(book_id, title, author, genre)
        return redirect(url_for('index'))
    return render_template('add_book.html')
# QUÉ DEBES CREAR:
# - Debes crear el archivo 'add_book.html' dentro de la carpeta 'templates' para mostrar el formulario de agregar libro.

@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    """Muestra el formulario para editar un libro y procesa el envío del formulario."""
    book = get_book(book_id)
    if not book:
        return render_template('error.html', message='Libro no encontrado.') # Asume que tienes un error.html
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        update_book(book_id, title, author, genre)
        return redirect(url_for('index'))
    return render_template('edit_book.html', book=book)
# QUÉ DEBES CREAR:
# - Debes crear el archivo 'edit_book.html' dentro de la carpeta 'templates' para mostrar el formulario de editar libro.

@app.route('/delete/<int:book_id>')
def delete_book_route(book_id):
    """Elimina un libro y redirige a la página principal."""
    delete_book(book_id)
    return redirect(url_for('index'))
# QUÉ DEBES CREAR:
# - En 'index.html', debes crear enlaces para eliminar cada libro, apuntando a esta ruta con el ID del libro.

@app.route('/search', methods=['GET', 'POST'])
def search_book_route():
    """Muestra el formulario de búsqueda y procesa la búsqueda."""
    if request.method == 'POST':
        query = request.form['query']
        results = search_books(query)
        return render_template('search_results.html', results=results, query=query)
    return render_template('search.html')
# QUÉ DEBES CREAR:
# - Debes crear el archivo 'search.html' dentro de la carpeta 'templates' para mostrar el formulario de búsqueda.
# - Debes crear el archivo 'search_results.html' dentro de la carpeta 'templates' para mostrar los resultados de la búsqueda.

if __name__ == '__main__':
    app.run(debug=True)