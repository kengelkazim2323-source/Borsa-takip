import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from datetime import datetime
import numpy as np

# ==========================================
# 1. SİSTEM AYARLARI & GÖRÜNÜM (MOBİL UYUMLU CSS)
# ==========================================
st.set_page_config(page_title="BORSA TERMINAL", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Menüleri gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    .stApp { margin-top: -60px; } 

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }

    /* YENİ ÜST CANLI PİYASA ŞERİDİ (MOBİL İÇİN YATAY SCROLL) */
    .mini-ticker-wrapper {
        width: 100%;
        overflow-x: auto; /* Mobilde yana kaydırma sağlar */
        background: #161b22;
        border-bottom: 1px solid #30363d;
        position: fixed; top: 0; left: 0; right: 0;
        z-index: 1000;
        -ms-overflow-style: none; /* IE ve Edge scrollbar gizleme */
        scrollbar-width: none; /* Firefox scrollbar gizleme */
    }
    .mini-ticker-wrapper::-webkit-scrollbar { display: none; } /* Chrome/Safari scrollbar gizleme */
    
    .mini-ticker-container {
        display: flex;
        padding: 8px 15px;
        gap: 25px; /* Mobilde sıkışmayı önler */
        width: max-content;
    }
    .mini-item { 
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        min-width: 60px;
    }
    .mini-symbol { font-size: 11px; font-weight: 800; color: #8b949e; letter-spacing: 0.5px; }
    .mini-pct { font-size: 13px; font-weight: 800; margin: 2px 0; }
    .mini-price { font-size: 12px; font-weight: 600; color: #f0f6fc; }
    
    .mini-up { color: #3fb950; }
    .mini-down { color: #f85149; }

    /* KART VE TABLO DÜZENLEMELERİ */
    .stMetric { background: #161b22 !important; border: 1px solid #30363d !important; padding: 10px !important; border-radius: 8px !important; }
    div[data-testid="stExpander"] { border: none !important; background: transparent !important; }
    .signal-card { background: #1c2128; border-left: 4px solid #58a6ff; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .signal-buy { border-color: #3fb950; }
    .signal-sell { border-color: #f85149; }
    .signal-hold { border-color: #d29922; }
    
    /* Input alanlarını küçültme */
    .stTextInput input, .stSelectbox div { font-size: 13px !important; }
    
    /* İsim Değişikliği ve Logo */
    h1 { color: #ffffff !important; font-weight: 800 !important; letter-spacing: -1px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA ---
def load_data():
    res = st_javascript("localStorage.getItem('kral_borsa_data');")
    return json.loads(res) if res and res != "null" else []

def save_data(data):
    st_javascript(f"localStorage.setItem('kral_borsa_data', '{json.dumps(data)}');")

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. ÜST ŞERİT (YÜZDELİK ÜSTTE, FİYAT ALTTA)
# ==========================================
piyasa = {"USD/TRY": "USDTRY=X", "ONS ALTIN": "GC=F", "GÜMÜŞ": "SI=F", "BIST 100": "XU100.IS", "BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD"}
usd_kur = 33.0

ticker_html = '<div class="mini-ticker-wrapper"><div class="mini-ticker-container">'
for isim, sembol in piyasa.items():
    try:
        t = yf.Ticker(sembol)
        f = t.fast_info['lastPrice']
        p = t.fast_info['regularMarketPreviousClose']
        d = ((f - p) / p) * 100
        if isim == "USD/TRY": usd_kur = f
        
        cls = "mini-up" if d >= 0 else "mini-down"
        sign = "+" if d >= 0 else ""
        
        # Tasarım: Sembol -> Yüzde -> Fiyat
        ticker_html += f'''
        <div class="mini-item">
            <span class="mini-symbol">{isim}</span>
            <span class="mini-pct {cls}">{sign}{d:.2f}%</span>
            <span class="mini-price">{f:,.2f}</span>
        </div>
        '''
    except: continue
ticker_html += '</div></div>'

st.markdown(ticker_html, unsafe_allow_html=True)
st.markdown("<br><br><br>", unsafe_allow_html=True) # Üst bar boşluğu

# ==========================================
# 3. ANA PANEL & TÜM HİSSELER GİRİŞİ
# ==========================================
st.title("🏛️ BORSA TERMİNALİ")

# TAM BIST LİSTESİ (Entegrasyon)
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "AMZN", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"]
TUM_LISTE = sorted(list(set(BIST_FULL + GLOBAL_LIST)))

with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    secilen = c1.selectbox("Varlık Seç", TUM_LISTE, label_visibility="collapsed")
    adet = c2.number_input("Adet", min_value=0.0, step=1.0, label_visibility="collapsed")
    maliyet = c3.number_input("Maliyet", min_value=0.0, format="%.2f", label_visibility="collapsed")
    if c4.button("🚀 EKLE", use_container_width=True):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet})
        save_data(st.session_state.portfoy)
        st.rerun()

# ==========================================
# 4. TEKNİK AL-SAT RADARI (YAPAY ZEKA)
# ==========================================
def al_sat_analizi_yap(symbol):
    try:
        data = yf.Ticker(symbol).history(period="3mo")
        if len(data) < 25: return "Veri Yetersiz", "signal-hold"
        
        close = data['Close']
        sma20 = close.rolling(20).mean().iloc[-1]
        
        # RSI Hesaplama
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        fiyat = close.iloc[-1]

        # Sinyal Mantığı
        if rsi < 35 and fiyat > sma20:
            return f"🟢 GÜÇLÜ AL (RSI: {rsi:.1f} - Trend Yukarı)", "signal-buy"
        elif rsi < 30:
            return f"🟢 AL / DİP FIRSATI (RSI: {rsi:.1f})", "signal-buy"
        elif rsi > 70 and fiyat < sma20:
            return f"🔴 GÜÇLÜ SAT (RSI: {rsi:.1f} - Trend Kırıldı)", "signal-sell"
        elif rsi > 70:
            return f"🔴 SAT / ŞİŞMİŞ (RSI: {rsi:.1f})", "signal-sell"
        else:
            return f"⚪ TUT / İZLE (RSI: {rsi:.1f} - Yön Arıyor)", "signal-hold"
    except:
        return "Analiz Yapılamadı", "signal-hold"

# ==========================================
# 5. MERKEZİ SEKME YÖNETİMİ
# ==========================================
t1, t2, t3, t4 = st.tabs(["📊 PORTFÖY", "🤖 AL-SAT RADARI", "💰 TEMETTÜ", "📰 HABER"])

if st.session_state.portfoy:
    data = []
    t_maliyet, t_deger = 0, 0
    
    for item in st.session_state.portfoy:
        try:
            h = yf.Ticker(item['Hisse'])
            f = h.fast_info['lastPrice']
            
            # Temettü Verisini Çekme (Hızlı)
            try:
                temettu_orani = h.info.get('dividendYield', 0)
                temettu_str = f"%{(temettu_orani * 100):.2f}" if temettu_orani else "Yok"
            except:
                temettu_str = "Bilinmiyor"

            m_top = item['Adet'] * item['Maliyet']
            d_top = item['Adet'] * f
            
            data.append({
                "Varlık": item['Hisse'], 
                "Adet": item['Adet'], 
                "Maliyet": item['Maliyet'], 
                "Güncel": f, 
                "Değer": d_top, 
                "K/Z": d_top - m_top,
                "Temettü": temettu_str
            })
            t_maliyet += m_top; t_deger += d_top
        except: continue
        
    df = pd.DataFrame(data)

    with t1:
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Varlık", f"{t_deger:,.0f} ₺")
        m2.metric("Net K/Z", f"{(t_deger-t_maliyet):,.0f} ₺", f"%{((t_deger-t_maliyet)/t_maliyet*100):.2f}" if t_maliyet > 0 else "0")
        m3.metric("Dolar Karşılığı", f"${(t_deger/usd_kur):,.0f}")
        
        st.dataframe(df.drop(columns=['Temettü']).style.format({"Maliyet": "{:.2f}", "Güncel": "{:.2f}", "Değer": "{:,.0f}", "K/Z": "{:,.0f}"}), use_container_width=True)
        
        if st.button("🗑️ Terminali Sıfırla"):
            st.session_state.portfoy = []
            save_data([])
            st.rerun()

    with t2:
        st.subheader("Yapay Zeka Destekli Teknik Yönlendirme")
        st.caption("Algoritma hisselerinin Momentum (RSI) ve Hareketli Ortalamalarını (SMA20) kıyaslayarak sana yol gösterir.")
        
        for asset in df['Varlık'].unique():
            sinyal_metni, css_class = al_sat_analizi_yap(asset)
            st.markdown(f"""
            <div class="signal-card {css_class}">
                <strong style="font-size:16px;">{asset}</strong><br>
                <span>Durum: {sinyal_metni}</span>
            </div>
            """, unsafe_allow_html=True)

    with t3:
        st.subheader("💰 Pasif Gelir (Temettü) Durumu")
        st.caption("Portföyündeki hisselerin güncel yıllık temettü (kâr payı) verimlilikleri.")
        st.dataframe(df[['Varlık', 'Değer', 'Temettü']].style.format({"Değer": "{:,.0f} ₺"}), use_container_width=True)

    with t4:
        try:
            news = yf.Ticker("XU100.IS").news[:5]
            for n in news:
                st.markdown(f"**[{n['publisher']}]** {n['title']}  \n[Habere Git]({n['link']})")
                st.divider()
        except: st.write("Haber akışına şu an ulaşılamıyor.")

else:
    st.info("Portföy boş. Yukarıdan varlık ekleyerek başlayın.")
