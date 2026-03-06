import streamlit as st
import yfinance as yf
import pandas as pd
import json
from streamlit_javascript import st_javascript
from datetime import datetime

# ==========================================
# 1. KRİTİK AYARLAR VE GİZLEME (CSS)
# ==========================================
st.set_page_config(page_title="BORSA TERMİNALİ", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Streamlit Gereksiz Arayüzü Yok Et */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -80px; } 

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }

    /* ÜST PANEL (TICKER) - YATAY KAYDIRMA */
    .ticker-wrapper {
        width: 100%; overflow-x: auto; background: #161b22; 
        border-bottom: 1px solid #30363d; position: fixed; 
        top: 0; left: 0; right: 0; z-index: 9999;
    }
    .ticker-container { display: flex; padding: 10px 20px; gap: 30px; width: max-content; }
    .ticker-card { display: flex; flex-direction: column; align-items: center; min-width: 80px; }
    
    .t-pct { font-size: 14px; font-weight: 900; margin-bottom: 2px; }
    .t-sym { font-size: 11px; font-weight: 700; color: #8b949e; text-transform: uppercase; }
    .t-price { font-size: 13px; font-weight: 600; color: #f0f6fc; margin-top: 2px; }
    
    .up { color: #3fb950; }
    .down { color: #f85149; }

    /* TAB VE KART TASARIMI */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 4px; padding: 10px 20px; }
    .signal-box { background: #1c2128; border-left: 5px solid #58a6ff; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ YÖNETİMİ ---
def load_data():
    res = st_javascript("localStorage.getItem('terminal_v12_data');")
    return json.loads(res) if res and res != "null" else []

def save_data(data):
    st_javascript(f"localStorage.setItem('terminal_v12_data', '{json.dumps(data)}');")

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. ÜST PANEL (CANLI AKIŞ)
# ==========================================
piyasa_izleme = {
    "BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "ONS ALTIN": "GC=F", 
    "BITCOIN": "BTC-USD", "EREĞLİ": "EREGL.IS", "GÜMÜŞ": "SI=F", "THY": "THYAO.IS", "NASDAQ": "^IXIC"
}

ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        info = tk.fast_info
        fiyat = info['lastPrice']
        degisim = ((fiyat - info['regularMarketPreviousClose']) / info['regularMarketPreviousClose']) * 100
        renk = "up" if degisim >= 0 else "down"
        isaret = "+" if degisim >= 0 else ""
        
        ticker_content += f'''
        <div class="ticker-card">
            <span class="t-pct {renk}">{isaret}{degisim:.2f}%</span>
            <span class="t-sym">{isim}</span>
            <span class="t-price">{fiyat:,.2f}</span>
        </div>'''
    except: continue
ticker_content += '</div></div>'
st.markdown(ticker_content, unsafe_allow_html=True)

st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# 3. ANA BAŞLIK VE GİRİŞ (TÜM HİSSELER)
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>🏛️ BORSA TERMİNALİ</h1>", unsafe_allow_html=True)

# Tüm BİST + Global Listesi
BIST_ALL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD", "AMZN"]
LISTE = sorted(list(set(BIST_ALL + GLOBAL_LIST)))

col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
with col1: s_hisse = st.selectbox("Hisse Ara", LISTE, label_visibility="collapsed")
with col2: s_adet = st.number_input("Adet", min_value=0.0, step=1.0, label_visibility="collapsed")
with col3: s_maliyet = st.number_input("Maliyet", min_value=0.0, label_visibility="collapsed")
with col4: 
    if st.button("🚀 EKLE", use_container_width=True):
        st.session_state.portfoy.append({"Hisse": s_hisse, "Adet": s_adet, "Maliyet": s_maliyet})
        save_data(st.session_state.portfoy)
        st.rerun()

# ==========================================
# 4. ANALİZ VE SEKME MANTIĞI
# ==========================================
tab_p, tab_s, tab_t = st.tabs(["📊 PORTFÖY", "🤖 AL-SAT ROBOTU", "💰 TEMETTÜ"])

if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            hist = tk.history(period="3mo")
            current = hist['Close'].iloc[-1]
            
            # Teknik Sinyal Hesaplama (RSI-14)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
            
            signal = "🟢 GÜÇLÜ AL" if rsi < 35 else "🔴 GÜÇLÜ SAT" if rsi > 70 else "⚪ TUT"
            
            # Temettü
            yield_val = tk.info.get('dividendYield', 0)
            
            p_data.append({
                "Hisse": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": current, "Değer": item['Adet'] * current,
                "K/Z": (current - item['Maliyet']) * item['Adet'],
                "RSI": rsi, "Sinyal": signal, "Temettü Verimi": f"%{yield_val*100:.2f}"
            })
        except: continue
    
    df = pd.DataFrame(p_data)

    with tab_p:
        st.metric("Toplam Portföy Değeri", f"{df['Değer'].sum():,.2f} ₺")
        st.dataframe(df[['Hisse', 'Adet', 'Maliyet', 'Güncel', 'Değer', 'K/Z']], use_container_width=True)
        if st.button("🗑️ Portföyü Sıfırla"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()

    with tab_s:
        st.caption("AI Analiz: RSI-14 ve Fiyat Momentumuna göre oluşturulmuştur.")
        for index, row in df.iterrows():
            st.markdown(f"""
            <div class="signal-box">
                <b>{row['Hisse']}</b> → {row['Sinyal']} <br>
                <small>RSI Değeri: {row['RSI']:.2f} | Güncel Fiyat: {row['Güncel']:.2f}</small>
            </div>
            """, unsafe_allow_html=True)

    with tab_t:
        st.subheader("Yıllık Tahmini Temettü Verimi")
        st.table(df[['Hisse', 'Temettü Verimi']])

else:
    st.info("Portföyünüz boş. Yukarıdan varlık ekleyerek başlayın.")
