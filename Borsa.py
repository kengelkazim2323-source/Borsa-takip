import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from streamlit_javascript import st_javascript
from datetime import datetime
import numpy as np

# ==========================================
# 1. AYARLAR & PREMIUM TASARIM 
# ==========================================
st.set_page_config(page_title="Borsa kuşu v10.1", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Genel Font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    /* Üst Panel Özel Fontu (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;900&display=swap');
    
    html, body, [class*="st-"] { font-family: 'JetBrains Mono', monospace; background-color: #0d1117; }
    
    /* YENİ ÜST PANEL TASARIMI (Buzlu Cam & Animasyon) */
    .top-ticker { 
        background: rgba(22, 27, 34, 0.4); 
        backdrop-filter: blur(10px); 
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-radius: 12px; 
        padding: 20px 10px; 
        text-align: center; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2); 
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .top-ticker:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
    }
    .top-ticker.up { border-top: 4px solid #3fb950; }
    .top-ticker.down { border-top: 4px solid #f85149; }
    
    .top-ticker h3 { 
        font-family: 'Inter', sans-serif !important; 
        font-size: 0.9rem; 
        color: #8b949e !important; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        margin-bottom: 10px;
    }
    .top-ticker p { 
        font-family: 'Inter', sans-serif !important; 
        font-size: 1.6rem; 
        font-weight: 900; 
        color: #ffffff; 
        margin: 0;
        text-shadow: 0 0 15px rgba(255,255,255,0.1);
    }
    .ticker-change {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        margin-top: 8px;
        display: inline-block;
    }
    .change-up { background-color: rgba(63, 185, 80, 0.15); color: #3fb950; }
    .change-down { background-color: rgba(248, 81, 73, 0.15); color: #f85149; }
    
    /* Form ve Kartlar */
    div[data-testid="stForm"] { border: 1px solid #1f6feb !important; border-radius: 12px; background-color: #161b22; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px !important; }
    .news-card { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-bottom: 8px; border: 1px solid #30363d; }
    .signal-card { background: #1c2128; border: 1px solid #58a6ff; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    
    /* Gizli Sidebar */
    [data-testid="collapsedControl"] { display: none; }
    
    h1, h2, h3 { color: #58a6ff !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- KALICI HAFIZA ---
def load_permanent_data():
    js_get = "localStorage.getItem('kral_v10_data');"
    res = st_javascript(js_get)
    if res and res != "null": return json.loads(res)
    return None

def save_permanent_data(data):
    js_set = f"localStorage.setItem('kral_v10_data', '{json.dumps(data)}');"
    st_javascript(js_set)

if 'portfoy' not in st.session_state:
    stored = load_permanent_data()
    st.session_state.portfoy = stored if stored else []

# ==========================================
# 2. YENİ PİYASA PANELİ (GLASSMORPHISM)
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>🏛️ İMPARATOR YATIRIM TERMİNALİ</h1>", unsafe_allow_html=True)

piyasa_hisseleri = {"DOLAR": "USDTRY=X", "ONS ALTIN": "GC=F", "GÜMÜŞ": "SI=F", "BIST 100": "XU100.IS", "BITCOIN": "BTC-USD"}
usd_kur = 33.0 
cols = st.columns(len(piyasa_hisseleri))

for i, (isim, sembol) in enumerate(piyasa_hisseleri.items()):
    try:
        t_obj = yf.Ticker(sembol)
        fiyat = t_obj.fast_info['lastPrice']
        prev = t_obj.fast_info['regularMarketPreviousClose']
        degisim = ((fiyat - prev) / prev) * 100
        if isim == "DOLAR": usd_kur = fiyat
        
        yon_class = "up" if degisim >= 0 else "down"
        change_class = "change-up" if degisim >= 0 else "change-down"
        ok = "▲" if degisim >= 0 else "▼"
        
        with cols[i]:
            st.markdown(f"""
            <div class="top-ticker {yon_class}">
                <h3>{isim}</h3>
                <p>{fiyat:,.2f}</p>
                <div class="ticker-change {change_class}">{ok} %{abs(degisim):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    except: continue

st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# 3. ANA EKRANDA VARLIK GİRİŞİ 
# ==========================================
BIST_FULL = sorted([
    "A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"
])
GLOBAL_LIST = ["AAPL", "TSLA", "NVDA", "AMZN", "BTC-USD", "ETH-USD"]
TUM_LISTE = sorted(list(set(BIST_FULL + GLOBAL_LIST)))

with st.form("portfoy_giris_formu"):
    st.write("### ➕ Varlık Yönetimi")
    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
    secilen = c1.selectbox("Varlık Seç (Ara):", TUM_LISTE)
    adet = c2.number_input("Adet:", min_value=0.0, step=1.0)
    maliyet = c3.number_input("Maliyet:", min_value=0.0, format="%.3f")
    ekle_btn = c4.form_submit_button("🚀 Portföye Ekle")
    temizle_btn = c5.form_submit_button("🗑️ Hepsini Sil")

    if ekle_btn:
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet})
        save_permanent_data(st.session_state.portfoy)
        st.success("Eklendi!")
        st.rerun()
    if temizle_btn:
        st.session_state.portfoy = []
        save_permanent_data([])
        st.rerun()

# ==========================================
# 4. TEKNİK ANALİZ FONKSİYONU
# ==========================================
def get_technical_signals(symbol):
    try:
        data = yf.Ticker(symbol).history(period="3mo")
        if len(data) < 50: return "Veri Yetersiz", "⚪ Nötr"
        
        close = data['Close']
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        trend = "🟢 Yükseliş Trendi (SMA20 > SMA50)" if sma20 > sma50 else "🔴 Düşüş Trendi (SMA20 < SMA50)"
        
        if rsi > 70: rsi_durum = f"🔥 Aşırı Alım / Riskli (RSI: {rsi:.1f})"
        elif rsi < 30: rsi_durum = f"💎 Aşırı Satım / Fırsat (RSI: {rsi:.1f})"
        else: rsi_durum = f"⚪ Nötr Bölge (RSI: {rsi:.1f})"
        
        return trend, rsi_durum
    except:
        return "Hata", "Hata"

# ==========================================
# 5. MERKEZİ ANALİZ SEKMELERİ
# ==========================================
t1, t2, t3, t4 = st.tabs(["📊 Portföy", "💵 Dolar Bazlı", "🎯 Teknik Sinyaller", "📰 Haberler & İstihbarat"])

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
        with col2:
            st.plotly_chart(px.pie(df, values='Değer', names='Varlık', hole=0.5, template="plotly_dark"), use_container_width=True)
        st.dataframe(df.style.format({"Maliyet": "{:.2f}", "Güncel": "{:.2f}", "Değer": "{:,.2f}", "K/Z": "{:,.2f}"}), use_container_width=True)

    with t2:
        st.metric("Toplam USD Değer", f"${(t_deger/usd_kur):,.2f}")
        st.plotly_chart(px.bar(df, x='Varlık', y='USD_KZ', color='USD_KZ', color_continuous_scale='RdYlGn', template="plotly_dark"), use_container_width=True)

    with t3:
        st.subheader("🎯 Portföyündeki Hisselerin Teknik Analizi")
        st.info("Algoritma son 3 aylık veriler üzerinden RSI(14) ve Hareketli Ortalamaları (SMA20-SMA50) hesaplar.")
        
        for item in st.session_state.portfoy:
            trend, rsi_durum = get_technical_signals(item['Hisse'])
            st.markdown(f"""
            <div class="signal-card">
                <h4 style='margin:0; color:#c9d1d9;'>{item['Hisse']}</h4>
                <p style='margin:5px 0 0 0;'><b>Trend Sinyali:</b> {trend}</p>
                <p style='margin:0;'><b>Momentum (RSI):</b> {rsi_durum}</p>
            </div>
            """, unsafe_allow_html=True)

else:
    with t1: st.info("Yukarıdaki formdan portföyünüze varlık ekleyin.")

with t4:
    col_news, col_surge = st.columns([2, 1])
    
    with col_surge:
        st.subheader("⚡ Hacim Radarı")
        st.caption("Tüm piyasada olağandışı hacim taraması (Top 20)")
        for s in TUM_LISTE[:20]:
            try:
                h_hist = yf.Ticker(s).history(period="5d")
                if len(h_hist) >= 2:
                    v_avg = h_hist['Volume'].iloc[:-1].mean()
                    v_now = h_hist['Volume'].iloc[-1]
                    if v_now > v_avg * 1.5:
                        st.markdown(f"<div style='background:#21262d; border:1px solid #d29922; padding:10px; border-radius:8px; color:#e3b341; margin-bottom:5px;'>🔥 <b>{s}</b> Hacim Patlaması!</div>", unsafe_allow_html=True)
            except: continue
            
    with col_news:
        st.subheader("📢 Piyasa Gündemi")
        h_symbol = st.session_state.portfoy[0]['Hisse'] if st.session_state.portfoy else "XU100.IS"
        try:
            raw_news = yf.Ticker(h_symbol).news
            if not raw_news: raw_news = yf.Ticker("XU100.IS").news
            for n in raw_news[:8]:
                st.markdown(f"""<div class="news-card">
                <small style='color:#8b949e;'>{datetime.fromtimestamp(n.get('providerPublishTime', 0)).strftime('%H:%M')}</small> | <b>{n.get('publisher')}</b><br>
                <a href="{n.get('link')}" target="_blank" style='text-decoration:none; color:#58a6ff; font-weight:bold;'>{n.get('title')}</a>
                </div>""", unsafe_allow_html=True)
        except: st.error("Haberlere ulaşılamıyor.")
