# MRT zu 3D-Modell Konverter

Diese Webanwendung ermöglicht die Konvertierung von MRT-Bildern (DICOM) in 3D-Modelle (STL), die für 3D-Druck oder weitere Analysen verwendet werden können.

## Funktionen

- Upload von DICOM-Dateien (MRT-Bilder)
- Anpassbare Schwellenwerte für die Segmentierung
- Verschiedene Bildfilter zur Verbesserung der Qualität
- 3D-Vorschau des generierten Modells
- Download des 3D-Modells im STL-Format

## Installation mit Docker

### Voraussetzungen

- Docker und Docker Compose installiert

### Installation und Start

1. Repository klonen:
git clone https://github.com/username/mrt-3d-konverter.git
cd mrt-3d-konverter
2. Docker-Container starten:
docker-compose up -d
3. Die Anwendung ist nun unter http://localhost:5000 verfügbar.

## Manuelle Installation

### Voraussetzungen

- Python 3.9 oder höher
- Abhängigkeiten für OpenGL und X-Server

### Installation

1. Repository klonen:
git clone https://github.com/username/mrt-3d-konverter.git
cd mrt-3d-konverter
2. Virtuelle Umgebung erstellen und aktivieren:
python -m venv venv
source venv/bin/activate # Unter Windows: venv\Scripts\activate
3. Abhängigkeiten installieren:
pip install -r requirements.txt
4. Anwendung starten:
python app.py
5. Die Anwendung ist nun unter http://localhost:5000 verfügbar.

## Verwendung

1. DICOM-Dateien einer MRT-Serie hochladen
2. Segmentierungsparameter anpassen:
- Min. Schwellenwert: Niedrigere Werte erfassen mehr Gewebe
- Max. Schwellenwert: Höhere Werte sind selektiver
3. Bildverarbeitungsoptionen wählen:
- Gaussian-Filter: Reduziert Rauschen, erhöht aber die Verarbeitungszeit
- Median-Filter: Alternative zum Gaussian-Filter
4. "Hochladen und Verarbeiten" klicken
5. Nach der Verarbeitung erscheint eine Vorschau des 3D-Modells
6. Das fertige 3D-Modell kann als STL-Datei heruntergeladen werden

## Lizenz

MIT
