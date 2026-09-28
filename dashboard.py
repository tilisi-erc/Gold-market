import os
from flask import Flask, render_template_string
import json, requests
from datetime import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TILISI BI GOLD MARKET</title>
<style>
body{background:#000;color:#FFD700;font-family:Arial;text-align:center;margin:0}
.header{background:linear-gradient(90deg,#FFD700,#000);padding:15px;font-size:22px;font-weight:bold;color:#000}
.card{background:#111;border:1px solid #FFD700;margin:10px;border-radius:10px;padding:15px}
.price{font-size:32px;color:#00FF00}
.btn{padding:12px 20px;margin:5px;border:none;border-radius:8px;font-weight:bold;font-size:16px}
.buy{background:#00C853;color:#fff}
.sell{background:#D50000;color:#fff}
.refresh{background:#2962FF;color:#fff}
</style>
</head>
<body>
<div class="header">TILISI BI GOLD MARKET</div>
<div class="card">
<div>LIVE GOLD</div>
<div class="price" id="gold">$--</div>
<div id="info">Loading...</div>
</div>
<div class="card">
<div id="sr">RESISTANCE / SUPPORT loading...</div>
</div>
<div>
<button class="btn buy" onclick="check('buy')">BUY CHECK</button>
<button class="btn sell" onclick="check('sell')">SELL CHECK</button>
<button class="btn refresh" onclick="load()">REFRESH LIVE</button>
</div>
<script>
async function load(){
 let r=await fetch('/api/data'); let j=await r.json();
 document.getElementById('gold').innerText='$'+j.gold;
 document.getElementById('info').innerText='DXY '+j.dxy+' | RSI '+j.rsi+' | '+j.time;
 document.getElementById('sr').innerText='RESISTANCE $'+j.resistance+' | SUPPORT $'+j.support;
 if(j.sound){let a=new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg'); a.play();}
}
function check(t){alert(t.toUpperCase()+' CHECK: Angalia levels!'); load();}
load(); setInterval(load,60000);
</script>
</body>
</html>
"""

def get_live():
 try:
  g=requests.get('https://api.gold-api.com/price/XAU',timeout=10).json()
  price=float(g['price'])
 except:
  price=4170.10
 return {"gold":price,"dxy":101.2,"rsi":25.4,"resistance":round(price+1,2),"support":4032,"time":datetime.now().strftime('%H:%M:%S'),"sound":False}

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/data')
def data(): return get_live()

if __name__=='__main__':
 port=int(os.environ.get('PORT',5000))
 app.run(host='0.0.0.0',port=port)
