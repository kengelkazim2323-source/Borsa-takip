import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import urllib.request
import re


# ==========================================
# 0. VERİ YÖNETİMİ
# ==========================================
PORTFOY_DOSYASI = "portfoy_kayitlari.json"
IPO_DOSYASI = "halka_arz_kayitlari.json"

def load_json(dosya_adi):
    if not os.path.exists(dosya_adi): return []
    try:
        with open(dosya_adi, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x.get('Hisse', '')) if isinstance(data, list) else []
    except: return []

def save_json(dosya_adi, data):
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_json(PORTFOY_DOSYASI)
if 'ipo_liste' not in st.session_state:
    st.session_state.ipo_liste = load_json(IPO_DOSYASI)

@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="1mo") # Grafik için 1 aylık veri çekiyoruz
        if hist.empty: return None
        
        # TEMETTÜ GÜNCELLEMESİ: Yıllık toplam yerine EN SON ödenen brüt rakamı alır.
        divs = tk.dividends
        if not divs.empty:
            divs.index = divs.index.tz_localize(None)
            # En son ödenen brüt temettü miktarı
            son_brut_temettu = divs.iloc[-1] 
            # %10 Stopaj düşülerek Midas tarzı NET rakama ulaşılır (Örn: 12 TL -> 10.8 TL)
            guncel_net_temettu = son_brut_temettu * 0.90 
            son_tarih = divs.index[-1].strftime('%d.%m.%Y')
        else: 
            guncel_net_temettu = 0.0
            son_tarih = "-"
            
        return {"hist": hist, "temettu": guncel_net_temettu, "tarih": son_tarih}
    except: return None

@st.cache_data(ttl=300)
def fetch_tefas_price(symbol):
    try:
        code = symbol.replace(".IS", "").upper()
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={code}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        m = re.search(r'Son Fiyat \(TL\).*?<span>([\d.,]+)</span>', html, re.DOTALL)
        if not m: m = re.search(r'top-list-right">([\d.,]+)</span>', html)
        if m:
            price_str = m.group(1).replace('.', '').replace(',', '.')
            return float(price_str)
    except: pass
    return None

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
        if rsi < 35 and last_price > ma20: return "🟢 GÜÇLÜ AL"
        elif rsi < 45: return "🟢 AL"
        elif rsi > 70: return "🔴 SAT"
        elif rsi > 60: return "🔴 ZAYIF SAT"
        else: return "🟡 TUT"
    except: return "---"

# ==========================================
# 1. TEMA VE CSS
# ==========================================
st.set_page_config(page_title="Borsa Takip", page_icon="📈", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

tema_isimleri = ["Galaksi (VIP)", "Siber Punk", "Matrix", "Altın Vuruş", "Zümrüt Yeşili", "Lav Akışı"]
with st.sidebar:
    st.header("🎨 Tema")
    tema = st.selectbox("Görünüm", tema_isimleri)

tema_renkleri = {
    "Galaksi (VIP)": {"bg": "#0B0E14", "text": "#E0E0E0", "box": "#161B22", "accent": "#00D4FF"},
    "Siber Punk": {"bg": "#0D0221", "text": "#FFFFFF", "box": "#190033", "accent": "#FF00FF"},
    "Matrix": {"bg": "#000000", "text": "#00FF41", "box": "#0D0208", "accent": "#00FF41"},
    "Altın Vuruş": {"bg": "#0F0F0F", "text": "#F5F5F5", "box": "#1A1A1A", "accent": "#D4AF37"},
    "Zümrüt Yeşili": {"bg": "#06120B", "text": "#E8F5E9", "box": "#0D2114", "accent": "#00E676"},
    "Lav Akışı": {"bg": "#1A0F0F", "text": "#F8F9FA", "box": "#2D1B1B", "accent": "#FF4D4D"}
}

t_sec = tema_renkleri.get(tema, tema_renkleri["Galaksi (VIP)"])

st.markdown(f"""
    <style>
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; }}
    [data-testid="stMetric"] {{ background: {t_sec['box']}; padding: 20px; border-radius: 12px; border: 1px solid {t_sec['accent']}; text-align: center; }}
    .kral-table {{ width: 100%; border-collapse: collapse; background: {t_sec['box']}22; border: 1px solid {t_sec['accent']}33; border-radius: 10px; overflow: hidden; }}
    .kral-table th {{ padding: 12px; text-align: left; background: {t_sec['accent']}22; color: {t_sec['accent']}; }}
    .kral-table td {{ padding: 12px; border-bottom: 1px solid {t_sec['accent']}11; color: {t_sec['text']}; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. ÜST BİLGİ
# ==========================================
st.markdown(f"<h2 style='text-align:center; color:{t_sec['accent']};'>🚀 Borsa Takip</h2>", unsafe_allow_html=True)

# ==========================================
# 3. VERİ HAZIRLAMA VE PERFORMANS HESABI
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ADEL.IS", "AGROT.IS", "AKBNK.IS", "AKSA.IS", "ALARK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRISA.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "FROTO.IS", "GARAN.IS", "GESAN.IS", "GUBRF.IS", "HALKB.IS", "HEKTS.IS", "ISCTR.IS", "ISGYO.IS", "ISMEN.IS", "ISYAT.IS", "KCHOL.IS", "KLKIM.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "MIATK.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PETKM.IS", "PGSUS.IS", "REEDR.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "SOKM.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS"])
FON_LIST = sorted(["TTE.IS", "AES.IS", "AFO.IS", "AYA.IS", "KPH.IS", "KPA.IS", "ZGD.IS", "ZRE.IS", "TAU.IS", "MAC.IS", "YZG.IS", "OPB.IS", "NNF.IS", "IDH.IS", "GSP.IS", "IHY.IS"])

full_data = []
history_dfs = [] # Aylık grafik için

for i, item in enumerate(st.session_state.portfoy):
    piyasa_durumu = item.get("Piyasa", "Türk Borsası")
    d = fetch_stock_data(item['Hisse'])
    
    if piyasa_durumu == "Yatırım Fonu":
        c = fetch_tefas_price(item['Hisse']) or item['Maliyet']
        sinyal = "VERİ YOK"; temettu = 0.0; tarih = "-"
    else:
        if d:
            c = d['hist']['Close'].iloc[-1]
            sinyal = get_signal(d['hist'])
            temettu = d['temettu']
            tarih = d['tarih']
            # Grafik verisi için hisse adetiyle çarpılmış fiyatları sakla
            temp_h = d['hist'][['Close']].copy()
            temp_h['TotalValue'] = temp_h['Close'] * int(item['Adet'])
            history_dfs.append(temp_h[['TotalValue']])
        else:
            c = item['Maliyet']; sinyal = "VERİ YOK"; temettu = 0.0; tarih = "-"

    adet_int = int(item['Adet'])
    full_data.append({
        "id": i, "Piyasa": piyasa_durumu, "Hisse": item['Hisse'], 
        "Sinyal": sinyal, "Adet": adet_int, "Maliyet": item['Maliyet'], 
        "Güncel": c, "K/Z": (c - item['Maliyet']) * adet_int, 
        "Değer": c * adet_int, "Temettu": temettu, 
        "NetTemettu": temettu * adet_int, "Tarih": tarih
    })

# ==========================================
# 4. TABLAR
# ==========================================
tab_tr, tab_fon, tab_div, tab_ipo = st.tabs(["🇹🇷 TÜRK BORSASI", "📊 YATIRIM FONLARI", "💰 TEMETTÜ GELİRİ", "🚀 HALKA ARZ TAKİP"])

with st.sidebar:
    st.divider()
    st.subheader("➕ Yeni Varlık")
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Yatırım Fonu"], horizontal=True)
    hisse_sec = st.selectbox("Hisse/Fon Seç", BIST_FULL if piyasa_sec=="Türk Borsası" else FON_LIST)
    adet_sec = st.number_input("Adet", min_value=0, step=1)
    maliyet_sec = st.number_input("Maliyet", min_value=0.0)
    if st.button("🚀 Portföye Ekle"):
        st.session_state.portfoy.append({"Piyasa": piyasa_sec, "Hisse": hisse_sec, "Adet": int(adet_sec), "Maliyet": float(maliyet_sec)})
        save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()

# --- TÜRK BORSASI ---
with tab_tr:
    df_bist = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Türk Borsası'])
    if not df_bist.empty:
        st.metric("PORTFÖY DEĞERİ", f"{tr_format(df_bist['Değer'].sum())} ₺")
        st.write("---")
        for _, r in df_bist.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**{r['Hisse']}** ({r['Sinyal']})")
            c2.write(f"{r['Adet']} Adet @ {tr_format(r['Maliyet'])} ₺")
            kz_color = "green" if r['K/Z'] >= 0 else "red"
            c3.markdown(f":{kz_color}[{tr_format(r['K/Z'])} ₺]")
            if c4.button("❌", key=f"del_tr_{r['id']}"):
                st.session_state.portfoy.pop(r['id']); save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()
        
        # PERFORMANS GRAFİĞİ (AYLIK)
        if history_dfs:
            st.divider()
            st.subheader("📈 Portföy Performansı (Son 30 Gün)")
            combined_hist = pd.concat(history_dfs, axis=1).sum(axis=1)
            fig = px.line(combined_hist, labels={'value': 'Toplam Değer (₺)', 'Date': 'Tarih'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=t_sec['text'], showlegend=False)
            fig.update_traces(line_color=t_sec['accent'])
            st.plotly_chart(fig, use_container_width=True)
    else: st.info("Hisse bulunamadı.")

# --- FONLAR ---
with tab_fon:
    df_fon = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Yatırım Fonu'])
    if not df_fon.empty:
        for _, r in df_fon.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**{r['Hisse']}**")
            c2.write(f"{r['Adet']} Adet")
            c3.write(f"Değer: {tr_format(r['Değer'])} ₺")
            if c4.button("❌", key=f"del_fon_{r['id']}"):
                st.session_state.portfoy.pop(r['id']); save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()

# --- TEMETTÜ ---
with tab_div:
    df_div = pd.DataFrame([x for x in full_data if x['Temettu'] > 0])
    if not df_div.empty:
        st.metric("TAHMİNİ NET NAKİT AKIŞI", f"{tr_format(df_div['NetTemettu'].sum())} ₺")
        table_html = "<table class='kral-table'><thead><tr><th>HİSSE</th><th>TARİH</th><th>ADET</th><th>NET HİSSE BAŞI</th><th>TOPLAM NET</th></tr></thead><tbody>"
        for _, r in df_div.iterrows():
            table_html += f"<tr><td>{r['Hisse']}</td><td>{r['Tarih']}</td><td>{r['Adet']}</td><td>{tr_format(r['Temettu'])} ₺</td><td><b>{tr_format(r['NetTemettu'])} ₺</b></td></tr>"
        st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)

# --- HALKA ARZ ---
with tab_ipo:
    with st.form("ipo_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        ipo_isim = ic1.text_input("Şirket Kodu")
        ipo_fiyat = ic2.number_input("Fiyat", min_value=0.0)
        ipo_adet = ic3.number_input("Lot", min_value=0, step=1)
        if st.form_submit_button("➕ Ekle"):
            st.session_state.ipo_liste.append({"Isim": ipo_isim.upper(), "Fiyat": ipo_fiyat, "Adet": int(ipo_adet)})
            save_json(IPO_DOSYASI, st.session_state.ipo_liste); st.rerun()

    if st.session_state.ipo_liste:
        for idx, ipo in enumerate(st.session_state.ipo_liste):
            # SİLME SEKMESİNİ SATIRA HİZALAMA
            col_exp, col_del = st.columns([0.9, 0.1])
            with col_exp:
                with st.expander(f"📈 {ipo['Isim']} ({ipo['Adet']} Lot)"):
                    p = ipo['Fiyat']
                    maliyet = ipo['Adet'] * p
                    t_html = "<table class='kral-table'><thead><tr><th>GÜN</th><th>FİYAT</th><th>KAR</th></tr></thead><tbody>"
                    for g in range(1, 11):
                        p *= 1.10
                        t_html += f"<tr><td>{g}. Tavan</td><td>{tr_format(p)} ₺</td><td>{tr_format((p*ipo['Adet'])-maliyet)} ₺</td></tr>"
                    st.markdown(t_html + "</tbody></table>", unsafe_allow_html=True)
            with col_del:
                st.write("") # Boşluk hizalama için
                if st.button("❌", key=f"del_ipo_{idx}"):
                    st.session_state.ipo_liste.pop(idx); save_json(IPO_DOSYASI, st.session_state.ipo_liste); st.rerun()

st.caption(f"🕒 Güncelleme: {datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')}")

