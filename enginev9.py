"""
TILISI LITE v7.1.4 - FINAL CLEAN PRODUCTION
Eldoret Edition - Works 100% on Pydroid3
3 Steps Integrated: DUAL CHECK + AUTO LOOP + SMART ALERT
"""

import requests, json, os, time
from datetime import datetime, timezone
from pathlib import Path

# ================= CONFIG =================
LOG_FILE = "tilisi_signals.log"
HISTORY_FILE = "tilisi_history.json"
EAT_OFFSET = 3 # EAT = UTC+3
LOOP_MINUTES = 15

# ================= MATH (NO LIBS) =================
def ema(prices, period):
    k = 2.0 / (period + 1)
    ev = prices[0]
    for p in prices[1:]:
        ev = p * k + ev * (1 - k)
    return ev

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 70
    rs = ag / al
    return 100 - (100 / (1 + rs))

def atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / period if trs else 10

def fetch_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code!= 200:
            print(f"Yahoo {symbol} -> {r.status_code}")
            return None
        j = r.json()
        res = j['chart']['result'][0]
        quote = res['indicators']['quote'][0]
        closes = [c for c in quote['close'] if c is not None]
        highs = [h for h in quote['high'] if h is not None]
        lows = [l for l in quote['low'] if l is not None]
        return closes, highs, lows
    except Exception as e:
        print(f"Fetch error {symbol}: {e}")
        return None

# ================= S/R DETECTOR =================
class SRDetector:
    def find_levels(self, highs, lows, current_price):
        swing_highs, swing_lows = [], []
        for i in range(2, len(highs)-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < lows[i-2] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])

        def cluster(levels):
            if not levels: return []
            levels = sorted(levels)
            cl = [levels[0]]
            for lv in levels[1:]:
                if abs(lv - cl[-1]) > 8:
                    cl.append(lv)
            return cl

        res_levels = sorted([h for h in cluster(swing_highs) if h > current_price])
        sup_levels = sorted([l for l in cluster(swing_lows) if l < current_price], reverse=True)

        nearest_res = res_levels[0] if res_levels else current_price + 20
        nearest_sup = sup_levels[0] if sup_levels else current_price - 20

        return {
            "nearest_res": float(nearest_res),
            "nearest_sup": float(nearest_sup),
            "dist_res": float(abs(nearest_res - current_price)),
            "dist_sup": float(abs(current_price - nearest_sup)),
            "strength_res": len([h for h in swing_highs if abs(h-nearest_res)<8]),
            "strength_sup": len([l for l in swing_lows if abs(l-nearest_sup)<8])
        }

# ================= ENGINE =================
class TilisiEngineLite:
    def __init__(self):
        self.sr = SRDetector()
        Path(LOG_FILE).touch(exist_ok=True)
        Path(HISTORY_FILE).touch(exist_ok=True)

    def analyze(self, symbol):
        data = fetch_yahoo(symbol)
        if not data: return None
        closes, highs, lows = data
        price = closes[-1]
        e20 = ema(closes, 20)
        e50 = ema(closes, 50)
        trend = "bullish" if price > e20 > e50 else "bearish" if price < e20 < e50 else "ranging"
        last5 = closes[-5:]
        struct = "HH_HL" if last5[-1]>last5[-2]>last5[-3] else "LH_LL" if last5[-1]<last5[-2]<last5[-3] else "ranging"
        return {
            "price": price,
            "trend": trend,
            "structure": struct,
            "rsi": rsi(closes, 14),
            "atr": atr(highs, lows, closes, 14),
            "sr": self.sr.find_levels(highs, lows, price)
        }

    def get_signal(self, gold, dxy, us10y, intent, hour):
        sr = gold['sr']
        g1 = 1 if dxy and dxy['trend']=="bearish" else -1 if dxy and dxy['trend']=="bullish" else 0
        votes = (1 if gold['trend']=="bullish" else -1 if gold['trend']=="bearish" else 0) + (1 if gold['structure']=="HH_HL" else -1 if gold['structure']=="LH_LL" else 0)
        g2 = 1 if votes>=1 else -1 if votes<=-1 else 0
        g3 = "ACTIVE" if 10<=hour<13 or 15<=hour<19 else "WAIT"
        g4 = 1 if 50<=gold['rsi']<=70 else -1 if 30<=gold['rsi']<=50 else 0
        g6_block = (intent=="BUY" and sr['dist_res']<3) or (intent=="SELL" and sr['dist_sup']<3)
        g7 = -1 if us10y and us10y['trend']=="bullish" else 1 if us10y and us10y['trend']=="bearish" else 0

        intent_score = 1 if intent=="BUY" else -1
        supporting = sum([1 for s in [g1,g2,g4,g7] if s==intent_score])
        if not g6_block: supporting+=1

        if g3=="WAIT": return "WAIT", supporting, g3, g6_block
        if g6_block: return "WAIT", supporting, g3, g6_block
        if g1!=0 and g1!=intent_score: return "WAIT", supporting, g3, g6_block
        if supporting>=4: return intent, supporting, g3, g6_block
        return "WAIT", supporting, g3, g6_block

    def run_once(self):
        print("\n=== TILISI LITE v7.1.4 FETCHING ===")
        gold = self.analyze("GC=F")
        dxy = self.analyze("DX-Y.NYB")
        us10y = self.analyze("^TNX")

        if not gold:
            print("Failed fetch Gold - check internet")
            return

        hour = (datetime.now(timezone.utc).hour + EAT_OFFSET) % 24
        ts = datetime.now(timezone.utc)
        ts_eat = ts.hour + EAT_OFFSET
        if ts_eat >= 24: ts_eat -= 24
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " EAT"

        # STEP 1: DUAL CHECK
        buy_sig, buy_sup, g3_b, block_b = self.get_signal(gold, dxy, us10y, "BUY", hour)
        sell_sig, sell_sup, g3_s, block_s = self.get_signal(gold, dxy, us10y, "SELL", hour)

        # Choose best
        if buy_sig == "BUY" and sell_sig == "SELL":
            final_signal = "BOTH" if buy_sup == sell_sup else ("BUY" if buy_sup > sell_sup else "SELL")
            final_sup = max(buy_sup, sell_sup)
        elif buy_sig == "BUY":
            final_signal = "BUY"
            final_sup = buy_sup
        elif sell_sig == "SELL":
            final_signal = "SELL"
            final_sup = sell_sup
        else:
            final_signal = "WAIT"
            final_sup = max(buy_sup, sell_sup)

        dxy_info = f"{dxy['trend']} {dxy['price']:.1f}" if dxy else "N/A"
        sr = gold['sr']

        log = f"[{time_str}] GOLD ${gold['price']:.2f} | FINAL:{final_signal} (BUY:{buy_sig} {buy_sup}/5 | SELL:{sell_sig} {sell_sup}/5) | DXY {dxy_info} | RSI {gold['rsi']:.1f} | ATR {gold['atr']:.1f}\n"
        log += f" S/R -> Res ${sr['nearest_res']:.0f} ({sr['dist_res']:.1f}$ away {sr['strength_res']}x) | Sup ${sr['nearest_sup']:.0f} ({sr['dist_sup']:.1f}$ away {sr['strength_sup']}x) | Session {hour}:00 {g3_b}\n"
        if final_signal == "BUY":
            log += f" Invalidation -> Close below ${int(sr['nearest_sup'])} | Target -> ${int(sr['nearest_res'])}\n"
        elif final_signal == "SELL":
            log += f" Invalidation -> Close above ${int(sr['nearest_res'])} | Target -> ${int(sr['nearest_sup'])}\n"
        else:
            log += f" Invalidation -> No trade - waiting for gates\n"
        log += "-"*90 + "\n"

        print(log)
        with open(LOG_FILE, "a") as f:
            f.write(log)

        # STEP 3: SMART ALERT
        if final_signal!= "WAIT":
            print("\a")
            print(f"🔔🔔🔔 ALERT {final_signal} GOLD ${gold['price']:.2f} 🔔🔔🔔")
        else:
            print("Silent - WAIT logged only")

        # Save history
        try:
            hist = []
            if os.path.getsize(HISTORY_FILE) > 2:
                with open(HISTORY_FILE, "r") as jf:
                    hist = json.load(jf)
            hist.append({"time": time_str, "price": gold['price'], "signal": final_signal, "buy": buy_sig, "sell": sell_sig})
            hist = hist[-500:]
            with open(HISTORY_FILE, "w") as jf:
                json.dump(hist, jf, indent=2)
        except:
            pass

# ================= RUNNER WITH LOOP =================
if __name__ == "__main__":
    engine = TilisiEngineLite()

    # STEP 2: AUTO LOOP 15 MIN
    print(f"TILISI v7.1.4 Started - Loop every {LOOP_MINUTES} min | EAT UTC+3")
    print("Gusa STOP kwa Pydroid ku-stop\n")

    while True:
        try:
            engine.run_once()
            print(f"Sleeping {LOOP_MINUTES} min... next run at EAT")
            time.sleep(LOOP_MINUTES * 60)
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"Loop error: {e} - retrying in 60s")
            time.sleep(60)