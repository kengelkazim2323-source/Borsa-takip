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
# 1. YENİ NESİL RENK TEMALARI
# ==========================================
st.set_page_config(page_title="Borsa Takip", page_icon="📈", layout="wide")
st_autorefresh(interval=1000, key="datarefresh")

with st.sidebar:
    st.header("🎨 Borsa Takip")
    tema = st.selectbox("Tema Seçimi", [
        "Galaksi (VIP)", "Premium Koyu", "Altın Vuruş", 
        "Zümrüt Yeşili", "Siber Punk", "Retro Kehribar", "Matrix",
        "Okyanus Derinliği", "Lav Akışı", "Kuzey Işıkları", 
        "Buzul (Dark)", "Mor Ötesi", "Bakır Buharı", 
        "Gece Yarısı", "Safir Gece", "Çöl Fırtınası", "Kızıl Elmas"
    ])

tema_renkleri = {
    "Premium Koyu": {"bg": "#121212", "text": "#ffffff", "box": "#4c4c4c", "accent": "#BB86FC"},
    "Galaksi (VIP)": {"bg": "#0B0E14", "text": "#E0E0E0", "box": "#161B22", "accent": "#00D4FF"},
    "Altın Vuruş": {"bg": "#0F0F0F", "text": "#F5F5F5", "box": "#1A1A1A", "accent": "#D4AF37"},
    "Zümrüt Yeşili": {"bg": "#06120B", "text": "#E8F5E9", "box": "#0D2114", "accent": "#00E676"},
    "Siber Punk": {"bg": "#0D0221", "text": "#FFFFFF", "box": "#190033", "accent": "#FF00FF"},
    "Retro Kehribar": {"bg": "#0A0A0A", "text": "#FFB300", "box": "#1A1A1A", "accent": "#FF8F00"},
    "Matrix": {"bg": "#000000", "text": "#00FF41", "box": "#0D0208", "accent": "#00FF41"},
    # --- YENİ EKLENEN 10 TEMA ---
    "Okyanus Derinliği": {"bg": "#001B2E", "text": "#ADB5BD", "box": "#003554", "accent": "#24D1FF"},
    "Lav Akışı": {"bg": "#1A0F0F", "text": "#F8F9FA", "box": "#2D1B1B", "accent": "#FF4D4D"},
    "Kuzey Işıkları": {"bg": "#0B101B", "text": "#E9ECEF", "box": "#1B263B", "accent": "#A5FFD6"},
    "Buzul (Dark)": {"bg": "#0D1117", "text": "#C9D1D9", "box": "#161B22", "accent": "#58A6FF"},
    "Mor Ötesi": {"bg": "#120D1D", "text": "#E0D7FF", "box": "#1E1631", "accent": "#9D4EDD"},
    "Bakır Buharı": {"bg": "#1B1510", "text": "#D4A373", "box": "#2C211A", "accent": "#E76F51"},
    "Gece Yarısı": {"bg": "#050505", "text": "#FFFFFF", "box": "#121212", "accent": "#F72585"},
    "Safir Gece": {"bg": "#03045E", "text": "#CAF0F8", "box": "#023E8A", "accent": "#00B4D8"},
    "Çöl Fırtınası": {"bg": "#1C1917", "text": "#F5F5F4", "box": "#292524", "accent": "#EAB308"},
    "Kızıl Elmas": {"bg": "#0F0202", "text": "#FFFFFF", "box": "#1F0505", "accent": "#D00000"}
}
t_sec = tema_renkleri[tema]
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@700&display=swap');
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; font-family: 'Inter', sans-serif; }}
    
    [data-testid="stMetric"] {{
        background: {t_sec['box']};
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid {t_sec['accent']} !important;
        text-align: center;
    }}

    .kral-table {{
        width: 100%;
        border-collapse: collapse;
        background: {t_sec['box']}22;
        margin-top: 10px;
        border: 1px solid {t_sec['accent']}33;
    }}
    .kral-table th {{
        padding: 12px;
        text-align: left;
        background: {t_sec['accent']}22;
        color: {t_sec['accent']};
        font-weight: 700;
        font-size: 14px;
        border-bottom: 2px solid {t_sec['accent']}44;
    }}
    .kral-table td {{
        padding: 12px;
        border-bottom: 1px solid {t_sec['accent']}11;
        font-size: 14px;
        color: {t_sec['text']};
    }}
    
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
# 4. HİSSE EKLEME (TAM LİSTE)
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLKIM.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

with st.expander("➕ PORTFÖYE VARLIK EKLE"):
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Amerikan Borsası"], horizontal=True)
    with st.form("hisse_ekle_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        if piyasa_sec == "Türk Borsası": hisse_sec = f1.selectbox("Hisse Seç", BIST_FULL)
        else: hisse_sec = f1.text_input("Sembol").upper()
        adet_sec = f2.number_input("Adet", min_value=0)
        maliyet_sec = f3.number_input("Maliyet", min_value=0.0)
        if st.form_submit_button("🚀 EKLE"):
            st.session_state.portfoy.append({"Piyasa": piyasa_sec, "Hisse": hisse_sec, "Adet": adet_sec, "Maliyet": maliyet_sec})
            save_data(st.session_state.portfoy); st.rerun()

# ==========================================
# 5. LİSTELEME VE TEMETTÜ
# ==========================================
if st.session_state.portfoy:
    tab_tr, tab_us, tab_div = st.tabs(["🇹🇷 TÜRK BORSASI", "🇺🇸 AMERİKAN BORSASI", "💰 TEMETTÜ GELİRİ"])
    
    full_data = []
    for i, item in enumerate(st.session_state.portfoy):
        d = fetch_stock_data(item['Hisse'])
        if d:
            c = d['hist']['Close'].iloc[-1]; pc = d['hist']['Close'].iloc[-2]
            full_data.append({
                "id": i, "Piyasa": item.get("Piyasa", "Türk Borsası"), "Hisse": item['Hisse'], 
                "Sinyal": get_signal(d['hist']), "Adet": item['Adet'], "Maliyet": item['Maliyet'], 
                "Güncel": c, "K/Z": (c - item['Maliyet']) * item['Adet'], 
                "Değer": c * item['Adet'], "Temettu": d['temettu'], 
                "NetTemettu": d['temettu'] * item['Adet'], "DailyDiff": (c - pc) * item['Adet']
            })

    def portfoy_goster(piyasa_turu, tab_container, data_list):
        with tab_container:
            df = pd.DataFrame([x for x in data_list if x['Piyasa'] == piyasa_turu])
            if df.empty: st.info("Henüz varlık yok."); return
                
            # --- SIRALAMA EKLE (Hisse Adına Göre Alfabetik) ---
            df = df.sort_values(by="Hisse")
            
            birim = "₺" if piyasa_turu == "Türk Borsası" else "$"
             
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} {birim}")
            m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} {birim}")
            m3.metric("GÜNLÜK FARK", f"{tr_format(df['DailyDiff'].sum())} {birim}")

            st.markdown("<br>", unsafe_allow_html=True)
        
            # --- YATAY SATIR VE SÜTUNLU TABLO ---
            table_html = "<table class='kral-table'><thead><tr>"
            table_html += "<th>HİSSE</th><th>SİNYAL</th><th>ADET</th><th>MALİYET(₺)</th><th>GÜNCEL(₺)</th><th>K/Z(₺)</th><th>TOPLAM(₺)</th>"
            table_html += "</tr></thead><tbody>"
            for _, r in df.iterrows():
                kz_color = "#00e676" if r['K/Z'] >= 0 else "#ff1744"
                table_html += "<tr>"
                table_html += f"<td><b>{r['Hisse']}</b></td>"
                table_html += f"<td>{r['Sinyal']}</td>"
                table_html += f"<td>{r['Adet']}</td>"
                table_html += f"<td>{tr_format(r['Maliyet'])}</td>"
                table_html += f"<td>{tr_format(r['Güncel'])}</td>"
                table_html += f"<td style='color:{kz_color}; font-weight:bold;'>{tr_format(r['K/Z'])}</td>"
                table_html += f"<td><b>{tr_format(r['Değer'])}</td>"
                table_html += "</tr>"
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

            # Silme Butonları (Tablo yapısını bozmamak için expander içine alındı)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("⚙️ HİSSE SİL"):
                cols = st.columns(4)
                for idx, r in df.iterrows():
                    if cols[idx % 4].button(f"❌ {r['Hisse']} Sil", key=f"del_{r['id']}"):
                        st.session_state.portfoy.pop(r['id']); save_data(st.session_state.portfoy); st.rerun()
            
            # --- GELİŞTİRİLMİŞ DAİRESEL GRAFİK ---
            st.markdown("<br>", unsafe_allow_html=True)
            fig = px.pie(df, values='Değer', names='Hisse', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#000000', width=1)))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t_sec['text']), showlegend=False, margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    portfoy_goster("Türk Borsası", tab_tr, full_data)
    portfoy_goster("Amerikan Borsası", tab_us, full_data)

    with tab_div:
        df_div = pd.DataFrame(full_data)
        if not df_div.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("💰 Yıllık Beklenen Nakit Akışı")
            tr_total = df_div[df_div['Piyasa'] == "Türk Borsası"]['NetTemettu'].sum()
            us_total = df_div[df_div['Piyasa'] == "Amerikan Borsası"]['NetTemettu'].sum()
            c1, c2 = st.columns(2)
            c1.metric("TOPLAM (BIST)", f"{tr_format(tr_total)} ₺")
            c2.metric("TOPLAM (ABD)", f"{tr_format(us_total)} $")
            st.markdown("---")
            h_cols = st.columns([2, 1, 1, 1.5])
            for col, txt in zip(h_cols, ["VARLIK", "ADET", "HİSSE BAŞI", "YILLIK NET GELİR"]): col.markdown(f"**{txt}**")
            st.divider()
            for _, r in df_div.sort_values(by="NetTemettu", ascending=False).iterrows():
                if r['Temettu'] > 0:
                    birim = "₺" if r['Piyasa'] == "Türk Borsası" else "$"   
                    
                    cc1, cc2, cc3, cc4 = st.columns([2, 1, 1, 1.5])
                    cc1.write(f"**{r['Hisse']}**")
                    cc2.write(f"{r['Adet']}")
                    cc3.write(f"{tr_format(r['Temettu'])} {birim}")
                    cc4.write(f"**{tr_format(r['NetTemettu'])} {birim}**")
                    st.divider()
        else: st.info("Temettü veren hisse bulunamadı.")

    if st.button("🗑️ TÜMÜNÜ SİL"):
        st.session_state.portfoy = []; save_data([]); st.rerun()
else:
    st.info("Portföy boş, lütfen ekleme yapınız.")
    

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Aktif.")
