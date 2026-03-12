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
            return data if isinstance(data, list) else []
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
# 1. TEMA VE CSS
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
    .kral-table {{ width: 100%; border-collapse: collapse; background: {t_sec['box']}22; margin-top: 10px; border: 1px solid {t_sec['accent']}33; border-radius: 10px; overflow: hidden; }}
    .kral-table th {{ padding: 12px; text-align: left; background: {t_sec['accent']}22; color: {t_sec['accent']}; font-weight: 700; border-bottom: 2px solid {t_sec['accent']}44; }}
    .kral-table td {{ padding: 12px; border-bottom: 1px solid {t_sec['accent']}11; color: {t_sec['text']}; }}
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; padding: 15px 0; border: 1px solid {t_sec['accent']}44; }}
    .ticker-content {{ display: flex; animation: ticker 25s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; }} .down {{ color: #ff1744; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. ÜST BİLGİ VE PİYASA
# ==========================================
clock_html = f"""
<div style="position: fixed; top: 10px; right: 10px; background: {t_sec['box']}; padding: 10px 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); z-index: 99999; display: flex; flex-direction: column; align-items: flex-end; border: 1px solid {t_sec['accent']};">
    <div id="digital-clock" style="font-size: 20px; font-weight: bold; font-family: 'JetBrains Mono', monospace; color: {t_sec['accent']};"></div>
    <div id="date-display" style="font-size: 11px; font-weight: 600; color: {t_sec['text']}; opacity: 0.8; letter-spacing: 1px;"></div>
</div>
<script>
function updateClock() {{
    const trTime = new Date(new Date().toLocaleString("en-US", {{timeZone: "Europe/Istanbul"}}));
    document.getElementById('digital-clock').innerText = trTime.toLocaleTimeString('tr-TR', {{hour12: false}});
    document.getElementById('date-display').innerText = trTime.toLocaleDateString('tr-TR', {{day: '2-digit', month: 'long', year: 'numeric', weekday: 'long'}}).toUpperCase();
}}
setInterval(updateClock, 1000); updateClock();
</script>
"""
st.components.v1.html(clock_html, height=80)


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
# 3. VERİ HAZIRLAMA
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ADEL.IS", "AGROT.IS", "AKBNK.IS", "AKSA.IS", "ALARK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRISA.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "FROTO.IS", "GARAN.IS", "GESAN.IS", "GUBRF.IS", "HALKB.IS", "HEKTS.IS", "ISCTR.IS", "ISGYO.IS", "ISMEN.IS", "ISYAT.IS", "KCHOL.IS", "KLKIM.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "MIATK.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PETKM.IS", "PGSUS.IS", "REEDR.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "SOKM.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS"])
FON_LIST = sorted(["TTE.IS", "AES.IS", "AFO.IS", "AYA.IS", "KPH.IS", "KPA.IS", "ZGD.IS", "ZRE.IS", "TAU.IS", "MAC.IS", "YZG.IS", "OPB.IS", "NNF.IS", "IDH.IS", "GSP.IS", "IHY.IS"])

full_data = []
for i, item in enumerate(st.session_state.portfoy):
    piyasa_durumu = item.get("Piyasa", "Türk Borsası")
    d = fetch_stock_data(item['Hisse'])
    
    if piyasa_durumu == "Yatırım Fonu":
        canli_fon_fiyati = fetch_tefas_price(item['Hisse'])
        if canli_fon_fiyati:
            c = canli_fon_fiyati
            sinyal = get_signal(d['hist']) if d else "VERİ YOK"
            pc = d['hist']['Close'].iloc[-2] if d else c
        else:
            c = item['Maliyet']; pc = c; sinyal = "VERİ YOK"
        temettu = 0.0
    else:
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

# ==========================================
# 4. TABLAR VE İÇERİK
# ==========================================
tab_tr, tab_fon, tab_div, tab_ipo = st.tabs(["🇹🇷 TÜRK BORSASI", "📊 YATIRIM FONLARI", "💰 TEMETTÜ GELİRİ", "🚀 HALKA ARZ TAKİP"])

with st.sidebar:
    st.divider()
    st.subheader("➕ Yeni Varlık")
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Yatırım Fonu"], horizontal=True)
    if piyasa_sec == "Türk Borsası": hisse_sec = st.selectbox("Hisse Seç", BIST_FULL)
    else: hisse_sec = st.selectbox("Fon Seç", FON_LIST + ["DİĞER"])
    if hisse_sec == "DİĞER": hisse_sec = st.text_input("Fon Kodu").upper()
    adet_sec = st.number_input("Adet", min_value=0.0)
    maliyet_sec = st.number_input("Maliyet", min_value=0.0)
    if st.button("🚀 Portföye Ekle"):
        st.session_state.portfoy.append({"Piyasa": piyasa_sec, "Hisse": hisse_sec, "Adet": float(adet_sec), "Maliyet": float(maliyet_sec)})
        save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()

# --- YÖNETİM FONKSİYONU ---
def varlik_yonetimi_render(df_local):
    with st.expander("🛠️ VARLIK YÖNETİMİ"):
        for _, r in df_local.iterrows():
            c1, c2, c3, c4 = st.columns([1.5, 2, 2, 1])
            c1.markdown(f"<div style='margin-top:25px;'><b>{r['Hisse']}</b></div>", unsafe_allow_html=True)
            y_adet = c2.number_input("Adet", value=float(r['Adet']), key=f"a_{r['id']}")
            y_maliyet = c3.number_input("Maliyet", value=float(r['Maliyet']), key=f"m_{r['id']}")
            c4.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            bc = c4.columns(2)
            if bc[0].button("💾", key=f"s_{r['id']}"):
                st.session_state.portfoy[r['id']]['Adet'] = y_adet
                st.session_state.portfoy[r['id']]['Maliyet'] = y_maliyet
                save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()
            if bc[1].button("❌", key=f"d_{r['id']}"):
                st.session_state.portfoy.pop(r['id'])
                save_json(PORTFOY_DOSYASI, st.session_state.portfoy); st.rerun()

def render_kral_table(df_local):
    table_html = "<table class='kral-table'><thead><tr><th>VARLIK</th><th>SİNYAL</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr></thead><tbody>"
    for _, r in df_local.iterrows():
        kz_color = "#00e676" if r['K/Z'] >= 0 else "#ff1744"
        table_html += f"<tr><td><b>{r['Hisse']}</b></td><td>{r['Sinyal']}</td><td>{r['Adet']}</td><td>{tr_format(r['Maliyet'])} ₺</td><td>{tr_format(r['Güncel'])} ₺</td><td style='color:{kz_color}; font-weight:bold;'>{tr_format(r['K/Z'])} ₺</td><td><b>{tr_format(r['Değer'])} ₺</b></td></tr>"
    return table_html + "</tbody></table>"

# --- TÜRK BORSASI ---
with tab_tr:
    df_bist = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Türk Borsası'])
    if not df_bist.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("PORTFÖY DEĞERİ", f"{tr_format(df_bist['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z", f"{tr_format(df_bist['K/Z'].sum())} ₺")
        m3.metric("GÜNLÜK DEĞİŞİM", f"{tr_format(df_bist['DailyDiff'].sum())} ₺")
        st.markdown(render_kral_table(df_bist), unsafe_allow_html=True)
        varlik_yonetimi_render(df_bist)
        
        # Grafik
        df_chart = df_bist[df_bist['Değer'] > 0]
        if not df_chart.empty:
            st.divider()
            fig = px.pie(df_chart, values='Değer', names='Hisse', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t_sec['text']))
            st.plotly_chart(fig, use_container_width=True)
    else: st.info("Hisse senedi bulunamadı.")

# --- YATIRIM FONLARI ---
with tab_fon:
    df_fon = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Yatırım Fonu'])
    if not df_fon.empty:
        st.markdown(render_kral_table(df_fon), unsafe_allow_html=True)
        varlik_yonetimi_render(df_fon)
        
        # Grafik
        df_chart_f = df_fon[df_fon['Değer'] > 0]
        if not df_chart_f.empty:
            st.divider()
            fig_f = px.pie(df_chart_f, values='Değer', names='Hisse', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
            fig_f.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=t_sec['text']))
            st.plotly_chart(fig_f, use_container_width=True)
    else: st.info("Fon bulunamadı.")

# --- TEMETTÜ GELİRİ ---
with tab_div:
    st.markdown(f"### 💰 Yıllık Projeksiyon")
    df_div = pd.DataFrame([x for x in full_data if x['Temettu'] > 0])
    if not df_div.empty:
        toplam_temettu = df_div['NetTemettu'].sum()
        st.metric("TAHMİNİ YILLIK NAKİT AKIŞI", f"{tr_format(toplam_temettu)} ₺", delta=f"Aylık: {tr_format(toplam_temettu/12)} ₺")
        
        div_table = "<table class='kral-table'><thead><tr><th>HİSSE</th><th>ADET</th><th>HİSSE BAŞI</th><th>YILLIK TOPLAM</th><th>VERİM (%)</th></tr></thead><tbody>"
        for _, r in df_div.iterrows():
            verim = (r['Temettu'] / r['Güncel']) * 100 if r['Güncel'] > 0 else 0
            div_table += f"<tr><td><b>{r['Hisse']}</b></td><td>{r['Adet']}</td><td>{tr_format(r['Temettu'])} ₺</td><td><b>{tr_format(r['NetTemettu'])} ₺</b></td><td>%{verim:.2f}</td></tr>"
        st.markdown(div_table + "</tbody></table>", unsafe_allow_html=True)
    else: st.warning("Temettü verisi bulunamadı.")

# --- HALKA ARZ ---
with tab_ipo:
    st.subheader("🚀 Yeni Halka Arz Ekle")
    with st.form("ipo_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        ipo_isim = ic1.text_input("Şirket Kodu (Örn: BINHO)")
        ipo_fiyat = ic2.number_input("Halka Arz Fiyatı", min_value=0.0)
        ipo_adet = ic3.number_input("Lot Sayısı", min_value=0)
        if st.form_submit_button("➕ Listeye Ekle"):
            if ipo_isim:
                st.session_state.ipo_liste.append({"Isim": ipo_isim.upper(), "Fiyat": ipo_fiyat, "Adet": ipo_adet})
                save_json(IPO_DOSYASI, st.session_state.ipo_liste); st.rerun()

    if st.session_state.ipo_liste:
        for idx, ipo in enumerate(st.session_state.ipo_liste):
            with st.expander(f"📈 {ipo['Isim']} - Tavan Simülasyonu"):
                col1, col2 = st.columns([4, 1])
                maliyet = ipo['Adet'] * ipo['Fiyat']
                tavan_list = []
                p = ipo['Fiyat']
                for g in range(1, 11):
                    p *= 1.10
                    tavan_list.append({"Gün": f"{g}. Tavan", "Fiyat": f"{tr_format(p)} ₺", "Toplam Kar": f"{tr_format((p * ipo['Adet']) - maliyet)} ₺"})
                col1.table(pd.DataFrame(tavan_list))
                if col2.button("❌ SİL", key=f"del_ipo_{idx}"):
                    st.session_state.ipo_liste.pop(idx)
                    save_json(IPO_DOSYASI, st.session_state.ipo_liste); st.rerun()

st.markdown("---")
st.caption(f"🕒 Son Güncelleme: {datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')}")

