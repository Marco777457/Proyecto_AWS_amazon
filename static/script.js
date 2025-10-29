fetch('/api/costs')
  .then(res => res.json())
  .then(data => {
    const div = document.getElementById('data');
    let html = '<table border="1" cellpadding="5"><tr><th>Fecha</th><th>EC2 ($)</th><th>S3 ($)</th></tr>';
    data.forEach(row => {
      html += `<tr><td>${row.date}</td><td>${row.ec2.toFixed(2)}</td><td>${row.s3.toFixed(2)}</td></tr>`;
    });
    html += '</table>';
    div.innerHTML = html;
  });

// --- Iniciar cámara ---
const video = document.getElementById('video');

if (video) {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
    })
    .catch(err => {
      console.error("No se puede acceder a la cámara:", err);
      document.getElementById('cameraResult').innerText = "⚠️ No se puede acceder a la cámara";
    });

  document.getElementById('captureBtn').addEventListener('click', async () => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    // Convierte la imagen a blob
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    const formData = new FormData();
    formData.append('image', blob, 'captura.png');

    // Envía la imagen a Flask
    const response = await fetch('/api/camera', { method: 'POST', body: formData });
    const result = await response.json();

    document.getElementById('cameraResult').innerText = result.message;
  });
}
