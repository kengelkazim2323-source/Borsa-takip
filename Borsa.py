import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import 



# ==========================================
# 0. VERİ YÖNETİMİ VE CACHE SİSTEMİ
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
    """Hisse verisini ve gerçek temettüyü hızlıca çeker."""
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="35d")
        if hist.empty: return None
        
        # Gerçek Temettü Hesabı (Son 1 Yıl)
        divs = tk.dividends
        if not divs.empty:
            divs.index = divs.index.tz_localize(None)
            son_1_yil = datetime.now() - timedelta(days=365)
            yillik_temettu = divs[divs.index >= son_1_yil].sum()
        else:
            yillik_temettu = 0.0
            
        return {"hist": hist, "temettu": yillik_temettu}
    except: return None

# ==========================================
# 1. SAYI FORMATLAMA VE TEKNİK ANALİZ
# ==========================================
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
# 2. GÖRSEL AYARLAR VE TEMA SEÇİMİ
# ==========================================
st.set_page_config(page_title="KRAL BORSA", page_icon="📈", layout="wide")
st_autorefresh(interval=60000, key="datarefresh") # API'yi yormamak için 60sn

with st.sidebar:
    st.header("🎨 GÖRÜNÜM")
    # Aydınlık Gündüz kaldırıldı
    tema = st.selectbox("Tema Seçimi", ["Premium Koyu", "Matrix", "Derin Okyanus"])
    st.markdown("<br><br>", unsafe_allow_html=True)

# Tema Renk Sözlüğü (Aydınlık Gündüz çıkarıldı)
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
    h1, h2, h3, p, div {{ color: {t_sec['text']} !important; }}
    
    /* Metrik Kutuları ve Tablolar */
    [data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; font-size: 24px; color: {t_sec['accent']} !important; }}
    .stMetric {{ background: {t_sec['box']}; padding: 15px; border-radius: 10px; border-left: 5px solid {t_sec['accent']}; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    
    /* Canlı Ticker Bandı */
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); padding: 15px 0; }}
    .ticker-content {{ display: flex; animation: ticker 40s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; font-family: 'JetBrains Mono', monospace; }} 
    .down {{ color: #ff1744; font-weight: bold; font-family: 'JetBrains Mono', monospace; }}
    .tk-isim {{ font-size: 12px; opacity: 0.8; margin-bottom: 3px; }}
    .tk-fiyat {{ font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: bold; }}
    
    /* Kutu Mesafeleri */
    .stTabs {{ margin-top: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. ANALOG + DİJİTAL SAAT & TAKVİM (KÖŞEYE SIFIRLANDI)
# ==========================================
clock_html = f"""
<div style="position: fixed; top: 0px; right: 0px; background: {t_sec['box']}; padding: 10px 15px; border-radius: 0 0 0 15px; box-shadow: -2px 2px 10px rgba(0,0,0,0.3); z-index: 99999; display: flex; align-items: center; gap: 15px; border-left: 2px solid {t_sec['accent']}; border-bottom: 2px solid {t_sec['accent']};">
    <div style="position: relative; width: 40px; height: 40px; border: 2px solid {t_sec['accent']}; border-radius: 50%;">
        <div id="hour-hand" style="position: absolute; bottom: 50%; left: 50%; width: 2px; height: 12px; background: {t_sec['text']}; transform-origin: bottom; transform: translateX(-50%);"></div>
        <div id="minute-hand" style="position: absolute; bottom: 50%; left: 50%; width: 2px; height: 16px; background: {t_sec['text']}; transform-origin: bottom; transform: translateX(-50%);"></div>
        <div id="second-hand" style="position: absolute; bottom: 50%; left: 50%; width: 1px; height: 18px; background: #ff1744; transform-origin: bottom; transform: translateX(-50%);"></div>
    </div>
    <div style="text-align: right; font-family: 'Inter', sans-serif;">
        <div id="digital-clock" style="font-size: 16px; font-weight: bold; font-family: 'JetBrains Mono', monospace; color: {t_sec['text']};"></div>
        <div id="date-display" style="font-size: 11px; color: {t_sec['text']}; opacity: 0.8;"></div>
    </div>
</div>
<script>
function updateClock() {{
    const now = new Date();
    const trTime = new Date(now.toLocaleString("en-US", {{timeZone: "Europe/Istanbul"}}));
    
    const timeString = trTime.toLocaleTimeString('tr-TR', {{hour12: false}});
    const dateOptions = {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }};
    const dateString = trTime.toLocaleDateString('tr-TR', dateOptions);
    
    document.getElementById('digital-clock').innerText = timeString;
    document.getElementById('date-display').innerText = dateString;

    const hours = trTime.getHours() % 12;
    const minutes = trTime.getMinutes();
    const seconds = trTime.getSeconds();
    
    const hourDeg = (hours * 30) + (minutes * 0.5);
    const minuteDeg = (minutes * 6) + (seconds * 0.1);
    const secondDeg = seconds * 6;
    
    document.getElementById('hour-hand').style.transform = `translateX(-50%) rotate(${{hourDeg}}deg)`;
    document.getElementById('minute-hand').style.transform = `translateX(-50%) rotate(${{minuteDeg}}deg)`;
    document.getElementById('second-hand').style.transform = `translateX(-50%) rotate(${{secondDeg}}deg)`;
}}
setInterval(updateClock, 1000);
updateClock();
</script>
"""
st.components.v1.html(clock_html, height=80)

# ==========================================
# 4. GENİŞLETİLMİŞ CANLI PİYASA BANDI
# ==========================================
st.markdown(f"<h2 style='text-align:center; color:{t_sec['accent']}; margin-top:-30px;'>📈 PORTFÖY YÖNETİM MERKEZİ</h2><br>", unsafe_allow_html=True)

piyasa_izleme = {
    "BIST 100": "XU100.IS", "BIST 30": "XU030.IS", "GRAM ALTIN": "GAU-TRY", "ONS ALTIN": "GC=F", 
    "GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X", "EUR/TRY": "EURTRY=X", "BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD"
}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-content">'
for isim, sembol in piyasa_izleme.items():
    d = fetch_stock_data(sembol)
    if d:
        hist = d['hist']
        if len(hist) >= 2:
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            degisim = ((last - prev) / prev) * 100
            color_class = "up" if degisim >= 0 else "down"
            ticker_content += f'<div style="text-align:center;"><div class="tk-isim">{isim}</div><div class="tk-fiyat">{tr_format(last)}</div><div class="{color_class}">{degisim:+.2f}%</div></div>'
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 5. TAM BİST LİSTESİ VE HİSSE EKLEME (FİXLENDİ)
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

with st.expander("➕ LİSTEYE YENİ HİSSE EKLE", expanded=False):
    col_v, col_a, col_m, col_b = st.columns([2, 1, 1, 1])
    with col_v: s_varlik = st.selectbox("Hisse Seç", BIST_FULL)
    with col_a: s_adet = st.number_input("Adet", min_value=0.01, step=1.0) # 0.01 yapıldı ki boş geçilmesin
    with col_m: s_maliyet = st.number_input("Maliyet (₺)", min_value=0.0, format="%.2f")
    with col_b: 
        st.write("") 
        st.write("")
        if st.button("🚀 PORTFÖYE EKLE", use_container_width=True):
            if s_varlik and s_adet > 0:
                yeni_kayit = {"Hisse": s_varlik, "Adet": float(s_adet), "Maliyet": float(s_maliyet)}
                st.session_state.portfoy.append(yeni_kayit)
                save_data(st.session_state.portfoy)
                st.success(f"Başarılı: {s_varlik} eklendi!") # Ince ayar: Kullanıcıya bilgi
                st.rerun()
            else:
                st.error("Adet 0'dan büyük olmalı!") # Ince ayar: Hata yakalama

st.markdown("<br>", unsafe_allow_html=True) 

# ==========================================
# 6. VERİ ANALİZİ VE SİNYALLER
# ==========================================
if st.session_state.portfoy:
    p_data = []
    total_daily_gain = 0
    
    for i, item in enumerate(st.session_state.portfoy):
        d = fetch_stock_data(item['Hisse'])
        if d:
            hist = d['hist']
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                daily_pct = ((curr - prev_close) / prev_close) * 100
                daily_tl = (curr - prev_close) * float(item['Adet'])
                
                total_daily_gain += daily_tl
                val = float(item['Adet']) * curr
                kz = (curr - float(item['Maliyet'])) * float(item['Adet'])
                signal = get_signal(hist)
                
                # Gerçek Temettü Hesaplaması
                yillik_temettu = d['temettu'] * float(item['Adet'])
                
                p_data.append({
                    "id": i, "Varlık": item['Hisse'], "Sinyal": signal, "Adet": item['Adet'],
                    "Güncel": curr, "Günlük (%)": daily_pct, "Günlük Fark (₺)": daily_tl,
                    "Değer": val, "K/Z": kz, "Yıllık Temettü": yillik_temettu
                })

    if p_data:
        df = pd.DataFrame(p_data)
        tab1, tab2, tab3 = st.tabs(["📊 PORTFÖYÜM", "📈 DAĞILIM", "💰 TEMETTÜ"])

        with tab1:
            m1, m2, m3 = st.columns(3)
            m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
            m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺")
            m3.metric("GÜNLÜK K/Z", f"{tr_format(total_daily_gain)} ₺", delta=f"{total_daily_gain:,.2f} ₺")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            for idx, row in df.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 0.5])
                c1.write(f"**{row['Varlık']}** ({row['Sinyal']})")
                c2.write(f"Fiyat: {tr_format(row['Güncel'])}")
                
                renk = "#00e676" if row['Günlük (%)'] >= 0 else "#ff1744"
                c3.markdown(f"<span style='color:{renk}; font-weight:bold;'>%{row['Günlük (%)']:+.2f}</span>", unsafe_allow_html=True)
                
                c4.write(f"K/Z: {tr_format(row['K/Z'])}")
                c5.write(f"Değer: {tr_format(row['Değer'])}")
                
                if c6.button("❌", key=f"del_{row['id']}"):
                    st.session_state.portfoy.pop(int(row['id']))
                    save_data(st.session_state.portfoy)
                    st.rerun()
                st.divider()

        with tab2:
            fig = px.pie(df, values='Değer', names='Varlık', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t_sec['text']))
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            top_div = df['Yıllık Temettü'].sum()
            st.success(f"### Gerçekleşen Yıllık Net Temettü: {tr_format(top_div)} ₺")
            st.info("Not: Bu veri son 1 yılda ödenen hisse başı temettü miktarları üzerinden hesaplanmıştır. Tahmini değil, gerçektir.")
            df_div = df[df['Yıllık Temettü'] > 0].copy()
            if not df_div.empty:
                df_div['Yıllık Temettü'] = df_div['Yıllık Temettü'].apply(lambda x: f"{tr_format(x)} ₺")
                st.dataframe(df_div[["Varlık", "Adet", "Yıllık Temettü"]], use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ TÜM PORTFÖYÜ SIFIRLA"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()
else:
    st.info("Portföy boş kral, ekleme yapmanı bekliyorum.")



tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Yüklendi.")


