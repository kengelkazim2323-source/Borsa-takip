import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from datetime import datetime

# ==========================================
# 1. AYARLAR & TASARIM
# ==========================================
st.set_page_config(page_title="İMPARATOR TERMINAL v9.5", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; background-color: #0d1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px !important; }
    .ticker-box { text-align: center; padding: 10px; border-radius: 8px; background: #1c2128; border: 1px solid #30363d; margin: 2px; }
    .news-card { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-bottom: 8px; border: 1px solid #30363d; }
    .surge-card { background: linear-gradient(90deg, #21262d 0%, #161b22 100%); border: 1px solid #d29922; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
    .ai-note { background-color: #0d1117; border: 1px dashed #58a6ff; padding: 15px; border-radius: 10px; color: #adbac7; }
    h1, h2, h3 { color: #58a6ff !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA ---
def load_permanent_data():
    js_get = "localStorage.getItem('kral_v9_data');"
    res = st_javascript(js_get)
    if res and res != "null": return json.loads(res)
    return None

def save_permanent_data(data):
    js_set = f"localStorage.setItem('kral_v9_data', '{json.dumps(data)}');"
    st_javascript(js_set)

if 'portfoy' not in st.session_state:
    stored = load_permanent_data()
    st.session_state.portfoy = stored if stored else []

# ==========================================
# 2. ÜST PANEL & CANLI PİYASA
# ==========================================
st.markdown("# 🏛️ İMPARATOR YATIRIM TERMİNALİ v9.5")

piyasa_hisseleri = {
    "DOLAR": "USDTRY=X", "EURO": "EURTRY=X", "ONS ALTIN": "GC=F",
    "ONS GÜMÜŞ": "SI=F", "GRAM ALTIN": "GAU-TRY.IS", "BIST 100": "XU100.IS", "BITCOIN": "BTC-USD"
}

usd_kur = 33.0 
p_cols = st.columns(len(piyasa_hisseleri))

for i, (isim, sembol) in enumerate(piyasa_hisseleri.items()):
    try:
        t_obj = yf.Ticker(sembol)
        fiyat = t_obj.fast_info['lastPrice']
        prev = t_obj.fast_info['regularMarketPreviousClose']
        degisim = ((fiyat - prev) / prev) * 100
        if isim == "DOLAR": usd_kur = fiyat
        with p_cols[i]:
            st.markdown(f"""<div class="ticker-box">
                <small style='color: #8b949e;'>{isim}</small><br>
                <strong style='font-size: 1.1em; color: #f0f6fc;'>{fiyat:,.2f}</strong><br>
                <span style='color: {"#3fb950" if degisim >= 0 else "#f85149"}; font-size: 0.9em;'>
                    {"▲" if degisim >= 0 else "▼"} %{abs(degisim):.2f}
                </span>
            </div>""", unsafe_allow_html=True)
    except: continue

# ==========================================
# 3. YAN PANEL (DEV BIST LİSTESİ)
# ==========================================
BIST_FULL = sorted([
    "A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"
])
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "AMZN", "GOOGL", "MSFT", "META", "BTC-USD", "ETH-USD", "SI=F", "GC=F"]
TUM_LISTE = sorted(list(set(BIST_FULL + GLOBAL_LIST)))

with st.sidebar:
    st.header("👑 Portföy Girişi")
    secilen = st.selectbox("Varlık Seç (Ara):", TUM_LISTE)
    adet = st.number_input("Adet:", min_value=0.0, step=1.0)
    maliyet = st.number_input("Birim Maliyet:", min_value=0.0, format="%.3f")
    
    if st.button("🚀 Portföye Ekle"):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet, "Temettu": 2.0})
        save_permanent_data(st.session_state.portfoy)
        st.success(f"{secilen} portföye eklendi!")
        st.rerun()
    
    st.markdown("---")
    if st.button("🗑️ Portföyü Sıfırla"):
        st.session_state.portfoy = []
        save_permanent_data([])
        st.rerun()

# ==========================================
# 4. ANALİZ MERKEZİ
# ==========================================
t1, t2, t3, t4 = st.tabs(["📊 Portföy Analizi", "💵 Dolar Bazlı", "📢 Hacim İstihbaratı", "📰 Canlı Haberler"])

if st.session_state.portfoy:
    data = []
    t_maliyet, t_deger = 0, 0
    for item in st.session_state.portfoy:
        try:
            h = yf.Ticker(item['Hisse'])
            f = h.fast_info['lastPrice']
            m_top = item['Adet'] * item['Maliyet']
            d_top = item['Adet'] * f
            data.append({
                "Varlık": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": f, "Değer": d_top, "K/Z": d_top - m_top,
                "USD_KZ": (d_top - m_top) / usd_kur
            })
            t_maliyet += m_top; t_deger += d_top
        except: continue
    df = pd.DataFrame(data)

    with t1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Toplam Varlık (TL)", f"{t_deger:,.2f}")
            kz_tl = t_deger - t_maliyet
            st.metric("Net Kar/Zarar", f"{kz_tl:,.2f} TL", f"%{((kz_tl/t_maliyet)*100):.2f}" if t_maliyet > 0 else "0")
            
            # AI NOTU
            if not df.empty:
                best = df.loc[df['K/Z'].idxmax(), 'Varlık']
                st.markdown(f"""<div class="ai-note">
                🤖 <b>Yapay Zeka Analizi:</b> Bugün yıldızın <b>{best}</b> gibi görünüyor. 
                Portföyünün %{(df['Değer'].max()/t_deger*100):.1f}'i tek varlıkta. Çeşitlendirmeyi düşünebilirsin.
                </div>""", unsafe_allow_html=True)
                
        with col2:
            st.plotly_chart(px.pie(df, values='Değer', names='Varlık', hole=0.5, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        st.dataframe(df.style.format({"Maliyet": "{:.2f}", "Güncel": "{:.2f}", "Değer": "{:,.2f}", "K/Z": "{:,.2f}"}), use_container_width=True)

    with t2:
        st.subheader("🇺🇸 Dolar Bazlı Performans")
        st.metric("Toplam USD Değer", f"${(t_deger/usd_kur):,.2f}")
        st.plotly_chart(px.bar(df, x='Varlık', y='USD_KZ', color='USD_KZ', color_continuous_scale='RdYlGn', template="plotly_dark"), use_container_width=True)

else:
    with t1: st.info("Hemen yan panelden hisse ekleyerek imparatorluğunu kurmaya başla!")

with t3:
    st.subheader("⚡ Olağandışı Hacim Girişleri (Top 20)")
    # Performans için ilk 20 varlığı tara
    hacim_bulundu = False
    with st.spinner("Varlıklar taranıyor..."):
        for s in TUM_LISTE[:20]:
            try:
                h_obj = yf.Ticker(s)
                h_hist = h_obj.history(period="5d")
                if len(h_hist) >= 2:
                    v_avg = h_hist['Volume'].iloc[:-1].mean()
                    v_now = h_hist['Volume'].iloc[-1]
                    if v_now > v_avg * 1.5:
                        st.markdown(f"""<div class="surge-card">🔥 <b>{s}</b>: Hacim patlaması! (Artış: %{((v_now/v_avg)*100-100):.0f})</div>""", unsafe_allow_html=True)
                        hacim_bulundu = True
            except: continue
    if not hacim_bulundu: st.write("Şu an taranan ana varlıklarda olağandışı bir durum yok.")

with t4:
    st.subheader("📢 Canlı Haber Akışı")
    h_symbol = st.session_state.portfoy[0]['Hisse'] if st.session_state.portfoy else "XU100.IS"
    try:
        raw_news = yf.Ticker(h_symbol).news
        if not raw_news: raw_news = yf.Ticker("XU100.IS").news
        for n in raw_news[:12]:
            st.markdown(f"""<div class="news-card">
            <small style='color:#8b949e;'>{datetime.fromtimestamp(n.get('providerPublishTime', 0)).strftime('%H:%M')}</small> | <b>{n.get('publisher')}</b><br>
            <a href="{n.get('link')}" target="_blank" style='text-decoration:none; color:#58a6ff; font-weight:bold;'>{n.get('title')}</a>
            </div>""", unsafe_allow_html=True)
    except: st.error("Haberlere ulaşılamıyor.")
