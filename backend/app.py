import os
import uuid
from flask import Flask, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from converter import convert_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend/public")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=os.path.join(FRONTEND_DIR, "static"))
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300 MB

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/convert', methods=['POST'])
def convert_endpoint():
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file part'}), 400

    target_format = request.form.get('target_format')
    target_size_kb = request.form.get('target_size_kb')
    remove_bg_flag = request.form.get('remove_bg') == 'true'
    resize_percent = request.form.get('resize_percent')

    try:
        target_size_kb = int(target_size_kb) if target_size_kb else None
        resize_percent = int(resize_percent) if resize_percent else None
    except:
        target_size_kb = None
        resize_percent = None

    saved_files = []
    for f in files:
        if f.filename == '':
            continue
        filename = secure_filename(f.filename)
        jobid = str(uuid.uuid4())
        saved_path = os.path.join(UPLOAD_DIR, jobid + '_' + filename)
        f.save(saved_path)
        saved_files.append(saved_path)

    try:
        out_paths = convert_file(saved_files, target_format, target_size_kb, remove_bg_flag, resize_percent)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if isinstance(out_paths, list):
        # Devolver los archivos como zip si hay varios
        if len(out_paths) == 1:
            return send_file(out_paths[0], as_attachment=True)
        else:
            import zipfile
            zip_path = os.path.join(UPLOAD_DIR, f'{uuid.uuid4()}.zip')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for path in out_paths:
                    zf.write(path, os.path.basename(path))
            return send_file(zip_path, as_attachment=True)
    else:
        return send_file(out_paths, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
