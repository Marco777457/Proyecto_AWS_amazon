import os
import csv
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, render_template_string, request
import pandas as pd
  
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

COSTS_CSV = os.path.join(DATA_DIR, 'costs.csv')

# Crear dataset inicial si no existe
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

# --- Template HTML ---
TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>VIGILA - AWS Cost & Security Dashboard (Extended)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
    <style>
      body { padding: 20px; }
      .card { margin-bottom: 16px; }
    </style>
  </head>
  <body>
    <div class="container">
      <h3 class="mb-3">VIGILA - AWS Cost Dashboard (Extended Version)</h3>

      <div class="card">
        <div class="card-header">1) Costos simulados de múltiples servicios AWS</div>
        <div class="card-body">
          <canvas id="costChart" height="120"></canvas>
          <div class="mt-3 d-flex justify-content-between">
            <button id="simulateBtn" class="btn btn-sm btn-outline-primary">Simular nuevo día</button>
            <strong><span id="latestTotals">Cargando...</span></strong>
          </div>
        </div>
      </div>
    </div>

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
              'Total: $' + total.toFixed(2) + ' | ' + keys.map(k => `${k.toUpperCase()}: $${last[k].toFixed(2)}`).join(' | ');
          });
      }

      fetchCosts();
      setInterval(fetchCosts, 5000);
      document.getElementById('simulateBtn').addEventListener('click', ()=>fetch('/api/simulate', {method:'POST'}).then(_=>fetchCosts()));
    </script>
  </body>
</html>
'''

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
    return jsonify({'ok':True, 'date': new_date})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
