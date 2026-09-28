from flask import Flask, render_template_string, jsonify
import json, os
from pathlib import Path

app = Flask(__name__)

LOG_FILE = "tilisi_signals.log"
HISTORY_FILE = "tilisi_history.json"

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TILISI BI GOLD MARKET</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{--gold:#FFD700;--black:#0a0a0a;--green:#00E676;--blue:#2979FF;--red:#FF1744;}
body{margin:0;background:var(--black);color:#fff;font-family:Inter,sans-serif;}
.header{background:linear-gradient(90deg,#000,var(--gold));padding:16px;text-align:center;border-bottom:3px solid var(--gold);}
.header h1{margin:0;color:#000;font-weight:900;letter-spacing:2px;}
.header p{margin:2px;color:#111;font-weight:600;}
.card{background:#121212;border:1px solid #222;border-left:4px solid var(--gold);border-radius:12px;padding:14px;margin:12px;}
.price{font-size:36px;font-weight:900;color:var(--gold);}
.badge{padding:6px 14px;border-radius:20px;font-weight:800;display:inline-block;margin:4px;}
.buy{background:var(--green);color:#000;}.sell{background:var(--red);color:#fff;}.wait{background:#333;color:#aaa;}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:900;font-size:16px;margin:6px 0;cursor:pointer;}
.btn-green{background:var(--green);color:#000;}.btn-blue{background:var(--blue);color:#fff;}.btn-red{background:var(--red);color:#fff;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.kpi{background:#1a1a1a;padding:10px;border-radius:10px;text-align:center;}
.kpi small{color:#888;}.kpi b{color:var(--gold);font-size:18px;}
.log{font-family:monospace;font-size:12px;background:#000;padding:10px;border-radius:8px;max-height:250px;overflow:auto;white-space:pre-wrap;}
canvas{background:#111;border-radius:12px;padding:8px;}
</style>
</head>
<body>
<div class="header">
<h1>TILISI BI GOLD MARKET</h1>
<p>LIVE INTELLIGENCE • ELDORET • v7.1.4</p>
</div>

<div class="card">
<div class="grid">
<div><small>LIVE GOLD</small><div class="price" id="price">$--.--</div><div id="signal"></div></div>
<div class="kpi"><small>DXY</small><br><b id="dxy">--</b><br><small>RSI</small><br><b id="rsi">--</b></div>
</div>
<div class="grid" style="margin-top:10px">
<div class="kpi"><small>RESISTANCE</small><br><b id="res">--</b><br><small id="resd"></small></div>
<div class="kpi"><small>SUPPORT</small><br><b id="sup">--</b><br><small id="supd"></small></div>
</div>
</div>

<div class="card">
<canvas id="chart" height="180"></canvas>
</div>

<div class="card">
<div class="grid">
<button class="btn btn-green" onclick="setIntent('BUY')">BUY CHECK</button>
<button class="btn btn-red" onclick="setIntent('SELL')">SELL CHECK</button>
</div>
<button class="btn btn-blue" onclick="refresh()">↻ REFRESH LIVE</button>
</div>

<div class="card">
<h3 style="color:var(--gold);margin:0 0 8px">📜 SIGNAL LOG</h3>
<div class="log" id="log">Loading...</div>
</div>

<script>
let chart;
async function refresh(){
 let r = await fetch('/api/data'); let d = await r.json();
 document.getElementById('price').innerText = '$'+d.last.price.toFixed(2);
 document.getElementById('dxy').innerText = d.last.dxy || '--';
 document.getElementById('rsi').innerText = d.last.rsi || '--';
 document.getElementById('res').innerText = '$'+(d.last.res||0);
 document.getElementById('sup').innerText = '$'+(d.last.sup||0);
 document.getElementById('resd').innerText = (d.last.dist_res||0)+' away';
 document.getElementById('supd').innerText = (d.last.dist_sup||0)+' away';
 let s = d.last.signal; let col = s=='BUY'?'buy':s=='SELL'?'sell':'wait';
 document.getElementById('signal').innerHTML = `<span class="badge ${col}">${s} ${d.last.supporting||''}/5</span>`;
 document.getElementById('log').innerText = d.log.slice(-3000);

 let labels = d.history.map(h=>h.time.split(' ')[1]);
 let prices = d.history.map(h=>h.price);
 if(chart) chart.destroy();
 chart = new Chart(document.getElementById('chart'),{
  type:'line',
  data:{labels:labels,datasets:[{label:'GOLD',data:prices,borderColor:'#FFD700',backgroundColor:'rgba(255,215,0,0.1)',tension:0.4,fill:true}]},
  options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{grid:{color:'#222'}}}}
 });
}
function setIntent(i){fetch('/api/run?intent='+i).then(()=>setTimeout(refresh,2000));}
refresh(); setInterval(refresh,30000);
</script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/data')
def data():
    history = []
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE) as f: history = json.load(f)
        except: pass
    log = ""
    if Path(LOG_FILE).exists():
        with open(LOG_FILE) as f: log = f.read()
    last = history[-1] if history else {"price":4170.1,"signal":"WAIT","supporting":0,"res":4171,"sup":4032,"dist_res":0.6,"dist_sup":137,"dxy":"101.2","rsi":25.4}
    return jsonify({"history":history[-30:],"log":log,"last":last})

@app.route('/api/run')
def run_engine():
    from engine import TilisiEngineLite
    import flask
    intent = flask.request.args.get('intent','BUY')
    e = TilisiEngineLite()
    try:
        import threading
        threading.Thread(target=lambda: e.run_once()).start()
        return jsonify({"ok":True,"intent":intent})
    except Exception as ex:
        return jsonify({"ok":False,"error":str(ex)})

if __name__ == '__main__':
    print("TILISI BI GOLD MARKET http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)