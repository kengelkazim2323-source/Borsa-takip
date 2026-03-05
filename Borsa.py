import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from datetime import datetime

# ==========================================
# 1. SİSTEM AYARLARI & GÖRÜNÜMÜ SIFIRLAMA (HARD CSS)
# ==========================================
st.set_page_config(page_title="İMPARATOR v11", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Streamlit'in standart menülerini ve butonlarını gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    .stApp { margin-top: -60px; } /* Üst boşluğu kapat */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }

    /* ÜST CANLI PİYASA ŞERİDİ (MİNİMAL) */
    .mini-ticker-container {
        display: flex;
        justify-content: space-between;
        background: #161b22;
        padding: 5px 20px;
        border-bottom: 1px solid #30363d;
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 1000;
    }
    .mini-item { font-size: 11px; font-weight: 600; color: #8b949e; }
    .mini-price { color: #f0f6fc; margin-left: 5px; }
    .mini-up { color: #3fb950; }
    .mini-down { color: #f85149; }

    /* SAĞ ÜST SİSTEM DURUMU */
    .system-status {
        position: fixed;
        top: 8px; right: 20px;
        font-size: 10px;
        background: rgba(31, 111, 235, 0.1);
        color: #58a6ff;
        padding: 2px 8px;
        border-radius: 20px;
        border: 1px solid #1f6feb;
        z-index: 1001;
    }

    /* KART VE TABLO DÜZENLEMELERİ */
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 10px !important; border-radius: 8px !important; }
    div[data-testid="stExpander"] { border: none !important; background: transparent !important; }
    .signal-card { background: #1c2128; border-left: 3px solid #58a6ff; padding: 8px 15px; border-radius: 4px; margin-bottom: 5px; font-size: 13px; }
    
    /* Input alanlarını küçültme */
    .stTextInput input, .stSelectbox div { font-size: 13px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA FONKSİYONLARI ---
def load_data():
    res = st_javascript("localStorage.getItem('kral_v11_data');")
    return json.loads(res) if res and res != "null" else []

def save_data(data):
    st_javascript(f"localStorage.setItem('kral_v11_data', '{json.dumps(data)}');")

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. CANLI ÜST ŞERİT (PİYASA)
# ==========================================
piyasa = {"USD": "USDTRY=X", "ALTIN": "GC=F", "GÜMÜŞ": "SI=F", "BIST": "XU100.IS", "BTC": "BTC-USD", "ETH": "ETH-USD"}
usd_kur = 33.0

ticker_html = '<div class="mini-ticker-container">'
for isim, sembol in piyasa.items():
    try:
        t = yf.Ticker(sembol)
        f = t.fast_info['lastPrice']
        p = t.fast_info['regularMarketPreviousClose']
        d = ((f - p) / p) * 100
        if isim == "USD": usd_kur = f
        cls = "mini-up" if d >= 0 else "mini-down"
        sign = "+" if d >= 0 else ""
        ticker_html += f'<div class="mini-item">{isim}<span class="mini-price">{f:,.2f}</span> <span class="{cls}">{sign}{d:.2f}%</span></div>'
    except: continue
ticker_html += '</div>'

st.markdown(ticker_html, unsafe_allow_html=True)
st.markdown('<div class="system-status">● TERMINAL v11.0 STABLE</div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True) # Üst bar için boşluk

# ==========================================
# 3. ANA PANEL & GİRİŞ
# ==========================================
st.title("🏛️ İMPARATOR")

# Dev Liste Enjeksiyonu (Hafıza dostu filtreleme için)
BIST_LIST = ["THYAO.IS", "ASELS.IS", "EREGL.IS", "TUPRS.IS", "SASA.IS", "SISE.IS", "AKBNK.IS", "KCHOL.IS", "BIMAS.IS", "EKGYO.IS", "ASTOR.IS", "FROTO.IS", "PETKM.IS", "HALKB.IS", "YKBNK.IS"] # Örnek kısaltılmış, tüm liste v9.5'teki gibi eklenebilir.
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "BTC-USD", "SI=F", "GC=F"]
TUM_LISTE = sorted(list(set(BIST_LIST + GLOBAL_LIST)))

with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    secilen = c1.selectbox("Varlık", TUM_LISTE, label_visibility="collapsed")
    adet = c2.number_input("Adet", min_value=0.0, step=1.0, label_visibility="collapsed")
    maliyet = c3.number_input("Maliyet", min_value=0.0, format="%.2f", label_visibility="collapsed")
    if c4.button("🚀 EKLE", use_container_width=True):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet})
        save_data(st.session_state.portfoy)
        st.rerun()

# ==========================================
# 4. ANALİZ MERKEZİ
# ==========================================
t1, t2, t3 = st.tabs(["📊 PORTFÖY", "🎯 TEKNİK", "📰 HABER"])

if st.session_state.portfoy:
    data = []
    t_maliyet, t_deger = 0, 0
    for item in st.session_state.portfoy:
        try:
            h = yf.Ticker(item['Hisse'])
            f = h.fast_info['lastPrice']
            m_top = item['Adet'] * item['Maliyet']
            d_top = item['Adet'] * f
            data.append({"Varlık": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'], "Güncel": f, "Değer": d_top, "K/Z": d_top - m_top})
            t_maliyet += m_top; t_deger += d_top
        except: continue
    df = pd.DataFrame(data)

    with t1:
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Varlık", f"{t_deger:,.0f} TL")
        m2.metric("Net K/Z", f"{(t_deger-t_maliyet):,.0f} TL", f"%{((t_deger-t_maliyet)/t_maliyet*100):.2f}")
        m3.metric("Dolar Karşılığı", f"${(t_deger/usd_kur):,.0f}")
        st.dataframe(df, use_container_width=True, height=250)
        if st.button("🗑️ Terminali Sıfırla"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()

    with t2:
        st.caption("Teknik Sinyal Havuzu")
        for asset in df['Varlık'].unique():
            hist = yf.Ticker(asset).history(period="1mo")
            if len(hist) > 10:
                rsi = 100 - (100 / (1 + (hist['Close'].diff().where(lambda x: x>0, 0).mean() / hist['Close'].diff().where(lambda x: x<0, 0).abs().mean())))
                durum = "💎 FIRSAT" if rsi < 35 else "🔥 ŞİŞMİŞ" if rsi > 65 else "⚪ NÖTR"
                st.markdown(f'<div class="signal-card"><b>{asset}</b> | RSI: {rsi:.1f} | <b>{durum}</b></div>', unsafe_allow_html=True)

    with t3:
        try:
            news = yf.Ticker("XU100.IS").news[:5]
            for n in news:
                st.markdown(f"**[{n['publisher']}]** {n['title']}  \n[Oku]({n['link']})")
                st.divider()
        except: st.write("Haber akışı geçici olarak kapalı.")

else:
    st.info("Portföy boş. Yukarıdan varlık ekleyerek başlayın.")
