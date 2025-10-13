import os
import subprocess
from PIL import Image
from rembg import remove

TMP_DIR = "converted"
os.makedirs(TMP_DIR, exist_ok=True)

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {cmd}\nSTDOUT: {result.stdout.decode()}\nSTDERR: {result.stderr.decode()}"
        )
    return result.stdout.decode()

# ---------- Convertidores ---------- #
def convert_office_to_pdf(path, outdir):
    cmd = f'soffice --headless --convert-to pdf --outdir "{outdir}" "{path}"'
    run_cmd(cmd)
    basename = os.path.splitext(os.path.basename(path))[0]
    outpdf = os.path.join(outdir, basename + ".pdf")
    if not os.path.exists(outpdf):
        raise RuntimeError("LibreOffice conversion failed.")
    return outpdf

def compress_pdf_gs(in_pdf, out_pdf, quality="ebook"):
    cmd = (
        f'gswin64c -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 '
        f'-dPDFSETTINGS=/{quality} -dNOPAUSE -dQUIET -dBATCH '
        f'-sOutputFile="{out_pdf}" "{in_pdf}"'
    )
    run_cmd(cmd)
    return out_pdf

def compress_image(in_path, out_path, target_kb=None, resize_percent=None):
    img = Image.open(in_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Redimensionar según porcentaje
    if resize_percent and resize_percent < 100:
        width = int(img.width * resize_percent / 100)
        height = int(img.height * resize_percent / 100)
        img = img.resize((width, height), Image.ANTIALIAS)

    quality = 95
    img.save(out_path, format="JPEG", quality=quality)

    if target_kb:
        target_bytes = target_kb * 1024
        while os.path.getsize(out_path) > target_bytes and quality > 10:
            quality = max(10, int(quality * 0.8))
            img.save(out_path, format="JPEG", quality=quality)
    return out_path

def reencode_media_ffmpeg(in_path, out_path, target_kb=None, target_format=None):
    is_audio = target_format in ["mp3", "wav", "ogg", "m4a"]
    is_video = target_format in ["mp4", "mov", "avi", "webm", "mkv"]

    if not target_kb:
        if is_audio:
            cmd = f'ffmpeg -y -i "{in_path}" -vn -acodec libmp3lame "{out_path}"'
        elif is_video:
            cmd = f'ffmpeg -y -i "{in_path}" -c:v libx264 -preset medium -crf 23 -c:a aac "{out_path}"'
        else:
            cmd = f'ffmpeg -y -i "{in_path}" "{out_path}"'
        run_cmd(cmd)
        return out_path

    # Ajuste de bitrate según tamaño
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", in_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        duration_s = float(probe.stdout.decode().strip())
    except:
        duration_s = None

    if not duration_s:
        return reencode_media_ffmpeg(in_path, out_path, None, target_format)

    target_bits = target_kb * 8 * 1024
    bitrate_kbps = max(64, int(target_bits / duration_s / 1000))

    if is_audio:
        cmd = f'ffmpeg -y -i "{in_path}" -vn -acodec libmp3lame -b:a {bitrate_kbps}k "{out_path}"'
    elif is_video:
        cmd = (
            f'ffmpeg -y -i "{in_path}" -b:v {bitrate_kbps}k -b:a 128k '
            f'-maxrate {bitrate_kbps}k -bufsize {bitrate_kbps*2}k "{out_path}"'
        )
    else:
        cmd = f'ffmpeg -y -i "{in_path}" "{out_path}"'

    run_cmd(cmd)
    return out_path

# ---------- FUNCIÓN PRINCIPAL ---------- #
def convert_file(paths, target_format, target_size_kb=None, remove_bg_flag=False, resize_percent=None):
    if isinstance(paths, str):
        paths = [paths]

    output_paths = []
    for path in paths:
        basename = os.path.splitext(os.path.basename(path))[0]
        ext = os.path.splitext(path)[1].lower()
        outdir = TMP_DIR
        os.makedirs(outdir, exist_ok=True)

        # Borrar fondo (solo imágenes)
        if remove_bg_flag and ext in [".png", ".jpg", ".jpeg", ".webp"]:
            img = Image.open(path)
            result = remove(img)
            out_path = os.path.join(outdir, f"{basename}_nobg.png")
            result.save(out_path)
            if target_size_kb:
                out_path = compress_image(out_path, out_path, target_size_kb, resize_percent)
            output_paths.append(out_path)
            continue

        # Redimensionar imagen
        if resize_percent and ext in [".png", ".jpg", ".jpeg", ".webp"]:
            out_path = os.path.join(outdir, f"{basename}_resized.{ext[1:]}")
            output_paths.append(compress_image(path, out_path, target_size_kb, resize_percent))
            continue

        # Office → PDF
        if target_format == "pdf" and ext in [".doc", ".docx", ".ppt", ".pptx", ".odt", ".odp"]:
            outpdf = convert_office_to_pdf(path, outdir)
            output_paths.append(outpdf)
            continue

        # PDF → Comprimir
        if ext == ".pdf" and target_size_kb:
            compressed = os.path.join(outdir, basename + "_compressed.pdf")
            compress_pdf_gs(path, compressed, "ebook")
            output_paths.append(compressed)
            continue

        # Imágenes
        if target_format in ["jpg", "jpeg", "png", "webp"]:
            out_path = os.path.join(outdir, f"{basename}.{target_format}")
            output_paths.append(compress_image(path, out_path, target_size_kb, resize_percent))
            continue

        # Audio / video
        if target_format in ["mp3", "wav", "mp4", "mov", "avi", "webm", "mkv"]:
            out_path = os.path.join(outdir, f"{basename}.{target_format}")
            output_paths.append(reencode_media_ffmpeg(path, out_path, target_size_kb, target_format))
            continue

        # HTML → PDF
        if ext == ".html" and target_format == "pdf":
            out_path = os.path.join(outdir, basename + ".pdf")
            cmd = f'wkhtmltopdf "{path}" "{out_path}"'
            run_cmd(cmd)
            output_paths.append(out_path)
            continue

        # Default: devolver el archivo original
        output_paths.append(path)

    return output_paths if len(output_paths) > 1 else output_paths[0]
