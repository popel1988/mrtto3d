document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const statusContainer = document.getElementById('status-container');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.querySelector('.progress-bar');
    const previewContainer = document.getElementById('preview-container');
    const downloadContainer = document.getElementById('download-container');
    const downloadLink = document.getElementById('download-link');
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Formular-Daten sammeln
        const formData = new FormData(uploadForm);
        const files = document.getElementById('dicom-files').files;
        
        if (files.length === 0) {
            showStatus('error', 'Bitte wählen Sie mindestens eine DICOM-Datei aus.');
            return;
        }
        
        // UI aktualisieren
        uploadBtn.disabled = true;
        showStatus('info', 'Dateien werden hochgeladen...');
        progressContainer.classList.remove('d-none');
        progressBar.style.width = '10%';
        
        // AJAX-Anfrage senden
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.min(90, Math.round((e.loaded / e.total) * 100));
                progressBar.style.width = percentComplete + '%';
            }
        };
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    
                    if (response.success) {
                        progressBar.style.width = '100%';
                        showStatus('success', '3D-Modell wurde erfolgreich erstellt!');
                        
                        // Vorschau anzeigen
                        previewContainer.innerHTML = `<img src="${response.preview_url}" alt="3D-Modell Vorschau" class="img-fluid">`;
                        
                        // Download-Link aktualisieren
                        downloadLink.href = response.download_url;
                        downloadContainer.classList.remove('d-none');
                    } else {
                        showStatus('error', response.error || 'Ein unbekannter Fehler ist aufgetreten.');
                    }
                } catch (e) {
                    showStatus('error', 'Fehler beim Parsen der Serverantwort.');
                }
            } else {
                try {
                    const response = JSON.parse(xhr.responseText);
                    showStatus('error', response.error || 'Serverfehler: ' + xhr.status);
                } catch (e) {
                    showStatus('error', 'Serverfehler: ' + xhr.status);
                }
            }
            
            uploadBtn.disabled = false;
        };
        
        xhr.onerror = function() {
            showStatus('error', 'Netzwerkfehler beim Hochladen der Dateien.');
            uploadBtn.disabled = false;
        };
        
        xhr.send(formData);
    });
    
    function showStatus(type, message) {
        let alertClass = 'alert-info';
        
        if (type === 'error') {
            alertClass = 'alert-danger';
        } else if (type === 'success') {
            alertClass = 'alert-success';
        }
        
        statusContainer.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    }
    
    // Filter-Typ-Änderung überwachen
    document.getElementById('filter-type').addEventListener('change', function() {
        const sigmaField = document.getElementById('sigma');
        sigmaField.disabled = this.value !== 'gaussian';
    });
});
