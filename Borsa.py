import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime

# ==========================================
# 1. VERİ YÖNETİMİ & OTOMATİK YENİLEME
# ==========================================
PORTFOY_DOSYASI = "portfoy_verileri.json"

# Sayfa her 15 saniyede bir kendini yeniler
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=15000, key="terminal_refresh")

def load_data():
    if os.path.exists(PORTFOY_DOSYASI):
        try:
            with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_data(data):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. TEMA VE CSS TASARIMI (MODERN DARK)
# ==========================================
st.set_page_config(page_title="BORSA TERMİNALİ", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Global Tema */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { margin-top: -70px; background-color: #05070a; } 
    
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; color: #e6edf3; }

    /* ÜST PANEL (TICKER) */
    .ticker-wrapper { 
        width: 100%; overflow-x: auto; background: rgba(13, 17, 23, 0.95); 
        border-bottom: 1px solid #00ff41; position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
        backdrop-filter: blur(10px);
    }
    .ticker-container { display: flex; padding: 12px 20px; gap: 40px; width: max-content; }
    .ticker-card { display: flex; flex-direction: column; align-items: center; border-right: 1px solid #30363d; padding-right: 20px; }
    .t-pct { font-size: 15px; font-weight: 800; }
    .t-sym { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .t-price { font-size: 14px; font-weight: 600; color: #ffffff; }
    .up { color: #00ff41; text-shadow: 0 0 10px rgba(0,255,65,0.3); }
    .down { color: #ff3131; text-shadow: 0 0 10px rgba(255,49,49,0.3); }

    /* KART TASARIMLARI */
    .stMetric { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); }
    .signal-box { background: #0d1117; border-left: 4px solid #00ff41; padding: 15px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #30363d; }
    
    /* Sekme Renkleri */
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #00ff41 !important; border-bottom-color: #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CANLI AKIŞ (15 SN'DE BİR GÜNCELLENİR)
# ==========================================
piyasa_izleme = {
    "BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "ONS ALTIN": "GC=F", 
    "BITCOIN": "BTC-USD", "GÜMÜŞ": "SI=F", "EREĞLİ": "EREGL.IS", "THY": "THYAO.IS", "NASDAQ": "^IXIC"
}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        fi = tk.fast_info
        fiyat = fi['lastPrice']
        degisim = ((fiyat - fi['regularMarketPreviousClose']) / fi['regularMarketPreviousClose']) * 100
        renk = "up" if degisim >= 0 else "down"
        isaret = "+" if degisim >= 0 else ""
        ticker_content += f'<div class="ticker-card"><span class="t-pct {renk}">{isaret}{degisim:.2f}%</span><span class="t-sym">{isim}</span><span class="t-price">{fiyat:,.2f}</span></div>'
    except: continue
ticker_content += '</div></div>'
st.markdown(ticker_content, unsafe_allow_html=True)
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# 4. PORTFÖY GİRİŞ
# ==========================================
st.markdown("<h1 style='text-align: center; color:#00ff41; text-shadow: 0 0 20px rgba(0,255,65,0.4);'>🏛️ TERMINAL_CORE_v14</h1>", unsafe_allow_html=True)

# Hisse listesi (Kısaltıldı, mantık aynı)
LISTE = sorted(["THYAO.IS", "EREGL.IS", "SASA.IS", "AKBNK.IS", "ASELS.IS", "SISE.IS", "TUPRS.IS", "KCHOL.IS", "AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"])

with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    with c1: s_hisse = st.selectbox("Varlık Seç", LISTE, label_visibility="collapsed")
    with c2: s_adet = st.number_input("Adet", min_value=0.0, step=1.0, label_visibility="collapsed")
    with c3: s_maliyet = st.number_input("Maliyet", min_value=0.0, label_visibility="collapsed")
    with c4: 
        if st.button("🚀 EKLE", use_container_width=True):
            st.session_state.portfoy.append({"Hisse": s_hisse, "Adet": s_adet, "Maliyet": s_maliyet})
            save_data(st.session_state.portfoy)
            st.rerun()

# ==========================================
# 5. ANALİZ VE GRAFİK
# ==========================================
tab_p, tab_g, tab_s, tab_t = st.tabs(["📊 PORTFÖY", "📈 K/Z GRAFİĞİ", "🤖 SİNYALLER", "💰 TEMETTÜ"])

if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            hist = tk.history(period="3mo")
            current = hist['Close'].iloc[-1]
            
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
            signal = "🟢 AL" if rsi < 35 else "🔴 SAT" if rsi > 70 else "⚪ TUT"
            
            kz = (current - item['Maliyet']) * item['Adet']
            p_data.append({
                "Hisse": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": current, "Değer": item['Adet'] * current, "K/Z": kz,
                "RSI": rsi, "Sinyal": signal, "Net_Temettü": (tk.info.get('dividendRate', 0) or 0) * 0.90 * item['Adet']
            })
        except: continue
    
    df = pd.DataFrame(p_data)

    with tab_p:
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("TOPLAM PORTFÖY", f"{df['Değer'].sum():,.2f} ₺")
        col_m2.metric("TOPLAM K/Z", f"{df['K/Z'].sum():,.2f} ₺", f"{((df['K/Z'].sum() / (df['Maliyet']*df['Adet']).sum())*100):.2f}%")
        
        # hide_index=True ile sol sekmeyi sildik
        st.dataframe(df[['Hisse', 'Adet', 'Maliyet', 'Güncel', 'Değer', 'K/Z']], 
                     use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Portföyü Temizle"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()

    with tab_g:
        st.subheader("Varlık Bazlı Kar / Zarar Dağılımı")
        if not df.empty:
            # Kar-Zarar Bar Grafiği
            chart_df = df[['Hisse', 'K/Z']].set_index('Hisse')
            st.bar_chart(chart_df, color="#00ff41" if df['K/Z'].sum() > 0 else "#ff3131")

    with tab_s:
        for _, row in df.iterrows():
            st.markdown(f'<div class="signal-box"><b>{row["Hisse"]}</b>: {row["Sinyal"]} | RSI: {row["RSI"]:.2f}</div>', unsafe_allow_html=True)

    with tab_t:
        st.metric("Yıllık Tahmini Net Temettü", f"{df['Net_Temettü'].sum():,.2f} ₺")
        st.dataframe(df[['Hisse', 'Adet', 'Net_Temettü']], use_container_width=True, hide_index=True)

else:
    st.info("Sistem Beklemede. Portföy verisi bekleniyor...")

# Alt Bilgi (Yenileme Zamanı)
st.caption(f"Son Güncelleme: {datetime.now().strftime('%H:%M:%S')} (15s periyot)")
