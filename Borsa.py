import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
import pytz
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh


# ==========================================
# 1. VERİ YÖNETİMİ
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

if 'portfoy' not in st.session_state: st.session_state.portfoy = load_data()

# ==========================================
# 2. TEMA VE CSS
# ==========================================
st.set_page_config(page_title="BORSA ASLANI", page_icon="🦁", layout="wide")
main_color = "#00ff41" 
bg_color = "#05070a"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: {bg_color}; }} 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] {{ font-family: 'JetBrains Mono', monospace; color: #e6edf3; }}
    .ticker-wrapper {{ width: 100%; overflow-x: auto; background: rgba(13, 17, 23, 0.98); border-bottom: 2px solid {main_color}; position: sticky; top: 0; z-index: 999; backdrop-filter: blur(10px); margin-bottom: 20px; }}
    .ticker-container {{ display: flex; padding: 10px 15px; gap: 30px; width: max-content; }}
    .up {{ color: {main_color}; }} .down {{ color: #ff3131; }}
    .stMetric {{ background: #0d1117; border: 1px solid #30363d; padding: 10px; border-radius: 8px; }}
    .signal-box {{ background: #0d1117; border-left: 4px solid {main_color}; padding: 12px; border-radius: 5px; margin-bottom: 8px; border: 1px solid #30363d; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. PİYASA AKIŞI (GÜÇLENDİRİLMİŞ)
# ==========================================
piyasa_izleme = {
    "GRAM ALTIN": "GAU-TRY", 
    "GÜMÜŞ TRY": "GAG-TRY", 
    "BIST 100": "XU100.IS", 
    "USD/TRY": "USDTRY=X", 
    "EUR/TRY": "EURTRY=X"
}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        # Hata payını düşürmek için önce fast_info, olmazsa history dene
        try:
            last = tk.fast_info['lastPrice']
            prev = tk.fast_info['regularMarketPreviousClose']
        except:
            hist = tk.history(period="2d")
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            
        degisim = ((last - prev) / prev) * 100
        color = "up" if degisim >= 0 else "down"
        ticker_content += f'<div style="text-align:center; border-right:1px solid #30363d; padding-right:20px;"><div style="font-size:10px; color:#8b949e">{isim}</div><div style="font-weight:bold;">{last:,.2f}</div><div class="{color}" style="font-size:11px;">{degisim:+.2f}%</div></div>'
    except: continue
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. VARLIK LİSTESİ (SADECE HİSSELER)
# ==========================================
# (Hisse listesi aynı, kodun kısalığı için burada özet geçiyorum, sen kendi kodundaki tam listeyi tutmaya devam et)
BIST_HİSSELERİ = ["THYAO.IS", "ASELS.IS", "EREGL.IS", "SISE.IS", "BIMAS.IS", "AKBNK.IS", "ISCTR.IS", "GARAN.IS"] 
VARLIK_LISTESI = ["GAU-TRY", "GAG-TRY", "USDTRY=X", "EURTRY=X"] + BIST_HİSSELERİ

# ==========================================
# 5. GİRİŞ PANELİ
# ==========================================
st.markdown(f"<h3 style='text-align: center; color:{main_color};'>🦁 BORSA ASLANI</h3>", unsafe_allow_html=True)

with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: s_varlik = st.selectbox("Varlık Seçin", VARLIK_LISTESI)
    with c2: s_adet = st.number_input("Adet (Tam Sayı)", min_value=0, step=1, value=0)
    with c3: s_maliyet = st.number_input("Maliyet (Tam Sayı)", min_value=0, step=1, value=0)
    
    if st.button("🚀 PORTFÖYE EKLE", use_container_width=True):
        if s_varlik and s_adet > 0:
            st.session_state.portfoy.append({"Hisse": s_varlik, "Adet": int(s_adet), "Maliyet": int(s_maliyet)})
            save_data(st.session_state.portfoy)
            st.rerun()

# ==========================================
# 6. TABLAR
# ==========================================
tab_p, tab_g, tab_s = st.tabs(["📊 PORTFÖY", "📈 ANALİZ", "🤖 SİNYAL"])

if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            # Buradaki veri çekme mantığı da yukarıdaki gibi güncellendi
            try: curr = tk.fast_info['lastPrice']
            except: curr = tk.history(period="1d")['Close'].iloc[-1]
            
            kz = (curr - float(item['Maliyet'])) * int(item['Adet'])
            
            p_data.append({
                "Varlık": item['Hisse'], "Adet": int(item['Adet']), "Maliyet": int(item['Maliyet']),
                "Güncel": round(curr, 2), "Değer": round(item['Adet'] * curr, 2), 
                "K/Z": round(kz, 2)
            })
        except: continue
    
    df = pd.DataFrame(p_data)
    with tab_p:
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Portföy boş.")

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | Veri motoru güçlendirildi.")
