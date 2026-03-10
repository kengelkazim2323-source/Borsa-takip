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
if 'ipo_liste' not in st.session_state:
    st.session_state.ipo_liste = []

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

@st.cache_data(ttl=300)
def fetch_tefas_price(symbol):
    try:
        code = symbol.replace(".IS", "").upper()
        url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={code}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        m = re.search(r'Son Fiyat \(TL\).*?<span>([\d,]+)</span>', html, re.DOTALL)
        if not m:
            m = re.search(r'top-list-right">([\d,]+)</span>', html)
        if m:
            return float(m.group(1).replace(',', '.'))
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
# 1. 20 FARKLI TEMA SEÇENEĞİ
# ==========================================
st.set_page_config(page_title="Borsa Takip", page_icon="📈", layout="wide")
st_autorefresh(interval=1000, key="datarefresh")

with st.sidebar:
    st.header("🎨 Tema Galerisi")
    tema = st.selectbox("Görünüm Seç", [
        "Galaksi (VIP)", "Siber Punk", "Matrix", "Altın Vuruş", "Zümrüt Yeşili", 
        "Lav Akışı", "Okyanus Derinliği", "Kuzey Işıkları", "Buzul (Dark)", "Mor Ötesi",
        "Bakır Buharı", "Gece Yarısı", "Safir Gece", "Çöl Fırtınası", "Kızıl Elmas",
        "Premium Koyu", "Retro Kehribar", "Derin Orman", "Antrasit VIP", "Neon Gecesi"
    ])

tema_renkleri = {
    "Galaksi (VIP)": {"bg": "#0B0E14", "text": "#E0E0E0", "box": "#161B22", "accent": "#00D4FF"},
    "Siber Punk": {"bg": "#0D0221", "text": "#FFFFFF", "box": "#190033", "accent": "#FF00FF"},
    "Matrix": {"bg": "#000000", "text": "#00FF41", "box": "#0D0208", "accent": "#00FF41"},
    "Altın Vuruş": {"bg": "#0F0F0F", "text": "#F5F5F5", "box": "#1A1A1A", "accent": "#D4AF37"},
    "Zümrüt Yeşili": {"bg": "#06120B", "text": "#E8F5E9", "box": "#0D2114", "accent": "#00E676"},
    "Lav Akışı": {"bg": "#1A0F0F", "text": "#F8F9FA", "box": "#2D1B1B", "accent": "#FF4D4D"},
    "Okyanus Derinliği": {"bg": "#001B2E", "text": "#ADB5BD", "box": "#003554", "accent": "#24D1FF"},
    "Kuzey Işıkları": {"bg": "#0B101B", "text": "#E9ECEF", "box": "#1B263B", "accent": "#A5FFD6"},
    "Buzul (Dark)": {"bg": "#0D1117", "text": "#C9D1D9", "box": "#161B22", "accent": "#58A6FF"},
    "Mor Ötesi": {"bg": "#120D1D", "text": "#E0D7FF", "box": "#1E1631", "accent": "#9D4EDD"},
    "Bakır Buharı": {"bg": "#1B1510", "text": "#D4A373", "box": "#2C211A", "accent": "#E76F51"},
    "Gece Yarısı": {"bg": "#050505", "text": "#FFFFFF", "box": "#121212", "accent": "#F72585"},
    "Safir Gece": {"bg": "#03045E", "text": "#CAF0F8", "box": "#023E8A", "accent": "#00B4D8"},
    "Çöl Fırtınası": {"bg": "#1C1917", "text": "#F5F5F4", "box": "#292524", "accent": "#EAB308"},
    "Kızıl Elmas": {"bg": "#0F0202", "text": "#FFFFFF", "box": "#1F0505", "accent": "#D00000"},
    "Premium Koyu": {"bg": "#121212", "text": "#ffffff", "box": "#4c4c4c", "accent": "#BB86FC"},
    "Retro Kehribar": {"bg": "#0A0A0A", "text": "#FFB300", "box": "#1A1A1A", "accent": "#FF8F00"},
    "Derin Orman": {"bg": "#081C15", "text": "#D8F3DC", "box": "#1B4332", "accent": "#95D5B2"},
    "Antrasit VIP": {"bg": "#1B1B1B", "text": "#D1D1D1", "box": "#2D2D2D", "accent": "#E0E0E0"},
    "Neon Gecesi": {"bg": "#000814", "text": "#FFFFFF", "box": "#001D3D", "accent": "#FFC300"}
}

t_sec = tema_renkleri[tema]
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@700&display=swap');
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; font-family: 'Inter', sans-serif; }}
    [data-testid="stMetric"] {{ background: {t_sec['box']}; padding: 20px !important; border-radius: 12px !important; border: 1px solid {t_sec['accent']} !important; text-align: center; }}
    .kral-table {{ width: 100%; border-collapse: collapse; background: {t_sec['box']}22; margin-top: 10px; border: 1px solid {t_sec['accent']}33; }}
    .kral-table th {{ padding: 12px; text-align: left; background: {t_sec['accent']}22; color: {t_sec['accent']}; font-weight: 700; border-bottom: 2px solid {t_sec['accent']}44; }}
    .kral-table td {{ padding: 12px; border-bottom: 1px solid {t_sec['accent']}11; color: {t_sec['text']}; }}
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; padding: 15px 0; border: 1px solid {t_sec['accent']}44; }}
    .ticker-content {{ display: flex; animation: ticker 25s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; }} .down {{ color: #ff1744; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SAAT VE TARİH
# ==========================================
clock_html = f"""
<div style="position: fixed; top: 10px; right: 10px; background: {t_sec['box']}; padding: 10px 25px; border-radius: 15px; z-index: 99999; border: 1px solid {t_sec['accent']};">
    <div id="digital-clock" style="font-size: 20px; font-weight: bold; font-family: 'JetBrains Mono', monospace; color: {t_sec['accent']};"></div>
    <div id="date-display" style="font-size: 11px; color: {t_sec['text']}; opacity: 0.8;"></div>
</div>
<script>
function updateClock() {{
    const trTime = new Date(new Date().toLocaleString("en-US", {{timeZone: "Europe/Istanbul"}}));
    document.getElementById('digital-clock').innerText = trTime.toLocaleTimeString('tr-TR', {{hour12: false}});
    document.getElementById('date-display').innerText = trTime.toLocaleDateString('tr-TR', {{day: '2-digit', month: 'long', year: 'numeric'}}).toUpperCase();
}}
setInterval(updateClock, 1000); updateClock();
</script>
"""
st.components.v1.html(clock_html, height=80)

# ==========================================
# 3. CANLI PİYASA
# ==========================================
st.markdown(f"<h2 style='text-align:center; color:{t_sec['accent']};'>🚀 Borsa Takip</h2>", unsafe_allow_html=True)
piyasa_izleme = { "BIST 100": "XU100.IS", "ONS ALTIN": "GC=F", "ONS GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X", "BTC": "BTC-USD"}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-content">'
for isim, sembol in piyasa_izleme.items():
    d = fetch_stock_data(sembol)
    if d:
        last = d['hist']['Close'].iloc[-1]; prev = d['hist']['Close'].iloc[-2]
        deg = ((last - prev) / prev) * 100
        ticker_content += f'<div style="text-align:center;"><div>{isim}</div><div style="font-weight:bold;">{tr_format(last)}</div><div class="{"up" if deg>=0 else "down"}">{deg:+.2f}%</div></div>'
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. HİSSE LİSTELERİ
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ADEL.IS", "AGROT.IS", "AKBNK.IS", "AKSA.IS", "ALARK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRISA.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "FROTO.IS", "GARAN.IS", "GESan.IS", "GUBRF.IS", "HALKB.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KLKIM.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "MIATK.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PETKM.IS", "PGSUS.IS", "REEDR.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "SOKM.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS"])
FON_LIST = sorted(["TTE.IS", "AES.IS", "AFO.IS", "AYA.IS", "KPH.IS", "KPA.IS", "ZGD.IS", "ZRE.IS", "TAU.IS", "MAC.IS", "YZG.IS", "OPB.IS", "NNF.IS", "IDH.IS", "GSP.IS", "IHY.IS"])

with st.expander("➕ PORTFÖYE VARLIK EKLE"):
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Yatırım Fonu"], horizontal=True)
    with st.form("hisse_ekle_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        if piyasa_sec == "Türk Borsası": hisse_sec = f1.selectbox("Hisse Seç", BIST_FULL)
        else:
            hisse_sec = f1.selectbox("Fon Seç", FON_LIST + ["DİĞER"])
            if hisse_sec == "DİĞER": hisse_sec = f1.text_input("Fon Kodu (Örn: IPJ.IS)").upper()
        adet_sec = f2.number_input("Adet", min_value=0.0, step=1.0, format="%.4f")
        maliyet_sec = f3.number_input("Maliyet", min_value=0.0, step=0.01, format="%.4f")
        if st.form_submit_button("🚀 EKLE"):
            if hisse_sec and adet_sec > 0:
                st.session_state.portfoy.append({"Piyasa": piyasa_sec, "Hisse": hisse_sec, "Adet": float(adet_sec), "Maliyet": float(maliyet_sec)})
                save_data(st.session_state.portfoy); st.rerun()

# ==========================================
# 5. TABLO VE SEKME YÖNETİMİ
# ==========================================
tab_tr, tab_fon, tab_div, tab_ipo = st.tabs(["🇹🇷 TÜRK BORSASI", "📊 YATIRIM FONLARI", "💰 TEMETTÜ GELİRİ", "🚀 YENİ HALKA ARZLAR"])

full_data = []
for i, item in enumerate(st.session_state.portfoy):
    piyasa_durumu = item.get("Piyasa", "Türk Borsası")
    
    # Her iki tür için de önce Yahoo Finance deniyoruz (Teknik analiz için geçmiş veri lazım)
    d = fetch_stock_data(item['Hisse'])
    
    if piyasa_durumu == "Yatırım Fonu":
        # Canlı Fiyatı TEFAS'tan çek (Daha güncel)
        canli_fon_fiyati = fetch_tefas_price(item['Hisse'])
        if canli_fon_fiyati:
            c = canli_fon_fiyati
            # Eğer Yahoo'da veri varsa sinyali oradan al
            sinyal = get_signal(d['hist']) if d else "VERİ YOK"
            pc = d['hist']['Close'].iloc[-2] if d else c
            temettu = 0.0
        else:
            c = item['Maliyet']; pc = c; sinyal = "VERİ YOK"; temettu = 0.0
    else:
        # Hisse senedi verileri
        if d:
            c = d['hist']['Close'].iloc[-1]; pc = d['hist']['Close'].iloc[-2]
            sinyal = get_signal(d['hist']); temettu = d['temettu']
        else:
            c = item['Maliyet']; pc = c; sinyal = "VERİ YOK"; temettu = 0.0

    full_data.append({
        "id": i, "Piyasa": piyasa_durumu, "Hisse": item['Hisse'], 
        "Sinyal": sinyal, "Adet": item['Adet'], "Maliyet": item['Maliyet'], 
        "Güncel": c, "K/Z": (c - item['Maliyet']) * item['Adet'], 
        "Değer": c * item['Adet'], "Temettu": temettu, 
        "NetTemettu": temettu * item['Adet'], "DailyDiff": (c - pc) * item['Adet']
    })

def portfoy_goster(piyasa_turu, tab_container, data_list):
    with tab_container:
        df = pd.DataFrame([x for x in data_list if x['Piyasa'] == piyasa_turu])
        if df.empty: st.info(f"{piyasa_turu} için henüz varlık yok."); return
        df = df.sort_values(by="Hisse")

        m1, m2, m3 = st.columns(3)
        m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺")
        m3.metric("GÜNLÜK FARK", f"{tr_format(df['DailyDiff'].sum())} ₺")

        table_html = "<table class='kral-table'><thead><tr><th>VARLIK</th><th>SİNYAL</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr></thead><tbody>"
        for _, r in df.iterrows():
            kz_color = "#00e676" if r['K/Z'] >= 0 else "#ff1744"
            table_html += f"<tr><td><b>{r['Hisse']}</b></td><td>{r['Sinyal']}</td><td>{r['Adet']}</td><td>{tr_format(r['Maliyet'])} ₺</td><td>{tr_format(r['Güncel'])} ₺</td><td style='color:{kz_color}; font-weight:bold;'>{tr_format(r['K/Z'])} ₺</td><td><b>{tr_format(r['Değer'])} ₺</b></td></tr>"
        st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)

        with st.expander("🛠️ VARLIK YÖNETİMİ"):
            for idx, r in df.iterrows():
                c1, c2, c3, c4 = st.columns([1.5, 2, 2, 1])
                c1.markdown(f"<div style='margin-top:25px;'><b>{r['Hisse']}</b></div>", unsafe_allow_html=True)
                y_adet = c2.number_input("Adet", value=float(r['Adet']), key=f"a_{r['id']}")
                y_maliyet = c3.number_input("Maliyet", value=float(r['Maliyet']), key=f"m_{r['id']}")
                c4.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                bc = c4.columns(2)
                if bc[0].button("💾", key=f"s_{r['id']}"):
                    st.session_state.portfoy[r['id']]['Adet'], st.session_state.portfoy[r['id']]['Maliyet'] = y_adet, y_maliyet
                    save_data(st.session_state.portfoy); st.rerun()
                if bc[1].button("❌", key=f"d_{r['id']}"):
                    st.session_state.portfoy.pop(r['id']); save_data(st.session_state.portfoy); st.rerun()

# Borsa Sekmesi ve Grafiği
portfoy_goster("Türk Borsası", tab_tr, full_data)
with tab_tr:
    df_chart_bist = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Türk Borsası' and x['Değer'] > 0])
    if not df_chart_bist.empty:
        st.divider()
        fig_bist = px.pie(df_chart_bist, values='Değer', names='Hisse', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel, hover_data=['Adet', 'K/Z', 'Güncel'])
        fig_bist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t_sec['text']))
        st.plotly_chart(fig_bist, use_container_width=True)

# Fon Sekmesi ve Grafiği
portfoy_goster("Yatırım Fonu", tab_fon, full_data)
with tab_fon:
    df_chart_fon = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Yatırım Fonu' and x['Değer'] > 0])
    if not df_chart_fon.empty:
        st.divider()
        fig_fon = px.pie(df_chart_fon, values='Değer', names='Hisse', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold, hover_data=['Adet', 'K/Z', 'Güncel'])
        fig_fon.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t_sec['text']))
        st.plotly_chart(fig_fon, use_container_width=True)

# Temettü Sekmesi
with tab_div:
    df_div = pd.DataFrame(full_data)
    if not df_div.empty and df_div['NetTemettu'].sum() > 0:
        st.metric("YILLIK TOPLAM TEMETTÜ", f"{tr_format(df_div['NetTemettu'].sum())} ₺")
        st.table(df_div[df_div['NetTemettu'] > 0][['Hisse', 'NetTemettu']])
    else: st.info("Temettü verisi bulunamadı.")

# Halka Arz Sekmesi
with tab_ipo:
    st.subheader("🚀 Halka Arz Takip & Tavan Simülasyonu")
    with st.form("ipo_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        ipo_isim = ic1.text_input("Arz Adı")
        ipo_fiyat = ic2.number_input("Fiyat", min_value=0.0)
        ipo_adet = ic3.number_input("Adet", min_value=0)
        if st.form_submit_button("➕ Ekle"):
            if ipo_isim:
                st.session_state.ipo_liste.append({"Isim": ipo_isim.upper(), "Fiyat": ipo_fiyat, "Adet": ipo_adet})
                st.rerun()

    for idx, ipo in enumerate(st.session_state.ipo_liste):
        with st.container():
            c1, c2, c3 = st.columns([2, 3, 1])
            maliyet = ipo['Adet'] * ipo['Fiyat']
            c1.markdown(f"### {ipo['Isim']}")
            c2.write(f"Maliyet: **{tr_format(maliyet)} ₺**")
            if c3.button("🗑️", key=f"rm_{idx}"):
                st.session_state.ipo_liste.pop(idx); st.rerun()
            with st.expander("📈 10 Günlük Tavan Serisi"):
                tavan_list = []
                p = ipo['Fiyat']
                for g in range(1, 11):
                    p *= 1.10
                    tavan_list.append({"Gün": g, "Fiyat": tr_format(p), "Kar": tr_format((p * ipo['Adet']) - maliyet)})
                st.table(pd.DataFrame(tavan_list))

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | TEFAS + Yahoo Verileri Aktif.")





