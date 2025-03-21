from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
import shutil
import numpy as np
from processing import process_dicom_to_3d
from PIL import Image
import io
import pydicom

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MODELS_FOLDER'] = 'models'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max upload

# Stellen Sie sicher, dass die Ordner existieren
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODELS_FOLDER'], exist_ok=True)

def check_image_sizes(directory):
    """Überprüft die Größen aller DICOM-Bilder im Verzeichnis und gibt die Größen zurück."""
    image_shapes = {}
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            # Versuche, die Datei als DICOM zu öffnen
            ds = pydicom.dcmread(file_path)
            shape = ds.pixel_array.shape
            
            if shape not in image_shapes:
                image_shapes[shape] = []
            image_shapes[shape].append(filename)
        except Exception as e:
            print(f"Fehler beim Lesen von {filename}: {e}")
    
    return image_shapes

def resize_dicom_images(directory, target_shape=None):
    """
    Skaliert alle DICOM-Bilder im Verzeichnis auf die gleiche Größe.
    Wenn target_shape None ist, wird die häufigste Größe verwendet.
    """
    image_shapes = check_image_sizes(directory)
    
    if not image_shapes:
        raise ValueError("Keine gültigen DICOM-Bilder gefunden")
    
    # Wenn keine Zielgröße angegeben ist, verwende die häufigste Größe
    if target_shape is None:
        # Finde die häufigste Größe
        most_common_shape = max(image_shapes.items(), key=lambda x: len(x[1]))[0]
        target_shape = most_common_shape
    
    # Protokolliere die gefundenen Bildgrößen
    print(f"Gefundene Bildgrößen: {list(image_shapes.keys())}")
    print(f"Verwende Zielgröße: {target_shape}")
    
    # Skaliere alle Bilder, die nicht die Zielgröße haben
    for shape, filenames in image_shapes.items():
        if shape != target_shape:
            for filename in filenames:
                file_path = os.path.join(directory, filename)
                try:
                    # Öffne DICOM
                    ds = pydicom.dcmread(file_path)
                    
                    # Konvertiere zu NumPy-Array
                    img_array = ds.pixel_array
                    
                    # Skaliere mit PIL
                    img = Image.fromarray(img_array)
                    img_resized = img.resize((target_shape[1], target_shape[0]), Image.LANCZOS)
                    
                    # Konvertiere zurück zu NumPy-Array
                    new_array = np.array(img_resized)
                    
                    # Aktualisiere DICOM-Daten
                    ds.PixelData = new_array.tobytes()
                    ds.Rows, ds.Columns = new_array.shape
                    
                    # Speichere aktualisierte DICOM-Datei
                    ds.save_as(file_path)
                    
                    print(f"Datei {filename} wurde auf Größe {target_shape} skaliert")
                except Exception as e:
                    print(f"Fehler beim Skalieren von {filename}: {e}")
    
    return target_shape

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
    
    # Größenparameter aus dem Formular holen
    target_size = request.form.get('size', None)
    
    # Temporäres Verzeichnis für die DICOM-Dateien erstellen
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Dateien speichern
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)
    
    try:
        # Überprüfe die Bildgrößen und protokolliere sie
        image_shapes = check_image_sizes(temp_dir)
        
        # Wenn mehr als eine Bildgröße gefunden wurde, vereinheitliche sie
        if len(image_shapes) > 1:
            # Wenn eine bestimmte Größe ausgewählt wurde, verwende diese als Zielgröße
            target_shape = None
            if target_size:
                width, height = map(int, target_size.split('x'))
                target_shape = (height, width)  # DICOM verwendet (rows, columns)
            
            # Skaliere alle Bilder auf die gleiche Größe
            used_shape = resize_dicom_images(temp_dir, target_shape)
            print(f"Alle Bilder wurden auf Größe {used_shape} vereinheitlicht")
        
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
        
        # Sammle verfügbare Bildgrößen für die Rückgabe
        available_sizes = []
        for shape in image_shapes.keys():
            available_sizes.append(f"{shape[1]}x{shape[0]}")  # Umwandlung von (rows, columns) zu "widthxheight"
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'preview_url': f"/preview/{session_id}",
            'download_url': f"/download/{session_id}",
            'available_sizes': available_sizes
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Fehler: {e}\n{error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500
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

@app.route('/check-sizes', methods=['POST'])
def check_uploaded_sizes():
    """Überprüft die Größen der hochgeladenen Dateien ohne sie zu verarbeiten."""
    if 'files[]' not in request.files:
        return jsonify({'error': 'Keine Dateien hochgeladen'}), 400
    
    files = request.files.getlist('files[]')
    
    # Temporäres Verzeichnis erstellen
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Dateien speichern
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
        
        # Bildgrößen überprüfen
        image_shapes = check_image_sizes(temp_dir)
        
        # Formatiere die Ergebnisse für die Rückgabe
        result = {}
        for shape, filenames in image_shapes.items():
            size_str = f"{shape[1]}x{shape[0]}"  # Umwandlung von (rows, columns) zu "widthxheight"
            result[size_str] = len(filenames)
        
        return jsonify({
            'success': True,
            'sizes': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Aufräumen
        shutil.rmtree(temp_dir, ignore_errors=True)

# Neue Route zum Anzeigen verfügbarer Bildgrößen
@app.route('/available-sizes', methods=['GET'])
def get_available_sizes():
    # Standard-Größen
    sizes = ['400x300', '800x600', '1024x768']
    
    # Durchsuche vorhandene Bilder nach Größen
    for session_id in os.listdir(app.config['MODELS_FOLDER']):
        if session_id.endswith('_preview.png'):
            preview_path = os.path.join(app.config['MODELS_FOLDER'], session_id)
            try:
                with Image.open(preview_path) as img:
                    sizes.append(f"{img.width}x{img.height}")
            except Exception:
                pass
    
    return jsonify({'sizes': list(set(sizes))})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
