# backend/test_client.py
import requests
import os

SERVER_URL = "http://127.0.0.1:5000/convert"
UPLOAD_FOLDER = "test_files"  # Carpeta donde pones DOCX, PDF, JPG, MP4
OUTPUT_FOLDER = "test_output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Lista de archivos de prueba
test_files = [
    "example.docx",
    "example.pdf",
    "example.jpg",
    "example.mp4"
]

# Target format y tamaño opcional (en KB)
target_format_map = {
    "example.docx": "pdf",
    "example.pdf": "pdf",
    "example.jpg": "jpg",
    "example.mp4": "mp4"
}
target_size_kb_map = {
    "example.docx": None,
    "example.pdf": 100,  # comprimir a 100 KB si es posible
    "example.jpg": 50,
    "example.mp4": 500
}

for file_name in test_files:
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        print(f"[SKIP] {file_name} no existe en {UPLOAD_FOLDER}")
        continue

    target_format = target_format_map.get(file_name)
    target_size_kb = target_size_kb_map.get(file_name)

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f)}
        data = {"target_format": target_format, "target_size_kb": target_size_kb}
        print(f"[UPLOAD] {file_name} → {target_format}, target {target_size_kb} KB")
        response = requests.post(SERVER_URL, files=files, data=data)
    
    if response.status_code == 200:
        out_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file_name)[0]}_converted.{target_format}")
        with open(out_path, "wb") as out_file:
            out_file.write(response.content)
        print(f"[OK] Guardado en {out_path}")
    else:
        print(f"[ERROR] {file_name}: {response.status_code} - {response.json()}")
