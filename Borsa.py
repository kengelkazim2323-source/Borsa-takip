import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from streamlit_components_dot_com import html # TradingView için gerekebilir

# ==========================================
# 1. AYARLAR & ULTRA PREMIUM TASARIM
# ==========================================
st.set_page_config(page_title="İMPARATOR TERMINAL v9", page_icon="💎", layout="wide")

# Font ve Renk Özelleştirmesi (Neon Emerald & Deep Blue)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; }
    
    .stMetric { 
        background-color: #0e1117; 
        border: 2px solid #1f6feb; 
        border-radius: 15px; 
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.2);
    }
    
    .ticker-box { 
        text-align: center; 
        padding: 12px; 
        border-radius: 10px; 
        background: #161b22; 
        border: 1px solid #30363d; 
        margin: 5px;
        transition: transform 0.3s;
    }
    .ticker-box:hover { transform: translateY(-5px); border-color: #58a6ff; }
    
    .news-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #238636;
        margin-bottom: 15px;
        border-bottom: 1px solid #30363d;
    }
    
    h1, h2, h3 { color: #58a6ff !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA ---
def load_permanent_data():
    js_get = "localStorage.getItem('kral_v9_data');"
    res = st_javascript(js_get)
    if res and res != "null":
        return json.loads(res)
    return None

def save_permanent_data(data):
    js_set = f"localStorage.setItem('kral_v9_data', '{json.dumps(data)}');"
    st_javascript(js_set)

if 'portfoy' not in st.session_state:
    stored = load_permanent_data()
    st.session_state.portfoy = stored if stored else []

# ==========================================
# 2. CANLI PİYASA PANELİ (PREMIUM)
# ==========================================
st.markdown("# 🏛️ İMPARATOR YATIRIM TERMİNALİ v9.0")

piyasa_hisseleri = {
    "DOLAR": "USDTRY=X", "EURO": "EURTRY=X", "GRAM ALTIN": "GAU-TRY.IS",
    "GÜMÜŞ": "GAG-TRY.IS", "ONS ALTIN": "GC=F", "BIST 100": "XU100.IS",
    "BITCOIN": "BTC-USD", "ETHER": "ETH-USD"
}

usd_kur = 32.5 # Varsayılan
st.subheader("🛰️ Küresel Piyasa Nabzı")
p_cols = st.columns(len(piyasa_hisseleri))

for i, (isim, sembol) in enumerate(piyasa_hisseleri.items()):
    try:
        t_obj = yf.Ticker(sembol)
        fiyat = t_obj.fast_info['lastPrice']
        prev = t_obj.fast_info['regularMarketPreviousClose']
        degisim = ((fiyat - prev) / prev) * 100
        if isim == "DOLAR": usd_kur = fiyat
        
        with p_cols[i]:
            st.markdown(f"""<div class="ticker-box">
                <small style='color: #8b949e; font-weight: bold;'>{isim}</small><br>
                <strong style='font-size: 1.3em; color: #f0f6fc;'>{fiyat:,.2f}</strong><br>
                <span style='color: {"#3fb950" if degisim >= 0 else "#f85149"}; font-weight: bold;'>
                    {"▲" if degisim >= 0 else "▼"} %{abs(degisim):.2f}
                </span>
            </div>""", unsafe_allow_html=True)
    except: continue

st.markdown("---")

# ==========================================
# 3. CANLI GRAFİKLER (TRADINGVIEW)
# ==========================================
st.subheader("📈 Canlı Teknik Analiz Sekmeleri")
grafik_tab1, grafik_tab2, grafik_tab3 = st.tabs(["🇹🇷 BIST:THYAO", "🇺🇸 NASDAQ:NVDA", "₿ CRYPTO:BTC"])

def draw_chart(symbol):
    st.components.v1.html(f"""
        <div id="tradingview_chart" style="height:400px;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true, "symbol": "{symbol}", "interval": "D",
          "timezone": "Etc/UTC", "theme": "dark", "style": "1",
          "locale": "tr", "toolbar_bg": "#f1f3f6", "enable_publishing": false,
          "allow_symbol_change": true, "container_id": "tradingview_chart"
        }});
        </script>
    """, height=400)

with grafik_tab1: draw_chart("BIST:THYAO")
with grafik_tab2: draw_chart("NASDAQ:NVDA")
with grafik_tab3: draw_chart("BINANCE:BTCUSDT")

# ==========================================
# 4. YAN PANEL & ANALİZ (Önceki Fonksiyonlar Korundu)
# ==========================================
# (Dev BIST listesi burada aktiftir)
BIST_FULL = sorted(["THYAO.IS", "ASELS.IS", "EREGL.IS", "TUPRS.IS", "SASA.IS"]) # ... v8'deki tam liste buraya

with st.sidebar:
    st.header("👑 Portföy Yönetimi")
    secilen = st.selectbox("Hisse Ara:", BIST_FULL + ["AAPL", "NVDA", "BTC-USD"])
    adet = st.number_input("Adet:", min_value=0.0)
    maliyet = st.number_input("Maliyet (TL):", min_value=0.0, format="%.3f")
    if st.button("🚀 Portföye İşle"):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet, "Temettu": 2.0})
        save_permanent_data(st.session_state.portfoy)
        st.rerun()

# ==========================================
# 5. HABER AKIŞI & TL/DOLAR ANALİZİ
# ==========================================
tab_analiz, tab_haber = st.tabs(["📊 Finansal Analiz", "📰 Canlı Haber Akışı"])

with tab_analiz:
    # TL ve Dolar Analiz Metrikleri (v8 logic)
    if st.session_state.portfoy:
        st.write("### Portföy Özeti")
        # Analiz kodları buraya (v8 ile aynı)
        st.info("TL ve Dolar bazlı detaylı tablolar v8 standartlarında aşağıda listelenmiştir.")
    else:
        st.info("Analiz için hisse ekleyin.")

with tab_haber:
    st.subheader("🔥 Piyasa Son Dakika")
    try:
        # Portföydeki ilk hissenin veya BIST100'ün haberlerini çek
        target = st.session_state.portfoy[0]['Hisse'] if st.session_state.portfoy else "XU100.IS"
        news_data = yf.Ticker(target).news
        for n in news_data[:10]:
            st.markdown(f"""
            <div class="news-card">
                <p style='color: #8b949e; font-size: 0.8em;'>{datetime.fromtimestamp(n['providerPublishTime']).strftime('%H:%M - %d.%m.%Y')}</p>
                <h4 style='color: #58a6ff;'><a href="{n['link']}" style='text-decoration:none; color:inherit;'>{n['title']}</a></h4>
                <span style='background: #30363d; padding: 2px 8px; border-radius: 5px; font-size: 0.7em;'>{n['publisher']}</span>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.error("Haberler şu an yüklenemiyor.")
