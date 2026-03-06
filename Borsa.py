import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. OTOMATİK YENİLEME VE HAFIZA
# ==========================================
# Eğer hata alırsan terminale: pip install streamlit-autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="terminal_refresh")
except:
    st.warning("Yenileme modülü eksik! 'pip install streamlit-autorefresh' yazmalısın.")

PORTFOY_DOSYASI = "portfoy_verileri.json"

def load_data():
    if os.path.exists(PORTFOY_DOSYASI):
        try:
            with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_data(data):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. ÖZEL TEMA TASARIMI (DARK TERMINAL)
# ==========================================
st.set_page_config(page_title="BORSA TERMİNALİ", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { margin-top: -80px; background-color: #05070a; } 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; color: #e6edf3; }
    
    .ticker-wrapper { width: 100%; overflow-x: auto; background: rgba(13, 17, 23, 0.95); border-bottom: 1px solid #00ff41; position: fixed; top: 0; left: 0; right: 0; z-index: 9999; backdrop-filter: blur(10px); }
    .ticker-container { display: flex; padding: 12px 20px; gap: 40px; width: max-content; }
    .ticker-card { display: flex; flex-direction: column; align-items: center; border-right: 1px solid #30363d; padding-right: 20px; }
    .up { color: #00ff41; text-shadow: 0 0 10px rgba(0,255,65,0.3); }
    .down { color: #ff3131; text-shadow: 0 0 10px rgba(255,49,49,0.3); }
    .stMetric { background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .signal-box { background: #0d1117; border-left: 4px solid #00ff41; padding: 15px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CANLI PİYASA AKIŞI
# ==========================================
piyasa_izleme = {"BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "ONS ALTIN": "GC=F", "BITCOIN": "BTC-USD", "NASDAQ": "^IXIC", "THY": "THYAO.IS", "EREGLI": "EREGL.IS"}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        last = tk.fast_info['lastPrice']
        prev = tk.fast_info['regularMarketPreviousClose']
        degisim = ((last - prev) / prev) * 100
        renk = "up" if degisim >= 0 else "down"
        ticker_content += f'<div class="ticker-card"><span class="{"up" if degisim>=0 else "down"}" style="font-weight:800">{degisim:+.2f}%</span><span style="font-size:10px; color:#8b949e">{isim}</span><span style="font-weight:600">{last:,.2f}</span></div>'
    except: continue
ticker_content += '</div></div>'
st.markdown(ticker_content, unsafe_allow_html=True)
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# 4. FULL BIST LİSTESİ (SABİT)
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])
# ==========================================
# 5. ARAYÜZ VE ANALİZ
# ==========================================
st.markdown("<h1 style='text-align: center; color:#00ff41;'>🏛️ BIST QUANTUM TERMINAL</h1>", unsafe_allow_html=True)

with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    with c1: s_hisse = st.selectbox("Varlık Ara", BIST_FULL, label_visibility="collapsed")
    with c2: s_adet = st.number_input("Adet", min_value=0.0, step=1.0, label_visibility="collapsed")
    with c3: s_maliyet = st.number_input("Maliyet", min_value=0.0, label_visibility="collapsed")
    with c4: 
        if st.button("🚀 EKLE", use_container_width=True):
            st.session_state.portfoy.append({"Hisse": s_hisse, "Adet": s_adet, "Maliyet": s_maliyet})
            save_data(st.session_state.portfoy)
            st.rerun()

tab_p, tab_g, tab_s, tab_t = st.tabs(["📊 PORTFÖY", "📈 K/Z ANALİZ", "🤖 SİNYALLER", "💰 TEMETTÜ"])

if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            current = tk.fast_info['lastPrice']
            
            # RSI Basit Hesaplama
            hist = tk.history(period="1mo")
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
            signal = "🟢 AL" if rsi < 35 else "🔴 SAT" if rsi > 70 else "⚪ TUT"
            
            kz = (current - item['Maliyet']) * item['Adet']
            p_data.append({
                "Hisse": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": current, "Değer": item['Adet'] * current, "K/Z": kz,
                "RSI": rsi, "Sinyal": signal, 
                "Net_Temettü": (tk.info.get('dividendRate', 0) or 0) * 0.90 * item['Adet']
            })
        except: continue
    
    df = pd.DataFrame(p_data)

    with tab_p:
        st.metric("PORTFÖY BÜYÜKLÜĞÜ", f"{df['Değer'].sum():,.2f} ₺", f"{df['K/Z'].sum():,.2f} ₺ K/Z")
        st.dataframe(df[['Hisse', 'Adet', 'Maliyet', 'Güncel', 'Değer', 'K/Z']], use_container_width=True, hide_index=True)
        if st.button("🗑️ Portföyü Temizle"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()

    with tab_g:
        if not df.empty:
            st.bar_chart(df.set_index('Hisse')['K/Z'], color="#00ff41")

    with tab_s:
        for _, row in df.iterrows():
            st.markdown(f'<div class="signal-box"><b>{row["Hisse"]}</b>: {row["Sinyal"]} (RSI: {row["RSI"]:.2f})</div>', unsafe_allow_html=True)

    with tab_t:
        st.metric("Yıllık Net Temettü Beklentisi", f"{df['Net_Temettü'].sum():,.2f} ₺")
        st.dataframe(df[['Hisse', 'Adet', 'Net_Temettü']], use_container_width=True, hide_index=True)
else:
    st.info("Portföyünüz boş.")

st.caption(f"Veriler yfinance üzerinden 15sn periyotla güncellenir. Son: {datetime.now().strftime('%H:%M:%S')}")
