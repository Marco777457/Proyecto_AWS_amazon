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
