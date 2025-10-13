const form = document.getElementById('converterForm');
const fileInput = document.getElementById('file');
const dropZone = document.getElementById('dropZone');
const fileList = document.getElementById('fileList');
const messageDiv = document.getElementById('message');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const historyList = document.getElementById('history');
const convertBtn = document.getElementById('convertBtn');
const toggleThemeBtn = document.getElementById('toggleTheme');
const formatSelect = document.getElementById('format');
const sizeInput = document.getElementById('size');

let selectedFiles = [];

// ---------- Funciones de utilidad ----------
function getValidFormats(ext) {
    ext = ext.toLowerCase();
    switch(ext) {
        case 'pdf': return ['docx', 'xlsx', 'jpg', 'png', 'webp']; // ejemplo
        case 'doc': case 'docx': return ['pdf'];
        case 'mp4': return ['mp3', 'wav'];
        case 'mp3': return ['wav'];
        case 'png': case 'jpg': case 'jpeg': return ['png','jpg','webp','remove_bg','compress'];
        case 'webp': return ['png','jpg','remove_bg','compress'];
        case 'html': return ['pdf'];
        default: return [];
    }
}

function showMessage(msg, type) {
    messageDiv.textContent = msg;
    messageDiv.className = 'toast ' + type;
    setTimeout(() => messageDiv.textContent = '', 4000);
}

function updateFileInput() {
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(f => dataTransfer.items.add(f));
    fileInput.files = dataTransfer.files;
}

// ---------- Drag & Drop ----------
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('hover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('hover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('hover');
    if(e.dataTransfer.files.length){
        selectedFiles = [...selectedFiles, ...e.dataTransfer.files];
        updateFileInput();
        renderFileList();
        updateFormatOptions();
    }
});

// ---------- Input change ----------
fileInput.addEventListener('change', (e) => {
    selectedFiles = [...selectedFiles, ...e.target.files];
    renderFileList();
    updateFormatOptions();
});

// ---------- Render lista de archivos ----------
function renderFileList() {
    fileList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const ext = file.name.split('.').pop().toLowerCase();
        let emoji = '📄';
        if (ext === 'pdf') emoji = '📕';
        else if (['jpg','jpeg','png','webp'].includes(ext)) emoji = '🖼️';
        else if (['mp3','wav','ogg'].includes(ext)) emoji = '🎵';
        else if (['mp4','avi','mov','mkv','webm'].includes(ext)) emoji = '🎬';
        else if (['zip','rar','7z'].includes(ext)) emoji = '🗜️';
        else if (['txt','doc','docx'].includes(ext)) emoji = '📝';
        else if (['xls','xlsx'].includes(ext)) emoji = '📊';
        else if (['ppt','pptx'].includes(ext)) emoji = '📈';

        const div = document.createElement('div');
        div.classList.add('file-item');
        div.innerHTML = `
            <span class="file-icon">${emoji}</span>
            <span>${file.name}</span>
            <button class="remove-file" data-index="${index}">❌</button>
        `;
        fileList.appendChild(div);
    });

    document.querySelectorAll('.remove-file').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.target.dataset.index);
            selectedFiles.splice(idx,1);
            updateFileInput();
            renderFileList();
            updateFormatOptions();
        });
    });
}

// ---------- Update opciones de formato ----------
function updateFormatOptions() {
    if(selectedFiles.length !== 1) return;
    const ext = selectedFiles[0].name.split('.').pop().toLowerCase();
    const validFormats = getValidFormats(ext);

    formatSelect.innerHTML = '';
    validFormats.forEach(f => {
        let text = f.toUpperCase(); // <-- Aquí convertimos a mayúsculas
        if(f === 'remove_bg') text = 'Borrar fondo';
        if(f === 'compress') text = 'Comprimir / Redimensionar';
        formatSelect.innerHTML += `<option value="${f}">${text}</option>`;
    });

    // Mostrar/ocultar opciones del checkbox y slider
    if(['jpg','jpeg','png','webp'].includes(ext)){
        removeBgDiv.style.display = 'block';
    } else {
        removeBgDiv.style.display = 'none';
    }
}

// ---------- Theme toggle ----------
toggleThemeBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    toggleThemeBtn.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
});

// ---------- Form submit ----------
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if(selectedFiles.length === 0){
        showMessage('Selecciona al menos un archivo','error');
        return;
    }

    const target_format = formatSelect.value;
    const target_size_kb = sizeInput.value;
    let remove_bg = false;
    let resize_percent = null;

    if(target_format === 'remove_bg') remove_bg = true;
    if(target_format === 'compress') {
        resize_percent = parseInt(prompt('Reducción en % (ej: 25 para 25%)', '100')) || 100;
    }

    convertBtn.disabled = true;
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';

    for(let i=0;i<selectedFiles.length;i++){
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append('file', file);

        // Normalizar el formato
        let finalFormat = target_format;
        if(['remove_bg','compress'].includes(target_format)){
            const ext = file.name.split('.').pop().toLowerCase();
            finalFormat = ext; // mantener el mismo formato
        }

        formData.append('target_format', finalFormat);
        if(target_size_kb) formData.append('target_size_kb', target_size_kb);
        formData.append('remove_bg', remove_bg);
        if(resize_percent) formData.append('resize_percent', resize_percent);

        try{
            const response = await fetch('/convert',{method:'POST', body:formData});
            if(!response.ok){
                const err = await response.json();
                showMessage('Error: '+err.error,'error');
                continue;
            }
            const blob = await response.blob();
            const downloadUrl = URL.createObjectURL(blob);
            addHistory(file.name, finalFormat, downloadUrl);

            const percent = Math.round(((i+1)/selectedFiles.length)*100);
            progressBar.style.width = percent+'%';
            progressText.textContent = percent+'%';
        } catch(err){
            showMessage('Error: '+err.message,'error');
        }
    }

    showMessage('Archivos convertidos con éxito ✔️','success');
    convertBtn.disabled = false;
    setTimeout(()=>{ progressContainer.style.display='none'; },500);
});

// ---------- Historial ----------
function addHistory(filename, format, url){
    const li = document.createElement('li');
    let icon='📄';
    const ext = format.toLowerCase();
    if(ext==='pdf') icon='📕';
    else if(['jpg','jpeg','png','webp'].includes(ext)) icon='🖼️';
    else if(['mp3','wav','ogg'].includes(ext)) icon='🎵';
    else if(['mp4','avi','mov'].includes(ext)) icon='🎬';
    else if(['zip','rar'].includes(ext)) icon='🗜️';
    else if(['txt','doc','docx'].includes(ext)) icon='📝';

    li.innerHTML = `
        <div class="file-info">
            <span class="file-icon">${icon}</span>
            <span class="file-name">${filename} → ${format.toUpperCase()}</span>
        </div>
        <button class="download-btn">📥</button>
        <button class="remove-btn">❌</button>
    `;

    li.querySelector('.download-btn').addEventListener('click',()=>{
        const a = document.createElement('a');
        a.href = url;
        a.download = filename.split('.')[0]+'.'+format;
        document.body.appendChild(a);
        a.click();
        a.remove();
    });

    li.querySelector('.remove-btn').addEventListener('click',()=>li.remove());
    historyList.appendChild(li);
}
