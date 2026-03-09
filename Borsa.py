import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh



# ==========================================
# 0. SAYI FORMATLAMA VE TEKNİK ANALİZ
# ==========================================
def tr_format(val):
    try:
        if val is None or pd.isna(val): return "0,00"
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def get_signal(data):
    """Basit RSI ve MA bazlı sinyal üretir."""
    try:
        if len(data) < 20: return "VERİ YETERSİZ"
        
        # RSI Hesaplama (14 günlük)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MA20 (20 Günlük Hareketli Ortalama)
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        last_price = data['Close'].iloc[-1]
        
        if rsi < 40 and last_price > ma20: return "🟢 AL"
        elif rsi > 70 or last_price < ma20: return "🔴 SAT"
        else: return "🟡 TUT"
    except:
        return "---"

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

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. TEMA VE SAAT
# ==========================================
st.set_page_config(page_title="BORSA TAKİP", page_icon="📈", layout="wide")
st_autorefresh(interval=500, key="datarefresh")

main_color = "#1a73e8"
tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #ffffff; }} 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] {{ font-family: 'JetBrains Mono', monospace; color: #202124; }}
    .top-right-clock {{ 
        position: fixed; top: 0px; right: 0px; color: #ffffff; font-weight: bold; font-size: 9px; 
        z-index: 9999; padding: 12px 20px; background: #202124;
        border-bottom-left-radius: 12px; box-shadow: -2px 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid {main_color};
    }}
    .ticker-wrapper {{ width: 100%; overflow-x: auto; background: #f1f3f4; border-bottom: 1px solid #dadce0; margin-bottom: 25px; }}
    .ticker-container {{ display: flex; padding: 12px; gap: 40px; width: max-content; }}
    .up {{ color: #137333; font-weight: 700; }} .down {{ color: #d93025; font-weight: 700; }}
    </style>
    <div class="top-right-clock">🕒 {tr_saati}</div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CANLI PİYASA BANDI
# ==========================================
piyasa_izleme = {"BIST 100": "XU100.IS", "GRAM ALTIN": "GAU-TRY", "ONS ALTIN": "GC=F", "ONS GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X"}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        hist = tk.history(period="2d")
        if not hist.empty:
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            degisim = ((last - prev) / prev) * 100
            color = "up" if degisim >= 0 else "down"
            ticker_content += f'<div style="text-align:center;"><div style="font-size:11px; color:#5f6368">{isim}</div><div style="font-size:15px; font-weight:bold;">{tr_format(last)}</div><div class="{color}" style="font-size:11px;">{degisim:+.2f}%</div></div>'
    except: continue
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. HİSSE EKLEME
# ==========================================
# Hisselerinizi buradaki listeye ekleyebilirsiniz (Tüm BİST kodlarını içeren liste kullanılabilir)
BIST_FULL = sorted(["AKBNK.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS", "SASA.IS", "SISE.IS", "THYAO.IS", "TUPRS.IS"]) 

st.markdown(f"<h2 style='text-align:center; color:{main_color}; margin-top:-20px;'>📈 BORSA TAKİP</h2>", unsafe_allow_html=True)

with st.container():
    col_v, col_a, col_m = st.columns([2, 1, 1])
    with col_v: s_varlik = st.selectbox("Hisse Seç", BIST_FULL)
    with col_a: s_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    with col_m: s_maliyet = st.number_input("Maliyet (₺)", min_value=0.0, format="%.2f")
    
    if st.button("🚀 PORTFÖYE EKLE", use_container_width=True):
        if s_varlik and s_adet > 0:
            st.session_state.portfoy.append({"Hisse": s_varlik, "Adet": s_adet, "Maliyet": s_maliyet})
            save_data(st.session_state.portfoy)
            st.rerun()

# ==========================================
# 5. VERİ ANALİZİ VE SİNYALLER
# ==========================================
if st.session_state.portfoy:
    p_data = []
    total_daily_gain = 0
    
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            hist = tk.history(period="30d") # Sinyal için en az 30 günlük veri çekiyoruz
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                daily_pct = ((curr - prev_close) / prev_close) * 100
                daily_tl = (curr - prev_close) * float(item['Adet'])
                
                total_daily_gain += daily_tl
                val = float(item['Adet']) * curr
                kz = (curr - float(item['Maliyet'])) * float(item['Adet'])
                
                # Teknik Sinyal Al
                signal = get_signal(hist)
                
                # Temettü
                info = tk.info
                d_rate = info.get('dividendRate', 0) or (curr * info.get('dividendYield', 0))
                
                p_data.append({
                    "Varlık": item['Hisse'], "Sinyal": signal, "Adet": item['Adet'],
                    "Güncel": curr, "Günlük (%)": daily_pct, "Günlük Fark (₺)": daily_tl,
                    "Değer": val, "K/Z": kz, "Yıllık Temettü": d_rate * float(item['Adet'])
                })
        except: continue

    df = pd.DataFrame(p_data)
    tab1, tab2, tab3 = st.tabs(["📊 PORTFÖYÜM", "📈 DAĞILIM", "💰 TEMETTÜ"])

    with tab1:
        m1, m2, m3 = st.columns(3)
        m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺")
        m3.metric("GÜNLÜK K/Z", f"{tr_format(total_daily_gain)} ₺", delta=f"{total_daily_gain:,.2f}")
        
        df_disp = df.copy()
        df_disp["Günlük (%)"] = df_disp["Günlük (%)"].apply(lambda x: f"%{x:+.2f}")
        for c in ["Güncel", "Değer", "K/Z", "Günlük Fark (₺)"]:
            df_disp[c] = df_disp[c].apply(tr_format)
            
        st.dataframe(df_disp[["Varlık", "Sinyal", "Adet", "Güncel", "Günlük (%)", "Günlük Fark (₺)", "Değer", "K/Z"]], 
                     use_container_width=True, hide_index=True)

    with tab2:
        fig = px.pie(df, values='Değer', names='Varlık', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        top_div = df['Yıllık Temettü'].sum()
        st.success(f"### Yıllık Tahmini Temettü: {tr_format(top_div)} ₺")
        st.table(df[df['Yıllık Temettü'] > 0][["Varlık", "Yıllık Temettü"]].style.format({"Yıllık Temettü": "{:,.2f} ₺"}))

    if st.button("🗑️ TÜMÜNÜ TEMİZLE"):
        st.session_state.portfoy = []
        save_data([])
        st.rerun()
else:
    st.info("Portföy boş kral, ekleme yapmanı bekliyorum.")

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Yüklendi.")


