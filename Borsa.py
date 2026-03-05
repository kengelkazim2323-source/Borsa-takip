import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from datetime import datetime

# ==========================================
# 1. AYARLAR & TASARIM (PREMIUM TERMINAL)
# ==========================================
st.set_page_config(page_title="İmparator Terminal v8", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stMetric { border-radius: 10px; background-color: #161b22; padding: 15px; border: 1px solid #30363d; }
    .ticker-box { text-align: center; padding: 10px; border-radius: 8px; background: #1c2128; border: 1px solid #30363d; margin: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA ---
def load_permanent_data():
    js_get = "localStorage.getItem('kral_v8_data');"
    res = st_javascript(js_get)
    if res and res != "null":
        return json.loads(res)
    return None

def save_permanent_data(data):
    js_set = f"localStorage.setItem('kral_v8_data', '{json.dumps(data)}');"
    st_javascript(js_set)

if 'portfoy' not in st.session_state:
    stored = load_permanent_data()
    st.session_state.portfoy = stored if stored else []

# ==========================================
# 2. CANLI PİYASA PANELİ & DOLAR KURU
# ==========================================
st.title("🏛️ İmparator Yatırım Terminali v8.0")

piyasa_hisseleri = {
    "Dolar ($)": "USDTRY=X", "Euro (€)": "EURTRY=X", "Gram Altın": "GAU-TRY.IS",
    "Gram Gümüş": "GAG-TRY.IS", "Ons Altın": "GC=F", "Ons Gümüş": "SI=F",
    "BIST 100": "XU100.IS", "Bitcoin": "BTC-USD"
}

usd_kur = 1.0
try:
    usd_kur = yf.Ticker("USDTRY=X").fast_info['lastPrice']
except: usd_kur = 32.5 # Hata durumunda varsayılan (yaklaşık)

st.subheader("🛰️ Canlı Piyasa Verileri")
p_cols = st.columns(len(piyasa_hisseleri))

for i, (isim, sembol) in enumerate(piyasa_hisseleri.items()):
    try:
        t_obj = yf.Ticker(sembol)
        fiyat = t_obj.fast_info['lastPrice']
        prev = t_obj.fast_info['regularMarketPreviousClose']
        degisim = ((fiyat - prev) / prev) * 100
        with p_cols[i]:
            st.markdown(f"""<div class="ticker-box">
                <small style='color: #8b949e;'>{isim}</small><br>
                <strong>{fiyat:.2f}</strong><br>
                <span style='color: {"#238636" if degisim >= 0 else "#da3633"};'>
                    {"▲" if degisim >= 0 else "▼"} %{abs(degisim):.2f}
                </span>
            </div>""", unsafe_allow_html=True)
    except: continue

st.markdown("---")

# ==========================================
# 3. DEV BIST LİSTESİ (A-Z TAM LİSTE)
# ==========================================
BIST_FULL = sorted([
    "A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS",
    "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS",
    "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS",
    "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS",
    "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS",
    "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS",
    "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS",
    "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS",
    "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS",
    "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS",
    "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS",
    "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS",
    "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS",
    "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS",
    "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS",
    "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS",
    "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS",
    "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS",
    "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS",
    "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS",
    "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS",
    "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS",
    "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS",
    "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS",
    "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS",
    "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS",
    "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS",
    "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS",
    "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS",
    "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS",
    "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS",
    "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS",
    "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS",
    "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS",
    "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS",
    "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS",
    "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS",
    "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS",
    "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS",
    "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS",
    "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS",
    "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS",
    "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS",
    "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS",
    "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS",
    "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS",
    "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS",
    "ZOREN.IS", "ZRGYO.IS"
])
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]
TUM_LISTE = sorted(BIST_FULL + GLOBAL_LIST)

# ==========================================
# 4. YAN PANEL (GİRİŞ)
# ==========================================
with st.sidebar:
    st.header("👑 Portföy Girişi")
    secilen = st.selectbox("Hisse Ara:", TUM_LISTE)
    adet = st.number_input("Adet:", min_value=0.0, step=1.0)
    maliyet = st.number_input("Maliyet (TL):", min_value=0.0, format="%.3f")
    temettu = st.slider("Beklenen Temettü (%)", 0.0, 20.0, 2.0)
    
    if st.button("🚀 Portföye Ekle"):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet, "Temettu": temettu})
        save_permanent_data(st.session_state.portfoy)
        st.rerun()

    if st.button("🗑️ Sıfırla"):
        st.session_state.portfoy = []
        save_permanent_data([])
        st.rerun()

# ==========================================
# 5. PORTFÖY ANALİZ - TABLAR
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 TL Analizi", "💵 Dolar Bazlı Analiz", "📰 Haberler"])

with tab1:
    if st.session_state.portfoy:
        data = []
        t_m, t_d, t_t = 0, 0, 0
        for item in st.session_state.portfoy:
            try:
                h = yf.Ticker(item['Hisse'])
                f = h.fast_info['lastPrice']
                m_t = item['Adet'] * item['Maliyet']
                d_t = item['Adet'] * f
                kz = d_t - m_t
                t_m += m_t; t_d += d_t; t_t += (d_t * item['Temettu'] / 100)
                data.append({"Varlık": item['Hisse'], "K/Z": kz, "Değer": d_t})
            except: continue
        
        df = pd.DataFrame(data)
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Portföy", f"{t_d:,.2f} TL")
        c2.metric("Toplam K/Z", f"{t_d-t_m:,.2f} TL", f"%{((t_d-t_m)/t_m*100):.2f}")
        c3.metric("Yıllık Temettü", f"{t_t:,.2f} TL")
        
        st.plotly_chart(px.pie(df, values='Değer', names='Varlık', title="TL Dağılım"), use_container_width=True)
    else: st.info("Hisse ekleyin.")

with tab2:
    if st.session_state.portfoy:
        st.subheader("🇺🇸 Dolar Bazlı Performans")
        dolar_data = []
        for item in st.session_state.portfoy:
            try:
                h = yf.Ticker(item['Hisse'])
                f_tl = h.fast_info['lastPrice']
                # Dolar bazlı maliyet (Maliyet / Mevcut Kur - Basitleştirilmiş)
                # Not: Gerçek analiz için alış tarihindeki kur gerekir ama bu "şu anki" dolar gücünü gösterir.
                f_usd = f_tl / usd_kur
                m_usd = item['Maliyet'] / usd_kur
                val_usd = item['Adet'] * f_usd
                kz_usd = (f_usd - m_usd) * item['Adet']
                dolar_data.append({"Varlık": item['Hisse'], "USD Değer": val_usd, "USD K/Z": kz_usd})
            except: continue
        
        df_usd = pd.DataFrame(dolar_data)
        st.plotly_chart(px.bar(df_usd, x='Varlık', y='USD K/Z', color='USD K/Z', 
                               title="Varlık Bazlı Dolar Kâr/Zarar ($)",
                               color_continuous_scale='RdYlGn'), use_container_width=True)
        st.metric("Toplam Dolar Değeri", f"${df_usd['USD Değer'].sum():,.2f}")
    else: st.info("Veri yok.")

with tab3:
    st.subheader("🗞️ Güncel Gelişmeler")
    target = st.session_state.portfoy[0]['Hisse'] if st.session_state.portfoy else "XU100.IS"
    news = yf.Ticker(target).news
    for n in news[:8]:
        st.markdown(f"**{n['publisher']}** - [{n['title']}]({n['link']})")
