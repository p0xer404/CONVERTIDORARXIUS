import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [format, setFormat] = useState("pdf");
  const [size, setSize] = useState("");
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert("Selecciona un archivo primero");
      return;
    }

    setMessage("Procesando...");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_format", format);
    if (size) formData.append("target_size_kb", size);

    try {
      const response = await fetch("/convert", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        setMessage("Error: " + err.error);
        return;
      }

      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `${file.name.split(".")[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setMessage("Archivo convertido con éxito!");
    } catch (error) {
      setMessage("Error: " + error.message);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "50px auto", fontFamily: "Arial, sans-serif" }}>
      <h1>Conversor de Archivos</h1>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 10, padding: 20, background: "#f9f9f9", borderRadius: 10 }}>
        <label>Selecciona archivo:</label>
        <input type="file" onChange={handleFileChange} />

        <label>Formato de salida:</label>
        <select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="pdf">PDF</option>
          <option value="jpg">JPG</option>
          <option value="png">PNG</option>
          <option value="webp">WEBP</option>
          <option value="mp3">MP3</option>
          <option value="mp4">MP4</option>
        </select>

        <label>Tamaño máximo (KB, opcional):</label>
        <input type="number" value={size} onChange={(e) => setSize(e.target.value)} placeholder="Ej: 500" />

        <button type="submit" style={{ padding: 10, background: "#007BFF", color: "#fff", border: "none", borderRadius: 5 }}>
          Convertir
        </button>
      </form>
      {message && <p style={{ marginTop: 15 }}>{message}</p>}
    </div>
  );
}

export default App;
