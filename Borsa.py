import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 0. VERİ YÖNETİMİ
# ==========================================
PORTFOY_DOSYASI = "portfoy_kayitlari.json"

def load_data():
    if not os.path.exists(PORTFOY_DOSYASI): return []
    try:
        with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []

def save_data(data):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="35d")
        if hist.empty: return None
        divs = tk.dividends
        if not divs.empty:
            divs.index = divs.index.tz_localize(None)
            son_1_yil = datetime.now() - timedelta(days=365)
            yillik_temettu = divs[divs.index >= son_1_yil].sum()
        else: yillik_temettu = 0.0
        return {"hist": hist, "temettu": yillik_temettu}
    except: return None

def tr_format(val):
    try:
        if val is None or pd.isna(val): return "0,00"
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

def get_signal(hist_data):
    try:
        if len(hist_data) < 20: return "VERİ YETERSİZ"
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        ma20 = hist_data['Close'].rolling(window=20).mean().iloc[-1]
        last_price = hist_data['Close'].iloc[-1]
        if rsi < 40 and last_price > ma20: return "🟢 AL"
        elif rsi > 70 or last_price < ma20: return "🔴 SAT"
        else: return "🟡 TUT"
    except: return "---"

# ==========================================
# 1. TEMA VE GÖRSEL AYARLAR
# ==========================================
st.set_page_config(page_title="KRAL BORSA", page_icon="📈", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

with st.sidebar:
    st.header("🎨 GÖRÜNÜM")
    tema = st.selectbox("Tema Seçimi", ["Premium Koyu", "Matrix", "Derin Okyanus"])

tema_renkleri = {
    "Premium Koyu": {"bg": "#121212", "text": "#ffffff", "box": "#1e1e1e", "accent": "#BB86FC"},
    "Matrix": {"bg": "#000000", "text": "#00FF41", "box": "#0D0208", "accent": "#00FF41"},
    "Derin Okyanus": {"bg": "#0f2027", "text": "#e0eaf5", "box": "#203a43", "accent": "#2bc0e4"}
}
t_sec = tema_renkleri[tema]

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@700&display=swap');
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, p, span, label {{ color: {t_sec['text']} !important; }}
    
    /* Input Kutuları Tema Uyumu */
    div[data-baseweb="select"], div[data-baseweb="input"], .stNumberInput input {{
        background-color: {t_sec['box']} !important;
        color: {t_sec['text']} !important;
        border: 1px solid {t_sec['accent']} !important;
        border-radius: 8px !important;
    }}
    
    /* Metrikler */
    .stMetric {{ background: {t_sec['box']}; padding: 15px; border-radius: 10px; border-left: 5px solid {t_sec['accent']}; margin-bottom: 20px; }}
    
    /* Kayan Yazı Hızlandırıldı (25s) */
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; padding: 15px 0; }}
    .ticker-content {{ display: flex; animation: ticker 25s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; }} .down {{ color: #ff1744; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. OVAL SAAT MODÜLÜ (TAM KÖŞE VE OVAL)
# ==========================================
clock_html = f"""
<div style="position: fixed; top: 0px; right: 0px; background: {t_sec['box']}; padding: 10px 20px; border-radius: 50px; box-shadow: -2px 2px 10px rgba(0,0,0,0.4); z-index: 99999; display: flex; align-items: center; gap: 15px; border: 2px solid {t_sec['accent']};"
    <div style="position: relative; width: 35px; height: 35px; border: 2px solid {t_sec['accent']}; border-radius: 50%;">
        <div id="hour-hand" style="position: absolute; bottom: 50%; left: 50%; width: 2px; height: 10px; background: {t_sec['text']}; transform-origin: bottom; transform: translateX(-50%);"></div>
        <div id="minute-hand" style="position: absolute; bottom: 50%; left: 50%; width: 2px; height: 14px; background: {t_sec['text']}; transform-origin: bottom; transform: translateX(-50%);"></div>
        <div id="second-hand" style="position: absolute; bottom: 50%; left: 50%; width: 1px; height: 16px; background: #ff1744; transform-origin: bottom; transform: translateX(-50%);"></div>
    </div>
    <div style="text-align: right;">
        <div id="digital-clock" style="font-size: 15px; font-weight: bold; font-family: 'JetBrains Mono', monospace; color: {t_sec['text']};"></div>
        <div id="date-display" style="font-size: 10px; color: {t_sec['text']}; opacity: 0.8;"></div>
    </div>
</div>
<script>
function updateClock() {{
    const now = new Date();
    const trTime = new Date(now.toLocaleString("en-US", {{timeZone: "Europe/Istanbul"}}));
    document.getElementById('digital-clock').innerText = trTime.toLocaleTimeString('tr-TR', {{hour12: false}});
    document.getElementById('date-display').innerText = trTime.toLocaleDateString('tr-TR', {{weekday:'short', day:'numeric', month:'short'}});
    const h = trTime.getHours() % 12; const m = trTime.getMinutes(); const s = trTime.getSeconds();
    document.getElementById('hour-hand').style.transform = `translateX(-50%) rotate(${{(h*30)+(m*0.5)}}deg)`;
    document.getElementById('minute-hand').style.transform = `translateX(-50%) rotate(${{(m*6)+(s*0.1)}}deg)`;
    document.getElementById('second-hand').style.transform = `translateX(-50%) rotate(${{s*6}}deg)`;
}}
setInterval(updateClock, 1000); updateClock();
</script>
"""
st.components.v1.html(clock_html, height=70)

# ==========================================
# 3. PİYASA BANDI
# ==========================================
st.markdown(f"<h2 style='text-align:center; color:{t_sec['accent']}; margin-top:-20px;'>📈 PORTFÖY YÖNETİMİ</h2>", unsafe_allow_html=True)
piyasa_izleme = {"BIST 100": "XU100.IS", "GRAM ALTIN": "GAU-TRY", "USD/TRY": "USDTRY=X", "BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD"}
ticker_content = '<div class="ticker-wrapper"><div class="ticker-content">'
for isim, sembol in piyasa_izleme.items():
    d = fetch_stock_data(sembol)
    if d:
        last = d['hist']['Close'].iloc[-1]; prev = d['hist']['Close'].iloc[-2]
        deg = ((last - prev) / prev) * 100
        ticker_content += f'<div style="text-align:center;"><div style="font-size:12px;">{isim}</div><div style="font-weight:bold;">{tr_format(last)}</div><div class="{"up" if deg>=0 else "down"}">{deg:+.2f}%</div></div>'
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. HİSSE EKLEME (FORM İLE DÜZENLENDİ)
# ==========================================
BIST_FULL = sorted(["AKBNK.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS", "SASA.IS", "SISE.IS", "THYAO.IS", "TUPRS.IS", "YKBNK.IS", "SAHOL.IS", "KOZAL.IS", "PGSUS.IS"]) # Örnek Liste

with st.expander("➕ PORTFÖYE HİSSE EKLE", expanded=False):
    with st.form("hisse_ekle_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        hisse_sec = f1.selectbox("Hisse", BIST_FULL)
        adet_sec = f2.number_input("Adet", min_value=0.01)
        maliyet_sec = f3.number_input("Maliyet", min_value=0.0)
        submit = st.form_submit_button("🚀 LİSTEYE EKLE", use_container_width=True)
        
        if submit:
            st.session_state.portfoy.append({"Hisse": hisse_sec, "Adet": adet_sec, "Maliyet": maliyet_sec})
            save_data(st.session_state.portfoy)
            st.toast(f"{hisse_sec} başarıyla eklendi!", icon="✅")
            st.rerun()

# ==========================================
# 5. LİSTELEME VE ANALİZ
# ==========================================
if st.session_state.portfoy:
    p_data = []; total_daily = 0
    for i, item in enumerate(st.session_state.portfoy):
        d = fetch_stock_data(item['Hisse'])
        if d:
            c = d['hist']['Close'].iloc[-1]; pc = d['hist']['Close'].iloc[-2]
            daily_tl = (c - pc) * item['Adet']; total_daily += daily_tl
            p_data.append({
                "id": i, "Hisse": item['Hisse'], "Sinyal": get_signal(d['hist']),
                "Adet": item['Adet'], "Güncel": c, "K/Z": (c - item['Maliyet']) * item['Adet'],
                "Değer": c * item['Adet'], "Temettu": d['temettu'] * item['Adet']
            })
    
    df = pd.DataFrame(p_data)
    t1, t2, t3 = st.tabs(["📊 LİSTE", "📈 GRAFİK", "💰 TEMETTÜ"])
    
    with t1:
        m1, m2, m3 = st.columns(3)
        m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺")
        m3.metric("GÜNLÜK FARK", f"{tr_format(total_daily)} ₺", delta=f"{total_daily:,.2f}")
        
        for idx, r in df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 0.5])
            c1.write(f"**{r['Hisse']}** | {r['Sinyal']}")
            c2.write(f"Değer: {tr_format(r['Değer'])} ₺")
            c3.write(f"K/Z: {tr_format(r['K/Z'])} ₺")
            if c4.button("❌", key=f"del_{idx}"):
                st.session_state.portfoy.pop(idx); save_data(st.session_state.portfoy); st.rerun()
            st.divider()

    with t2:
        st.plotly_chart(px.pie(df, values='Değer', names='Hisse', hole=0.4), use_container_width=True)
    
    with t3:
        st.success(f"### Yıllık Net Temettü: {tr_format(df['Temettu'].sum())} ₺")

    if st.button("🗑️ TÜMÜNÜ SİL"):
        st.session_state.portfoy = []; save_data([]); st.rerun()
else:
    st.info("Portföyün henüz boş, yukarıdan ekleme yapabilirsin.")




tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Yüklendi.")


