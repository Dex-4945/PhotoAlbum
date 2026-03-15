import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_collections():
    base = app.config['UPLOAD_FOLDER']
    if not os.path.exists(base):
        os.makedirs(base)
    return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]

def get_collection_images(collection_name):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], collection_name)
    if not os.path.exists(folder):
        return []
    return [
        f for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f)) and allowed_file(f)
    ]

@app.route('/')
def index():
    collections = get_collections()
    return render_template('index.html', collections=collections)

@app.route('/collection/<name>')
def collection(name):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], name)
    if not os.path.exists(folder):
        abort(404)
    images = get_collection_images(name)
    return render_template('collection.html', collection_name=name, images=images)

@app.route('/uploads/<collection>/<filename>')
def uploaded_file(collection, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], collection)
    return send_from_directory(folder, filename)

@app.route('/api/collections', methods=['GET'])
def api_collections():
    return jsonify(get_collections())

@app.route('/api/create_collection', methods=['POST'])
def create_collection():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Collection name is required'}), 400

    safe_name = secure_filename(name)
    if not safe_name:
        return jsonify({'error': 'Invalid collection name'}), 400

    folder = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    os.makedirs(folder, exist_ok=True)

    files = request.files.getlist('images')
    saved = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(folder, filename))
            saved.append(filename)

    return jsonify({'collection': safe_name, 'saved': saved})

@app.route('/api/add_to_collection', methods=['POST'])
def add_to_collection():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Collection name is required'}), 400

    safe_name = secure_filename(name)
    folder = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not os.path.exists(folder):
        return jsonify({'error': 'Collection not found'}), 404

    files = request.files.getlist('images')
    saved = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(folder, filename))
            saved.append(filename)

    return jsonify({'collection': safe_name, 'saved': saved})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)