"""
VIGILA - AWS Dashboard demo (single-file Flask app)

This file provides a demo dashboard that satisfies the 3 conditions requested:
 1) Reduce & show EC2/storage spend (demo with dataset + simulated real-time updates)
 2) Show advanced AWS security hardening checklist & evidence fields
 3) Show scalability recommendations & simple UI controls to simulate scale actions

How to use:
 - Put this file at the root of your GitHub repository for Render deployment.
 - Add a requirements.txt with the packages listed at the bottom of this file.
 - Configure Render service (Web Service) with start command: `gunicorn app:app`
 - OPTIONAL: to connect to real AWS Cost Explorer, set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION
   and enable the COSTEXPLORER integration (see commented section at the bottom).

What this demo includes (single file for simplicity):
 - Flask web app with a dashboard (Bootstrap + simple charts using Chart.js CDN)
 - A simulated dataset (data/costs.csv) created on first run if missing
 - API endpoints:
    /api/costs      -> returns recent costs JSON
    /api/simulate   -> append a simulated new cost point (for demo 'real-time')
    /api/security   -> returns security-checklist status
 - Simple JS polling every 5s to show near real-time behavior for costs
 - Inline comments that explain how to replace simulation with real AWS Cost Explorer calls

NOTE: This is a developer/demo artifact. For production, separate files, templates, static folder, proper secret handling,
      IAM roles, HTTPS, WAF, and VPC protections should be applied.

"""

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

# Create a sample dataset if it doesn't exist
if not os.path.exists(COSTS_CSV):
    start = datetime.utcnow() - timedelta(days=30)
    rows = []
    base_ec2 = 120.0
    base_s3 = 30.0
    for i in range(31):
        d = (start + timedelta(days=i)).strftime('%Y-%m-%d')
        # simulate some seasonality and noise
        ec2 = round(base_ec2 * (1 + 0.05 * random.sin(i/3) if hasattr(random, 'sin') else base_ec2 * (1 + 0.05*random.random())), 2)
        # simpler pattern
        ec2 = round(120 + 10 * random.random(), 2)
        s3 = round(30 + 5 * random.random(), 2)
        rows.append([d, ec2, s3])
    with open(COSTS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'ec2_cost_usd', 's3_cost_usd'])
        writer.writerows(rows)

# --- Dashboard template (single file to avoid extra template files) ---
TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>VIGILA - AWS Cost & Security Dashboard (Demo)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
    <style>
      body { padding: 20px; }
      .card { margin-bottom: 16px; }
      pre { background: #f8f9fa; padding: 12px; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>VIGILA - Infra Dashboard (Demo)</h2>
        <small class="text-muted">Simulated data / demo UI to deploy on Render</small>
      </div>

      <div class="row">
        <div class="col-md-8">
          <div class="card">
            <div class="card-header">1) EC2 & Storage spend (near real-time demo)</div>
            <div class="card-body">
              <canvas id="costChart" height="120"></canvas>
              <div class="mt-3 d-flex justify-content-between">
                <div>
                  <button id="simulateBtn" class="btn btn-sm btn-outline-primary">Simulate new reading</button>
                </div>
                <div>
                  <strong>Latest totals:</strong>
                  <span id="latestTotals">Loading...</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">3) Scalability & Data flow recommendations (how to grow)</div>
            <div class="card-body">
              <ul>
                <li>Use S3 for raw video storage with lifecycle policies to move to S3-IA / Glacier for older footage.</li>
                <li>Use EC2 Auto Scaling Groups + Elastic Load Balancer for ingestion microservices.</li>
                <li>Offload processing (thumbnails, transcoding, ML inference) to AWS Batch, ECS/Fargate, or Lambda where possible.</li>
                <li>Use SQS + SNS for decoupling ingestion and processing pipelines.</li>
                <li>Use RDS/Aurora for metadata and DynamoDB for high-throughput lookups. Add read replicas.</li>
                <li>Consider using Kinesis Video Streams for real-time video ingestion at scale.</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card">
            <div class="card-header">2) Advanced security hardening (display + evidence fields)</div>
            <div class="card-body">
              <div id="securityChecklist"></div>
              <hr>
              <h6>Evidence / Notes</h6>
              <textarea id="evidence" class="form-control" rows="4" placeholder="Describe evidence, e.g., CloudTrail enabled, Config rules, MFA enforced..."></textarea>
              <button id="saveEvidence" class="btn btn-sm btn-success mt-2">Save notes (local demo)</button>
              <div id="evidenceSaved" class="text-success mt-2" style="display:none;">Notes saved (client-side demo)</div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">Quick security checklist</div>
            <div class="card-body">
              <ul>
                <li>Enable AWS Organizations + SCPs</li>
                <li>Use IAM roles (no long-lived keys), least-privilege policies</li>
                <li>Enable MFA for all privileged users</li>
                <li>Turn on CloudTrail (multi-region) & AWS Config</li>
                <li>Encrypt S3 at rest (SSE-KMS), enable S3 Block Public Access</li>
                <li>Use VPC endpoints for S3 & DynamoDB</li>
                <li>Enable GuardDuty, Inspector, and Macie for data protection</li>
                <li>Use KMS with proper key rotation and DMARC for logs</li>
              </ul>
            </div>
          </div>

        </div>
      </div>

      <footer class="mt-4 text-muted small">Demo app — replace simulation with AWS Cost Explorer calls for production.</footer>
    </div>

    <script>
      // helper to fetch and render chart
      var ctx = document.getElementById('costChart').getContext('2d');
      var chart;

      function fetchCosts() {
        fetch('/api/costs')
          .then(r => r.json())
          .then(data => {
            const labels = data.map(r => r.date);
            const ec2 = data.map(r => r.ec2);
            const s3 = data.map(r => r.s3);
            const totals = data.map((r, i) => parseFloat((r.ec2 + r.s3).toFixed(2)));

            if(!chart){
              chart = new Chart(ctx, {
                type: 'line',
                data: {
                  labels: labels,
                  datasets: [{ label: 'EC2 (USD)', data: ec2, fill:false }, { label: 'S3 (USD)', data: s3, fill:false }]
                },
                options: { responsive:true }
              });
            } else {
              chart.data.labels = labels;
              chart.data.datasets[0].data = ec2;
              chart.data.datasets[1].data = s3;
              chart.update();
            }

            const last = data[data.length-1];
            document.getElementById('latestTotals').innerText = `EC2: $${last.ec2} | S3: $${last.s3} | Total: $${(last.ec2+last.s3).toFixed(2)}`;
          })
      }

      // Polling every 5s for near real-time demo
      fetchCosts();
      setInterval(fetchCosts, 5000);

      document.getElementById('simulateBtn').addEventListener('click', function(){
        fetch('/api/simulate', {method:'POST'}).then(_=>fetchCosts());
      });

      // Security checklist UI fetch
      function renderSecurityChecklist(){
        fetch('/api/security').then(r=>r.json()).then(j=>{
          const container = document.getElementById('securityChecklist');
          container.innerHTML = '';
          j.checks.forEach(c => {
            const div = document.createElement('div');
            div.className = 'form-check';
            div.innerHTML = `<input class='form-check-input' type='checkbox' id='chk_${c.id}' ${c.ok? 'checked':''}><label class='form-check-label' for='chk_${c.id}'>${c.title}</label>`;
            container.appendChild(div);
          });
        })
      }
      renderSecurityChecklist();

      document.getElementById('saveEvidence').addEventListener('click', ()=>{
        const v = document.getElementById('evidence').value;
        localStorage.setItem('vigila_evidence', v);
        document.getElementById('evidenceSaved').style.display = 'block';
        setTimeout(()=>document.getElementById('evidenceSaved').style.display='none', 2500);
      });

      // load saved notes
      const saved = localStorage.getItem('vigila_evidence');
      if(saved) document.getElementById('evidence').value = saved;
    </script>
  </body>
</html>
'''

# --- Backend helpers ---

def read_costs_csv(limit=31):
    df = pd.read_csv(COSTS_CSV, parse_dates=['date'])
    df = df.sort_values('date')
    rows = []
    for _, r in df.tail(limit).iterrows():
        rows.append({'date': r['date'].strftime('%Y-%m-%d'), 'ec2': float(r['ec2_cost_usd']), 's3': float(r['s3_cost_usd'])})
    return rows

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/api/costs')
def api_costs():
    rows = read_costs_csv()
    return jsonify(rows)

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    # Simulate a new reading appended to CSV (demo of 'real-time')
    df = pd.read_csv(COSTS_CSV, parse_dates=['date'])
    last_date = df['date'].max()
    new_date = (pd.to_datetime(last_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    last_ec2 = float(df.iloc[-1]['ec2_cost_usd'])
    last_s3 = float(df.iloc[-1]['s3_cost_usd'])
    # small random variation
    new_ec2 = round(max(0.0, last_ec2 + random.uniform(-5, 8)), 2)
    new_s3 = round(max(0.0, last_s3 + random.uniform(-2, 3)), 2)
    with open(COSTS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([new_date, new_ec2, new_s3])
    return jsonify({'ok':True, 'date': new_date, 'ec2': new_ec2, 's3': new_s3})

@app.route('/api/security')
def api_security():
    checks = [
        {'id':1, 'title':'AWS Organizations + SCPs configured', 'ok':False},
        {'id':2, 'title':'IAM roles (no long-lived keys) and least-privilege', 'ok':True},
        {'id':3, 'title':'MFA enforced for privileged users', 'ok':True},
        {'id':4, 'title':'CloudTrail multi-region enabled', 'ok':False},
        {'id':5, 'title':'AWS Config rules enabled for S3 encryption', 'ok':True},
        {'id':6, 'title':'S3 Block Public Access enabled', 'ok':True},
        {'id':7, 'title':'GuardDuty and Inspector enabled', 'ok':False},
    ]
    return jsonify({'checks':checks})

# --- Optional: placeholder for connecting to real AWS Cost Explorer ---
# To enable, install boto3 and configure AWS credentials. Example (UNCOMMENT and adapt):
# import boto3
# def fetch_costs_from_aws(start_date, end_date):
#     client = boto3.client('ce', region_name=os.environ.get('AWS_DEFAULT_REGION','us-east-1'))
#     response = client.get_cost_and_usage(
#         TimePeriod={'Start': start_date, 'End': end_date},
#         Granularity='DAILY',
#         Metrics=['UnblendedCost'],
#         GroupBy=[{'Type':'DIMENSION','Key':'SERVICE'}]
#     )
#     # parse and return a structure similar to read_costs_csv()

# --- Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

"""
requirements.txt:
flask
pandas
gunicorn
# boto3  # optional if you want to hook Cost Explorer

Instructions to deploy to Render (summary):
1. Push this file and requirements.txt to GitHub.
2. On Render, create a new Web Service from your GitHub repo.
   - Build command: (leave empty) or `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Add environment variables for production (SECRET_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION).
4. For real-time costs, replace the simulation with calls to AWS Cost Explorer using Boto3 and a read-only IAM role with CostExplorerReadOnly access.

Security notes (production):
 - Use IAM instance profile or secret manager for credentials (never commit keys).
 - Enable HTTPS (Render provides TLS automatically for public services).
 - Restrict admin UI by authentication (OAuth / Cognito) and network rules.
 - Use CloudTrail, Config, GuardDuty, and KMS for encryption.

"""
