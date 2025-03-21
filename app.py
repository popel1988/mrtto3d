from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
import shutil
from processing import process_dicom_to_3d

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MODELS_FOLDER'] = 'models'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max upload

# Stellen Sie sicher, dass die Ordner existieren
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODELS_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({'error': 'Keine Dateien hochgeladen'}), 400
    
    files = request.files.getlist('files[]')
    
    # Parameter aus dem Formular holen
    min_threshold = int(request.form.get('min_threshold', 300))
    max_threshold = int(request.form.get('max_threshold', 1500))
    filter_type = request.form.get('filter_type', 'gaussian')
    sigma = float(request.form.get('sigma', 1.0))
    
    # Temporäres Verzeichnis für die DICOM-Dateien erstellen
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Dateien speichern
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(temp_dir, filename))
    
    try:
        # 3D-Modell erstellen
        output_file = os.path.join(app.config['MODELS_FOLDER'], f"{session_id}.stl")
        preview_file = os.path.join(app.config['MODELS_FOLDER'], f"{session_id}_preview.png")
        
        process_dicom_to_3d(
            temp_dir, 
            output_file, 
            preview_file,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            filter_type=filter_type,
            sigma=sigma
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'preview_url': f"/preview/{session_id}",
            'download_url': f"/download/{session_id}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Aufräumen
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/preview/<session_id>')
def preview(session_id):
    preview_file = os.path.join(app.config['MODELS_FOLDER'], f"{session_id}_preview.png")
    if os.path.exists(preview_file):
        return send_file(preview_file, mimetype='image/png')
    return jsonify({'error': 'Vorschau nicht gefunden'}), 404

@app.route('/download/<session_id>')
def download(session_id):
    output_file = os.path.join(app.config['MODELS_FOLDER'], f"{session_id}.stl")
    if os.path.exists(output_file):
        return send_file(output_file, as_attachment=True, download_name="3d_model.stl")
    return jsonify({'error': '3D-Modell nicht gefunden'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
