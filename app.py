import os
import csv
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
import pandas as pd
import cv2
import numpy as np

app = Flask(__name__)

# ---------------- CONFIGURACIÓN DE ARCHIVOS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

COSTS_CSV = os.path.join(DATA_DIR, 'costs.csv')

# ---------------- CREAR DATASET INICIAL ----------------
if not os.path.exists(COSTS_CSV):
    start = datetime.utcnow() - timedelta(days=30)
    rows = []
    for i in range(31):
        d = (start + timedelta(days=i)).strftime('%Y-%m-%d')
        ec2 = round(120 + 10 * random.random(), 2)
        s3 = round(30 + 5 * random.random(), 2)
        rds = round(60 + 6 * random.random(), 2)
        lambda_cost = round(15 + 3 * random.random(), 2)
        cloudfront = round(20 + 4 * random.random(), 2)
        dynamodb = round(25 + 5 * random.random(), 2)
        rows.append([d, ec2, s3, rds, lambda_cost, cloudfront, dynamodb])
    with open(COSTS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'ec2', 's3', 'rds', 'lambda', 'cloudfront', 'dynamodb'])
        writer.writerows(rows)

# ---------------- TEMPLATE HTML ----------------
TEMPLATE = '''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>VIGILA - Panel Integral AWS</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
    <style>
      body { padding: 20px; background-color: #f8f9fa; }
      .card { margin-bottom: 20px; }
      h3, h4 { color: #0d6efd; }
      video { border: 2px solid #0d6efd; border-radius: 8px; }
    </style>
  </head>
  <body>
    <div class="container">
      <h3 class="mb-3 text-center">🚀 VIGILA - Panel Integral de AWS</h3>
      <p class="text-center text-muted">Supervisión de costos, seguridad y escalabilidad de la infraestructura en la nube</p>

      <!-- 🧮 BLOQUE 1: Costos -->
      <div class="card">
        <div class="card-header bg-primary text-white">1️⃣ Optimización de costos en servicios AWS</div>
        <div class="card-body">
          <canvas id="costChart" height="120"></canvas>
          <div class="mt-3 d-flex justify-content-between">
            <button id="simulateBtn" class="btn btn-sm btn-outline-primary">Simular nuevo día</button>
            <strong><span id="latestTotals">Cargando...</span></strong>
          </div>
        </div>
      </div>

      <!-- 🔐 BLOQUE 2: Seguridad -->
      <div class="card">
        <div class="card-header bg-success text-white">2️⃣ Medidas de seguridad avanzadas en AWS</div>
        <div class="card-body">
          <ul>
            <li>🔒 <strong>Cifrado de datos</strong> en reposo y en tránsito mediante AWS KMS y SSL/TLS.</li>
            <li>👤 <strong>Gestión de accesos segura</strong> con IAM y políticas de mínimos privilegios.</li>
            <li>🕵️ <strong>Auditoría constante</strong> con AWS CloudTrail y AWS Config.</li>
            <li>🧠 <strong>Detección de amenazas</strong> con Amazon GuardDuty y AWS Security Hub.</li>
          </ul>
          <p class="text-muted mb-0">Estas medidas garantizan la protección de los datos y las cuentas de VIGILA.</p>
        </div>
      </div>

      <!-- ⚙️ BLOQUE 3: Escalabilidad -->
      <div class="card">
        <div class="card-header bg-warning">3️⃣ Escalabilidad y rendimiento de la infraestructura</div>
        <div class="card-body">
          <ul>
            <li>⚙️ Uso de <strong>Auto Scaling</strong> para ajustar automáticamente la capacidad de las instancias EC2.</li>
            <li>🌐 Implementación de <strong>Elastic Load Balancer (ELB)</strong> para distribuir el tráfico de video.</li>
            <li>🗄️ <strong>RDS Multi-AZ</strong> para bases de datos altamente disponibles y tolerantes a fallos.</li>
            <li>📦 <strong>Amazon S3</strong> como almacenamiento masivo de grabaciones de video.</li>
            <li>📊 Monitoreo de recursos con <strong>Amazon CloudWatch</strong> para garantizar rendimiento óptimo.</li>
          </ul>
          <p class="text-muted mb-0">Esto permite que la infraestructura de VIGILA crezca automáticamente según la demanda.</p>
        </div>
      </div>

      <!-- 🎥 BLOQUE 4: Cámara para detección -->
      <div class="card">
        <div class="card-header bg-info text-white">4️⃣ Lectura de servicios AWS mediante cámara</div>
        <div class="card-body text-center">
          <video id="video" width="320" height="240" autoplay></video><br><br>
          <button id="captureBtn" class="btn btn-outline-info">📷 Leer con cámara</button>
          <p id="cameraResult" class="mt-3 font-weight-bold text-primary"></p>
        </div>
      </div>
    </div>

    <!-- Script principal -->
    <script>
      var ctx = document.getElementById('costChart').getContext('2d');
      var chart;

      function fetchCosts() {
        fetch('/api/costs')
          .then(r => r.json())
          .then(data => {
            const labels = data.map(r => r.date);
            const datasets = [];
            const colors = ['#007bff','#28a745','#ffc107','#dc3545','#6f42c1','#17a2b8'];
            const keys = Object.keys(data[0]).filter(k => k !== 'date');

            keys.forEach((key, i) => {
              datasets.push({
                label: key.toUpperCase(),
                data: data.map(r => r[key]),
                fill: false,
                borderColor: colors[i % colors.length]
              });
            });

            if(!chart){
              chart = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: { responsive: true }
              });
            } else {
              chart.data.labels = labels;
              chart.data.datasets = datasets;
              chart.update();
            }

            const last = data[data.length-1];
            let total = 0;
            for (const key of keys) total += last[key];
            document.getElementById('latestTotals').innerText = 
              '💰 Total: $' + total.toFixed(2) + ' | ' + keys.map(k => `${k.toUpperCase()}: $${last[k].toFixed(2)}`).join(' | ');
          });
      }

      fetchCosts();
      setInterval(fetchCosts, 5000);
      document.getElementById('simulateBtn').addEventListener('click', ()=>fetch('/api/simulate', {method:'POST'}).then(_=>fetchCosts()));

      // ---- Cámara ----
      const video = document.getElementById('video');
      if (navigator.mediaDevices && video) {
        navigator.mediaDevices.getUserMedia({ video: true })
          .then(stream => { video.srcObject = stream; })
          .catch(err => console.error("No se puede acceder a la cámara:", err));

        document.getElementById('captureBtn').addEventListener('click', async () => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d').drawImage(video, 0, 0);
          const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
          const formData = new FormData();
          formData.append('image', blob, 'captura.png');

          const response = await fetch('/api/camera', { method: 'POST', body: formData });
          const result = await response.json();
          document.getElementById('cameraResult').innerText = result.message;
        });
      }
    </script>
  </body>
</html>
'''

# ---------------- FUNCIONES ----------------
def read_costs_csv(limit=31):
    df = pd.read_csv(COSTS_CSV, parse_dates=['date'])
    df = df.sort_values('date')
    rows = []
    for _, r in df.tail(limit).iterrows():
        row = {'date': r['date'].strftime('%Y-%m-%d')}
        for col in df.columns[1:]:
            row[col] = float(r[col])
        rows.append(row)
    return rows

# ---------------- RUTAS FLASK ----------------
@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/api/costs')
def api_costs():
    return jsonify(read_costs_csv())

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    df = pd.read_csv(COSTS_CSV, parse_dates=['date'])
    last_date = df['date'].max()
    new_date = (pd.to_datetime(last_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    last_row = df.iloc[-1]
    new_row = [new_date]
    for col in df.columns[1:]:
        new_row.append(round(max(0, float(last_row[col]) + random.uniform(-5, 8)), 2))
    with open(COSTS_CSV, 'a', newline='') as f:
        csv.writer(f).writerow(new_row)
    return jsonify({'ok': True, 'date': new_date})

@app.route('/api/camera', methods=['POST'])
def api_camera():
    file = request.files.get('image')
    if not file:
        return jsonify({'message': '⚠️ No se recibió imagen.'})

    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # Simulación de detección de servicios AWS
    servicios = ["EC2", "S3", "RDS", "Lambda", "CloudFront", "DynamoDB"]
    servicio_detectado = random.choice(servicios)

    return jsonify({'message': f'✅ Servicio detectado mediante cámara: {servicio_detectado}'})

# ---------------- MAIN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
