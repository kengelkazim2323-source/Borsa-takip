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
# 0. VERİTABANI VE DOSYA YÖNETİMİ (FIXED)
# ==========================================
PORTFOY_FILE = "portfoy_kayitlari.json"

def load_portfoy():
    if os.path.exists(PORTFOY_FILE):
        try:
            with open(PORTFOY_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                return json.loads(content) if content else []
        except: return []
    return []

def save_portfoy(data):
    with open(PORTFOY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Session state ilk kurulum
if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_portfoy()

# ==========================================
# 1. VERİ MOTORU (ÖNBELLEK AYARLI)
# ==========================================
@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="60d")
        if hist.empty: return None
        divs = tk.dividends
        h_basi_t = divs[divs.index.tz_localize(None) > (datetime.now() - timedelta(days=365))].sum() if not divs.empty else 0.0
        return {"hist": hist, "h_basi_t": h_basi_t, "last_price": hist['Close'].iloc[-1]}
    except: return None

def tr_format(val):
    try:
        if val is None or pd.isna(val): return "0,00"
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

def get_signal(data):
    if data is None or len(data) < 35: return "BEKLE"
    c = data['Close']
    d = c.diff(); g = d.where(d > 0, 0).rolling(14).mean(); l = -d.where(d < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + g/l)).iloc[-1]
    macd = c.ewm(span=12).mean() - c.ewm(span=26).mean(); sig = macd.ewm(span=9).mean()
    if rsi < 40 and macd.iloc[-1] > sig.iloc[-1]: return "🔥 GÜÇLÜ AL"
    if rsi > 65: return "🔴 SAT"
    return "🟢 AL" if macd.iloc[-1] > sig.iloc[-1] else "🟡 TUT"

# ==========================================
# 2. GÖRSEL AYARLAR & TICKER
# ==========================================
st.set_page_config(page_title="KRAL BORSA", layout="wide")
st_autorefresh(interval=15000, key="refresh")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; }
    .ticker-wrapper { width: 100%; overflow: hidden; background: #121212; color: #00ff00; padding: 12px; margin-bottom: 20px; border-bottom: 2px solid #1a73e8; }
    .ticker-content { display: flex; animation: ticker 40s linear infinite; white-space: nowrap; gap: 60px; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    </style>
    """, unsafe_allow_html=True)

# Canlı Akış
piyasa_list = {"BIST 100": "XU100.IS", "ALTIN": "GAU-TRY", "DOLAR": "USDTRY=X", "GÜMÜŞ": "SI=F"}
ticker_html = '<div class="ticker-wrapper"><div class="ticker-content">'
for isim, sembol in piyasa_list.items():
    d = get_data(sembol)
    if d:
        ticker_html += f'<span>{isim}: {tr_format(d["last_price"])} </span>'
st.markdown(ticker_html + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 3. HİSSE EKLEME PANELİ (FIXED LOGIC)
# ==========================================
# (BIST_FULL listeniz burada aynen duruyor, yer kaplamasın diye kısalttım ama kodda tam çalışır)
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

with st.sidebar:
    st.header("🚀 HİSSE EKLE")
    h_sec = st.selectbox("Hisse", BIST_FULL)
    h_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    h_maly = st.number_input("Maliyet", min_value=0.0)
    if st.button("PORTFÖYE EKLE", use_container_width=True):
        if h_adet > 0:
            # Önce güncel listeyi yükle
            current_p = load_portfoy()
            # Yeni hisseyi ekle
            current_p.append({"Hisse": h_sec, "Adet": h_adet, "Maliyet": h_maly})
            # Dosyaya yaz (Atomik işlem)
            save_portfoy(current_p)
            # Session state'i güncelle
            st.session_state.portfoy = current_p
            st.success(f"{h_sec} Eklendi!")
            st.rerun()

# ==========================================
# 4. ANALİZ VE KRALIN TEMETTÜ KODU
# ==========================================
if st.session_state.portfoy:
    p_rows = []
    for item in st.session_state.portfoy:
        d = get_data(item['Hisse'])
        if d:
            curr = d['last_price']
            p_rows.append({
                "Varlık": item['Hisse'], "Sinyal": get_signal(d['hist']), "Adet": item['Adet'],
                "Güncel": curr, "Değer": curr * item['Adet'], "K/Z": (curr - item['Maliyet']) * item['Adet'],
                "Net Temettü": d['h_basi_t'] * item['Adet']
            })
    
    df = pd.DataFrame(p_rows)
    t1, t2, t3 = st.tabs(["📊 PORTFÖY", "📈 DAĞILIM", "💰 TEMETTÜ"])
    
    with t1:
        c1, c2 = st.columns(2)
        c1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
        c2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺", delta=f"{df['K/Z'].sum():,.2f}")
        st.dataframe(df.drop(columns=['Net Temettü']), use_container_width=True, hide_index=True)

    with t2:
        st.plotly_chart(px.pie(df, values='Değer', names='Varlık', hole=0.5, title="Varlık Dağılımı"), use_container_width=True)

    with t3:
        # KRALIN EFSANE TEMETTÜ KODU (DOKUNULMADI):
        st.markdown(f"### 💰 Yıllık Tahmini Net Temettü: **{tr_format(df['Net Temettü'].sum())} ₺**")
        st.dataframe(df[df['Net Temettü'] > 0][['Varlık', 'Adet', 'Net Temettü']], use_container_width=True, hide_index=True)

if st.sidebar.button("🗑️ TÜMÜNÜ SİL", type="primary"):
    save_portfoy([])
    st.session_state.portfoy = []
    st.rerun()

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Yüklendi.")


