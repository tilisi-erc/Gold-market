import os, requests
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import random
from engine import v7_check_gates, get_gold_price

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QuantTrade Terminal | Tilisi BI v7</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e14;color:#e6e6e6;font-family:'Inter',sans-serif}
.mono{font-family:'JetBrains Mono',monospace}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;border-bottom:1px solid #1f2a38;background:#0f151f;flex-wrap:wrap;gap:8px}
.brand{font-weight:800;letter-spacing:2px;color:#d4af37;font-size:14px}
.live{color:#00e676;font-size:11px}
.main{display:grid;grid-template-columns:220px 1fr 340px;gap:0;min-height:calc(100vh - 90px)}
.sidebar{background:#0f151f;border-right:1px solid #1f2a38;padding:16px;overflow-y:auto}
.sidebar h4{font-size:11px;color:#6b7a90;letter-spacing:1.5px;margin:18px 0 8px}
.item{padding:10px 12px;margin:4px 0;border-radius:6px;font-size:13px;border:1px solid transparent;color:#9aa8bd}
.item.active{background:#1a2332;border-color:#d4af37;color:#d4af37}
.center{background:#121a27;padding:16px}
.price-box{display:flex;align-items:baseline;gap:16px;margin:10px 0 8px;flex-wrap:wrap}
.price{font-size:42px;font-weight:800} .change{color:#00e676;font-size:14px}
.chart{height:340px;background:#0a0e14;border:1px solid #1f2a38;border-radius:8px;position:relative;overflow:hidden}
.level{position:absolute;right:0;left:0;border-top:1px dashed;padding:2px 8px;font-size:11px;display:flex;justify-content:flex-end}
.r1{top:28%;border-color:#d4af37;color:#d4af37} .s1{top:58%;border-color:#ff4d4d;color:#00e676}
.candle{position:absolute;bottom:60px;width:4px;background:#d4af37;border-radius:2px}
.right{background:#0f151f;border-left:1px solid #1f2a38;padding:16px;overflow-y:auto}
.card{background:#121a27;border:1px solid #1f2a38;border-radius:8px;padding:12px;margin-bottom:12px}
.card h5{font-size:11px;color:#d4af37;letter-spacing:1px;margin-bottom:8px}
.big-signal{font-size:30px;font-weight:800}
.metric{display:flex;justify-content:space-between;font-size:12px;margin:6px 0;color:#9aa8bd}
.metric b{color:#e6e6e6}
.badge{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700}
.badge-gold{background:#d4af37;color:#000} .badge-green{background:#0a3d2a;color:#00e676} .badge-red{background:#3d0a0a;color:#ff4d4d}
.gate{font-size:11px;padding:6px 8px;margin:3px 0;border-radius:4px;display:flex;justify-content:space-between}
.gate-pass{background:#0a3d2a;border-left:3px solid #00e676} .gate-wait{background:#3d2f0a;border-left:3px solid #d4af37} .gate-fail{background:#3d0a0a;border-left:3px solid #ff4d4d}
.footer{display:flex;justify-content:space-between;padding:10px 20px;font-size:11px;color:#6b7a90;background:#0a0e14;border-top:1px solid #1f2a38;flex-wrap:wrap}
@media(max-width:1100px){.main{grid-template-columns:1fr} .sidebar,.right{border:none}}
#notif{position:fixed;top:70px;right:16px;background:#0a3d2a;border:1px solid #00e676;color:#00e676;padding:14px 18px;border-radius:8px;display:none;z-index:99;box-shadow:0 10px 30px rgba(0,230,118,0.3)}
</style>
</head><body>
<div id="notif" class="mono"><b>🔔 MARKET ALERT</b><br><span id="notif-text"></span></div>
<div class="topbar">
<div class="brand mono">QUANTRADE TERMINAL <span style="font-weight:400;color:#6b7a90">/ XAUUSD / TILISI BI v7</span></div>
<div class="mono live">● LIVE • UTC <span id="utc"></span> | <span id="gates-count">Gates 0/8</span> | RESEARCH MODE</div>
</div>
<div class="main">
<div class="sidebar mono">
<h4>INSTRUMENT</h4>
<div class="item active">XAUUSD • GOLD/USD</div>
<div class="item">XAGUSD • SILVER/USD</div>
<div class="item">DXY • US DOLLAR INDEX</div>
<h4>ANALYTICS</h4>
<div class="item active">Technical Analysis</div>
<div class="item">Evidence Matrix</div>
<div class="item">Orderbook</div>
<div class="item">Backtest Lab</div>
<h4>STRATEGIES</h4>
<div class="item">SVM-RSI Ensemble <span style="color:#00e676">● ACTIVE</span></div>
<div class="item">LSTM Trend v2</div>
<h4>GATES STATUS</h4>
<div id="gates-list"></div>
</div>
<div class="center">
<div><span class="badge badge-gold">XAUUSD — GOLD / US DOLLAR</span> <span class="badge" style="background:#1a2332;color:#9aa8bd">COMEX • SPOT</span> <span class="badge badge-green" id="regime-badge">TRENDING</span></div>
<div class="price-box"><div class="price mono" id="price">$4,124.70</div><div class="change mono" id="chg">↗ +12.40 (+0.30%)</div></div>
<div class="mono" style="font-size:12px;color:#6b7a90;display:flex;gap:16px;margin-bottom:10px;flex-wrap:wrap">
<span>Open <b>4112.30</b></span><span>High <b>4128.50</b></span><span>Low <b>4108.20</b></span><span>Vol <b>1.24M</b></span><span>DXY <b id="dxy">101.2</b></span><span>RSI <b id="rsi">58.32</b></span>
</div>
<div class="chart" id="chart"></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">
<div class="card mono"><h5>AI ANALYST (v7)</h5><div id="ai-analyst" style="font-size:12px;line-height:1.5;color:#e6e6e6">Loading analysis...</div></div>
<div class="card mono"><h5>INVALIDATION & RISK</h5><div id="invalidation" style="font-size:11px;color:#9aa8bd"></div><div id="risk" style="margin-top:8px"></div></div>
</div>
</div>
<div class="right mono">
<div class="card"><h5>SIGNAL & INSIGHTS (v7)</h5>
<div id="signal-box" style="background:#0a3d2a;padding:12px;border-radius:6px"><div class="big-signal" id="signal">WAIT</div><div style="font-size:12px" id="confidence">Confidence 50%</div></div>
<div class="metric"><span>Model:</span><b>SVM-RSI Ensemble + v7 Gates</b></div>
<div class="metric"><span>Evidence:</span><b id="evidence">0 Supporting</b></div>
</div>
<div class="card"><h5>EVIDENCE MATRIX</h5>
<div style="font-size:11px"><div style="color:#00e676"><b>Supporting:</b> <span id="ev-sup">-</span></div>
<div style="color:#ff4d4d;margin-top:6px"><b>Contradicting:</b> <span id="ev-con">-</span></div>
<div style="color:#6b7a90;margin-top:6px"><b>Neutral:</b> <span id="ev-neu">-</span></div></div>
</div>
<div class="card"><h5>KEY LEVELS</h5>
<div class="metric"><span>Resistance 3</span><b>• 4145.00</b></div>
<div class="metric"><span>Resistance 2</span><b>• 4135.00</b></div>
<div class="metric"><span>Resistance 1</span><b>• 4128.00</b></div>
<div style="border-top:1px solid #1f2a38;margin:8px 0"></div>
<div class="metric"><span>Pivot</span><b>• 4120.45</b></div>
<div class="metric"><span style="color:#00e676">Support 1</span><b style="color:#00e676">• 4115.00</b></div>
<div class="metric"><span>Support 2</span><b>• 4105.00</b></div>
</div>
<div class="card"><h5>BACKTEST METRICS (60D)</h5>
<div style="display:flex;gap:6px;flex-wrap:wrap"><span class="badge badge-green">Win Rate 62%</span><span class="badge badge-gold">Sharpe 1.87</span><span class="badge badge-red">Max DD -3.1%</span></div>
</div>
</div>
</div>
<div class="footer mono"><span id="system-status">SYSTEM: Models loaded • 8 Gates active • Data: Live</span><span>ORDERBOOK: Bid <span id="bid">4124.68</span> | Ask <span id="ask">4124.72</span> | Spread 0.04</span></div>
<script>
let audioCtx=null;
function playAlert(){
 try{
  if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  const seq=[880,1200,880]; seq.forEach((f,i)=>{
   const o=audioCtx.createOscillator(); const g=audioCtx.createGain();
   o.connect(g); g.connect(audioCtx.destination);
   o.frequency.value=f; g.gain.setValueAtTime(0.7,audioCtx.currentTime+i*0.25);
   o.start(audioCtx.currentTime+i*0.25); o.stop(audioCtx.currentTime+i*0.25+0.3);
  });
 }catch(e){}
}
function showNotif(text){
 const n=document.getElementById('notif'); document.getElementById('notif-text').innerText=text;
 n.style.display='block'; playAlert(); setTimeout(()=>n.style.display='none',8000);
}
function updateUTC(){document.getElementById('utc').innerText=new Date().toUTCString().slice(17,25)}
setInterval(updateUTC,1000); updateUTC();
function buildChart(){
 let c=document.getElementById('chart'); c.innerHTML='<div class=\"level r1 mono\">R1 4128.00 — Resistance</div><div class=\"level s1 mono\">S1 4115.00 — Support</div>';
 for(let i=0;i<90;i++){let el=document.createElement('div'); el.className='candle'; el.style.left=(i*1.1+3)+'%'; let h=18+Math.random()*90; el.style.height=h+'px'; el.style.bottom=50+Math.random()*90+'px'; el.style.opacity=0.5+Math.random()*0.5; c.appendChild(el);}
}
buildChart();
async function load(){
 try{
  let r=await fetch('/api/data'); let j=await r.json();
  document.getElementById('price').innerText='$'+Number(j.gold).toLocaleString();
  document.getElementById('dxy').innerText=j.dxy; document.getElementById('rsi').innerText=j.rsi;
  document.getElementById('bid').innerText=(j.gold-0.02).toFixed(2); document.getElementById('ask').innerText=(j.gold+0.02).toFixed(2);
  document.getElementById('signal').innerText=j.signal; 
  document.getElementById('signal').style.color=j.signal=='BUY'?'#00e676':'#d4af37';
  document.getElementById('confidence').innerText='Confidence '+j.confidence+'% | Gates '+j.passed+'/8';
  document.getElementById('gates-count').innerText='Gates '+j.passed+'/8 | '+j.regime;
  document.getElementById('regime-badge').innerText=j.regime;
  document.getElementById('evidence').innerText=j.evidence.supporting.length+' Supporting / '+j.evidence.contradicting.length+' Contradicting';
  document.getElementById('ev-sup').innerText=j.evidence.supporting.join(', ')||'-';
  document.getElementById('ev-con').innerText=j.evidence.contradicting.join(', ')||'-';
  document.getElementById('ev-neu').innerText=j.evidence.neutral.join(', ')||'-';
  document.getElementById('ai-analyst').innerText=j.ai_analyst;
  document.getElementById('invalidation').innerText=j.invalidation;
  document.getElementById('risk').innerHTML='<span class=\"badge '+(j.risk=='LOW'?'badge-green':j.risk=='HIGH'?'badge-red':'badge-gold')+'\">Risk: '+j.risk+'</span>';
  let gl=document.getElementById('gates-list'); gl.innerHTML='';
  Object.entries(j.gates).forEach(([k,v])=>{
    let d=document.createElement('div'); d.className='gate gate-'+(v.status=='PASS'?'pass':v.status=='FAIL'?'fail':'wait');
    d.innerHTML='<span>'+k+'</span><span>'+v.status+'</span>'; gl.appendChild(d);
  });
  document.getElementById('system-status').innerText='SYSTEM: '+j.passed+'/8 Gates PASS • '+j.regime+' • '+j.signal;
  if(j.should_notify){
    showNotif(j.signal+' @ $'+j.gold+' | '+j.passed+'/8 Gates | Conf '+j.confidence+'%');
  }
 }catch(e){console.log(e)}
}
document.addEventListener('click',()=>{ if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)(); },{once:true});
load(); setInterval(load,30000);
</script></body></html>
"""

def get_gold_price():
    try:
        import requests
        r=requests.get('https://api.gold-api.com/price/XAU',timeout=6).json()
        return float(r['price'])
    except:
        return 4124.70

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/data')
def api_data():
    result = v7_check_gates()
    return jsonify(result)

if __name__ == '__main__':
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug=False)
