import pydicom
import os
import numpy as np
from scipy import ndimage
from skimage import measure
import pyvista as pv
import matplotlib.pyplot as plt

def load_dicom_series(directory_path):
    """Lädt eine Serie von DICOM-Dateien aus einem Verzeichnis."""
    dicom_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) 
                  if os.path.isfile(os.path.join(directory_path, f))]
    
    dicom_datasets = []
    for file in dicom_files:
        try:
            dicom_datasets.append(pydicom.dcmread(file))
        except:
            print(f"Konnte Datei nicht lesen: {file}")
    
    # Sortieren nach Schichtposition oder Instanznummer
    if dicom_datasets:
        if hasattr(dicom_datasets[0], 'SliceLocation'):
            dicom_datasets.sort(key=lambda x: x.SliceLocation)
        elif hasattr(dicom_datasets[0], 'InstanceNumber'):
            dicom_datasets.sort(key=lambda x: x.InstanceNumber)
    
    return dicom_datasets

def extract_pixel_data(dicom_datasets):
    """Extrahiert die Pixeldaten aus DICOM-Datensätzen und erstellt ein 3D-Array."""
    # Pixeldaten extrahieren und ggf. Rescale Slope/Intercept anwenden
    pixel_arrays = []
    for ds in dicom_datasets:
        pixel_array = ds.pixel_array.astype(np.float32)
        
        # Rescale Slope und Intercept anwenden, falls vorhanden
        if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
            pixel_array = pixel_array * ds.RescaleSlope + ds.RescaleIntercept
        
        pixel_arrays.append(pixel_array)
    
    # 3D-Array erstellen
    volume_3d = np.stack(pixel_arrays, axis=0)
    
    return volume_3d

def apply_filters(volume_data, filter_type='gaussian', sigma=1.0):
    """Wendet Filter auf die Volumendaten an."""
    if filter_type == 'gaussian':
        return ndimage.gaussian_filter(volume_data, sigma=sigma)
    elif filter_type == 'median':
        return ndimage.median_filter(volume_data, size=3)
    else:
        return volume_data

def threshold_segmentation(volume_data, min_threshold, max_threshold=None):
    """Führt eine einfache Schwellenwert-Segmentierung durch."""
    if max_threshold is None:
        return volume_data >= min_threshold
    else:
        return (volume_data >= min_threshold) & (volume_data <= max_threshold)

def create_3d_model(binary_volume, spacing=(1.0, 1.0, 1.0), step_size=1):
    """Erstellt ein 3D-Modell aus einem binären Volumen mit dem Marching Cubes Algorithmus."""
    # Marching Cubes Algorithmus anwenden
    verts, faces, normals, values = measure.marching_cubes(
        binary_volume[::step_size, ::step_size, ::step_size], 
        level=0.5,
        spacing=tuple(s * step_size for s in spacing)
    )
    
    # Faces für PyVista umformatieren (jede Fläche hat 3 Vertices)
    faces_pv = np.hstack([np.full((len(faces), 1), 3), faces])
    
    # PyVista-Mesh erstellen
    mesh = pv.PolyData(verts, faces_pv)
    mesh['Normals'] = normals
    
    return mesh

def save_preview_image(mesh, output_file):
    """Speichert eine Vorschau des 3D-Modells als Bild."""
    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
    plotter.add_mesh(mesh, color='white', smooth_shading=True)
    plotter.view_isometric()
    plotter.screenshot(output_file)
    plotter.close()

def process_dicom_to_3d(input_dir, output_stl, preview_file, min_threshold=300, max_threshold=1500, filter_type='gaussian', sigma=1.0):
    """Hauptfunktion zur Verarbeitung von DICOM zu 3D."""
    # DICOM-Dateien laden
    dicom_datasets = load_dicom_series(input_dir)
    
    if not dicom_datasets:
        raise ValueError("Keine gültigen DICOM-Dateien gefunden")
    
    # Volumendaten extrahieren
    volume_data = extract_pixel_data(dicom_datasets)
    
    # Bildverarbeitung
    filtered_volume = apply_filters(volume_data, filter_type=filter_type, sigma=sigma)
    
    # Segmentierung
    binary_volume = threshold_segmentation(filtered_volume, min_threshold=min_threshold, max_threshold=max_threshold)
    
    # Pixelabstände aus DICOM-Daten extrahieren (falls vorhanden)
    spacing = (1.0, 1.0, 1.0)  # Standardwerte
    if hasattr(dicom_datasets[0], 'PixelSpacing') and hasattr(dicom_datasets[0], 'SliceThickness'):
        pixel_spacing = dicom_datasets[0].PixelSpacing
        slice_thickness = dicom_datasets[0].SliceThickness
        spacing = (slice_thickness, pixel_spacing[0], pixel_spacing[1])
    
    # 3D-Modell erstellen
    mesh = create_3d_model(binary_volume, spacing=spacing)
    
    # Modell glätten
    mesh = mesh.smooth(n_iter=100)
    
    # Vorschau speichern
    save_preview_image(mesh, preview_file)
    
    # STL-Datei exportieren
    mesh.save(output_stl)
    
    return True
