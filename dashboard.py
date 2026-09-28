import os, requests
from flask import Flask, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QuantTrade Terminal - XAUUSD Research Lab</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e14;color:#e6e6e6;font-family:'Inter',sans-serif}
.mono{font-family:'JetBrains Mono',monospace}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;border-bottom:1px solid #1f2a38;background:#0f151f}
.brand{font-weight:800;letter-spacing:2px;color:#d4af37}
.live{color:#00e676;font-size:12px}
.main{display:grid;grid-template-columns:220px 1fr 320px;gap:0;min-height:100vh}
.sidebar{background:#0f151f;border-right:1px solid #1f2a38;padding:16px}
.sidebar h4{font-size:11px;color:#6b7a90;letter-spacing:1.5px;margin:18px 0 8px}
.item{padding:10px 12px;margin:4px 0;border-radius:6px;cursor:pointer;font-size:13px;border:1px solid transparent}
.item.active{background:#1a2332;border-color:#d4af37;color:#d4af37}
.center{background:#121a27;padding:16px}
.price-box{display:flex;align-items:baseline;gap:16px;margin:10px 0 16px}
.price{font-size:42px;font-weight:800}
.change{color:#00e676;font-size:14px}
.chart{height:420px;background:#0a0e14;border:1px solid #1f2a38;border-radius:8px;position:relative;overflow:hidden}
.chart::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(0deg,transparent,transparent 39px,#1f2a38 40px),repeating-linear-gradient(90deg,transparent,transparent 79px,#1a2332 80px);opacity:0.3}
.candle{position:absolute;bottom:80px;width:4px;background:#d4af37;border-radius:2px}
.level{position:absolute;right:0;left:0;border-top:1px dashed;padding:2px 8px;font-size:11px;display:flex;justify-content:flex-end}
.r1{top:30%;border-color:#d4af37;color:#d4af37} .s1{top:55%;border-color:#ff4d4d;color:#ff4d4d}
.right{background:#0f151f;border-left:1px solid #1f2a38;padding:16px}
.card{background:#121a27;border:1px solid #1f2a38;border-radius:8px;padding:12px;margin-bottom:12px}
.card h5{font-size:11px;color:#d4af37;letter-spacing:1px;margin-bottom:8px}
.big-signal{font-size:28px;font-weight:800;color:#00e676}
.metric{display:flex;justify-content:space-between;font-size:12px;margin:6px 0}
.btn{width:100%;padding:12px;border:none;border-radius:6px;font-weight:700;cursor:pointer;margin:4px 0}
.btn-buy{background:#00c853;color:#fff} .btn-sell{background:#d50000;color:#fff}
.badge{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700}
.badge-gold{background:#d4af37;color:#000} .badge-green{background:#0a3d2a;color:#00e676}
.footer{display:flex;justify-content:space-between;padding:10px 20px;font-size:11px;color:#6b7a90;background:#0a0e14;border-top:1px solid #1f2a38}
@media(max-width:900px){.main{grid-template-columns:1fr} .sidebar,.right{border:none}}
</style>
</head><body>
<div class="topbar">
<div class="brand mono">QUANTRADE TERMINAL <span style="font-weight:400;color:#6b7a90"> / MARKETS / COMMODITIES / GOLD (XAUUSD)</span></div>
<div class="mono live">● LIVE • UTC <span id="utc"></span> | Latency: 22ms | RESEARCH MODE</div>
</div>
<div class="main">
<div class="sidebar mono">
<h4>INSTRUMENT</h4>
<div class="item active">XAUUSD • GOLD/USD</div>
<div class="item">XAGUSD • SILVER/USD</div>
<div class="item">DXY • US DOLLAR INDEX</div>
<div class="item">US10Y • TREASURY</div>
<h4>ANALYTICS</h4>
<div class="item">Overview</div>
<div class="item active">Technical Analysis</div>
<div class="item">Orderbook</div>
<div class="item">Backtest Lab</div>
<div class="item">Risk Metrics</div>
<div class="item">Model Registry</div>
<h4>STRATEGIES</h4>
<div class="item">SVM-RSI Ensemble <span style="color:#00e676">● ACTIVE</span></div>
<div class="item">LSTM Trend v2</div>
</div>
<div class="center">
<div style="display:flex;gap:10px;align-items:center"><span class="badge badge-gold">XAUUSD - GOLD / US DOLLAR</span><span class="badge" style="background:#1a2332">COMEX • SPOT</span></div>
<div class="price-box"><div class="price mono" id="price">$4,124.70</div><div class="change mono" id="chg">↗ +12.40 (+0.30%)</div></div>
<div class="mono" style="font-size:12px;color:#6b7a90;display:flex;gap:16px;margin-bottom:12px">
<span>Open <b style="color:#e6e6e6">4112.30</b></span><span>High <b style="color:#e6e6e6">4128.50</b></span><span>Low <b style="color:#e6e6e6">4108.20</b></span><span>Vol <b style="color:#e6e6e6">1.24M</b></span>
</div>
<div class="chart" id="chart">
<div class="level r1 mono">R1 4128.00 — Resistance</div>
<div class="level s1 mono">S1 4115.00 — Support</div>
</div>
<div class="card" style="margin-top:12px"><h5>RSI (14) — <span id="rsi">58.32</span> NEUTRAL - Momentum rising</h5><div class="mono" style="height:40px;background:linear-gradient(90deg,#ff4d4d 0%,#6b7a90 50%,#00e676 100%);opacity:0.2;border-radius:4px;position:relative"><div id="rsi-dot" style="position:absolute;top:0;bottom:0;width:2px;background:#fff;left:58%"></div></div></div>
</div>
<div class="right mono">
<div class="card"><h5>SIGNAL & INSIGHTS</h5>
<div style="background:#0a3d2a;padding:12px;border-radius:6px"><div class="big-signal">↗ BUY</div><div style="font-size:12px;color:#00e676">Confidence 72%</div></div>
<div class="metric"><span>Model:</span><span>SVM-RSI Ensemble</span></div>
<div class="metric"><span>Trigger:</span><span style="font-size:10px">RSI>50 + EMA50>EMA200</span></div>
<div class="metric"><span>Signal Strength:</span><span>HIGH 72%</span></div>
</div>
<div class="card"><h5>KEY LEVELS</h5>
<div class="metric"><span>Resistance 3</span><span>• 4145.00</span></div>
<div class="metric"><span>Resistance 2</span><span>• 4135.00</span></div>
<div class="metric"><span>Resistance 1</span><span>• 4128.00</span></div>
<div style="border-top:1px solid #1f2a38;margin:8px 0"></div>
<div class="metric"><span>Pivot</span><span>• 4120.45</span></div>
<div class="metric"><span style="color:#00e676">Support 1</span><span style="color:#00e676">• 4115.00</span></div>
<div class="metric"><span>Support 2</span><span>• 4105.00</span></div>
</div>
<div class="card"><h5>MARKET METRICS</h5>
<div class="metric"><span>DXY</span><span>102.45 -0.12%</span></div>
<div class="metric"><span>USD Yield 10Y</span><span>4.32%</span></div>
<div class="metric"><span>Volatility (ATR)</span><span>14.6</span></div>
<div class="metric"><span>Risk/Reward</span><span>1:2.3</span></div>
<div style="margin-top:10px"><button class="btn btn-buy" onclick="exec('BUY')">EXECUTE BUY</button><button class="btn btn-sell" onclick="exec('SELL')">EXECUTE SELL</button></div>
</div>
<div class="card"><h5>BACKTEST METRICS (60D)</h5>
<div style="display:flex;gap:6px"><span class="badge badge-green">Win Rate 62%</span><span class="badge badge-gold">Sharpe 1.87</span><span class="badge" style="background:#3d0a0a;color:#ff4d4d">Max DD -3.1%</span></div>
</div>
</div>
</div>
<div class="footer mono"><span>SYSTEM: Models loaded • 4 strategies active • Data: Live (Exchange Delay &lt;1s)</span><span>ORDERBOOK: Bid <span id="bid">4124.68</span> | Ask <span id="ask">4124.72</span> | Spread 0.04</span></div>
<script>
function updateUTC(){document.getElementById('utc').innerText=new Date().toUTCString().slice(17,25)}
setInterval(updateUTC,1000); updateUTC();
async function load(){try{let r=await fetch('/api/data'); let j=await r.json();
document.getElementById('price').innerText='$'+Number(j.gold).toLocaleString(); 
document.getElementById('bid').innerText=(j.gold-0.02).toFixed(2); 
document.getElementById('ask').innerText=(j.gold+0.02).toFixed(2);
document.getElementById('rsi').innerText=j.rsi;
}catch(e){}}
function exec(t){alert(t+' Order Routed to Simulation Engine\\nModel: SVM-RSI Ensemble\\nConfidence: 72%');}
function buildCandles(){let c=document.getElementById('chart'); c.innerHTML='<div class=\"level r1 mono\">R1 4128.00 — Resistance</div><div class=\"level s1 mono\">S1 4115.00 — Support</div>'; for(let i=0;i<80;i++){let el=document.createElement('div'); el.className='candle'; el.style.left=(i*1.2+5)+'%'; let h=20+Math.random()*120; el.style.height=h+'px'; el.style.bottom=80+Math.random()*100+'px'; el.style.opacity=0.6+Math.random()*0.4; c.appendChild(el);}}
buildCandles(); load(); setInterval(load,10000);
</script></body></html>
"""

def get_gold():
    try:
        r=requests.get('https://api.gold-api.com/price/XAU',timeout=8).json()
        return float(r['price'])
    except:
        return 4124.70

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/api/data')
def data():
    price=get_gold()
    return jsonify(gold=price, rsi=58.32, dxy=102.45)

if __name__=='__main__':
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port)
