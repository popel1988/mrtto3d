FROM python:3.10-slim

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Verzeichnisse für Uploads und Modelle erstellen
RUN mkdir -p uploads models

# Xvfb für Off-Screen-Rendering starten und Flask-App ausführen
CMD Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset & \
    export DISPLAY=:99 && \
    python app.py
