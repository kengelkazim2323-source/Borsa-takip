import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
import pytz
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. VERİ YÖNETİMİ & OTOMATİK YENİLEME
# ==========================================
PORTFOY_DOSYASI = "portfoy_kayitlari.json"

def load_data():
    if not os.path.exists(PORTFOY_DOSYASI):
        return []
    try:
        with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content) if content else []
    except: return []

def save_data(data):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="terminal_refresh")
except: pass

# ==========================================
# 2. TEMA VE AYARLAR (SIDEBAR)
# ==========================================
st.set_page_config(page_title="BORSA ASLANI", page_icon="🦁", layout="wide")

with st.sidebar:
    st.markdown("<h2 style='color:#00ff41;'>⚙️ TERMİNAL AYARLARI</h2>", unsafe_allow_html=True)
    tema_secimi = st.selectbox("Renk Teması Seç", ["Matrix Green", "Cyber Blue", "Volcanic Red"])
    st.divider()
    st.info("Adet ve Maliyet kısımlarına rakam girip 'EKLE' butonuna basın.")

themes = {
    "Matrix Green": {"color": "#00ff41", "bg": "#05070a", "glow": "rgba(0,255,65,0.3)"},
    "Cyber Blue": {"color": "#00d4ff", "bg": "#010b13", "glow": "rgba(0,212,255,0.3)"},
    "Volcanic Red": {"color": "#ff3131", "bg": "#0a0505", "glow": "rgba(255,49,49,0.3)"}
}
main_color = themes[tema_secimi]["color"]
bg_color = themes[tema_secimi]["bg"]

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ margin-top: -80px; background-color: {bg_color}; }} 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] {{ font-family: 'JetBrains Mono', monospace; color: #e6edf3; }}
    .ticker-wrapper {{ width: 100%; overflow-x: auto; background: rgba(13, 17, 23, 0.95); border-bottom: 1px solid {main_color}; position: fixed; top: 0; left: 0; right: 0; z-index: 9999; backdrop-filter: blur(10px); }}
    .ticker-container {{ display: flex; padding: 12px 20px; gap: 40px; width: max-content; }}
    .up {{ color: {main_color}; }} .down {{ color: #ff3131; }}
    .stMetric {{ background: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }}
    .signal-box {{ background: #0d1117; border-left: 4px solid {main_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #30363d; }}
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. PİYASA AKIŞI (ÜST BANT)
# ==========================================
piyasa_izleme = {"BIST 100": "XU100.IS", "GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X", "ONS ALTIN": "GC=F", "BITCOIN": "BTC-USD"}
ticker_content = f'<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        last = tk.fast_info['lastPrice']
        prev = tk.fast_info['regularMarketPreviousClose']
        degisim = ((last - prev) / prev) * 100
        ticker_content += f'<div style="display:flex; flex-direction:column; align-items:center; border-right: 1px solid #30363d; padding-right:20px;"><span class="{"up" if degisim>=0 else "down"}" style="font-weight:800">{degisim:+.2f}%</span><span style="font-size:10px; color:#8b949e">{isim}</span><span style="font-weight:600">{last:,.2f}</span></div>'
    except: continue
st.markdown(ticker_content + '</div></div><br><br><br><br>', unsafe_allow_html=True)

# ==========================================
# 4. FULL BIST LİSTESİ
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

# ==========================================
# 5. GİRİŞ PANELİ (ETİKETLİ & FORMATLI)
# ==========================================
st.markdown(f"<h1 style='text-align: center; color:{main_color}; font-size: 50px;'>🦁 BORSA ASLANI</h1>", unsafe_allow_html=True)

with st.container():
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    with c1: s_hisse = st.selectbox("Varlık Seçin", BIST_FULL)
    with c2: s_adet_raw = st.text_input("Adet", placeholder="Örn: 100")
    with c3: s_maliyet_raw = st.text_input("Maliyet", placeholder="Örn: 45.50")
    with c4: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 EKLE", use_container_width=True):
            try:
                if s_adet_raw and s_maliyet_raw:
                    st.session_state.portfoy.append({
                        "Hisse": s_hisse, 
                        "Adet": float(s_adet_raw.replace(",", ".")), 
                        "Maliyet": float(s_maliyet_raw.replace(",", "."))
                    })
                    save_data(st.session_state.portfoy)
                    st.rerun()
            except: st.error("Rakam girin!")

tab_p, tab_g, tab_s = st.tabs(["📊 PORTFÖY", "📈 KAR-ZARAR ANALİZİ", "🤖 SİNYALLER"])

if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            curr = tk.fast_info['lastPrice']
            kz = (curr - item['Maliyet']) * item['Adet']
            h = tk.history(period="1mo")
            d = h['Close'].diff(); g = (d.where(d > 0, 0)).rolling(14).mean(); l = (-d.where(d < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (g/l))).iloc[-1]
            p_data.append({
                "Hisse": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": curr, "Değer": item['Adet'] * curr, "K/Z": kz, "RSI": rsi
            })
        except: continue
    
    df = pd.DataFrame(p_data)

    with tab_p:
        # Metriklerde 2 basamak formatı
        st.metric("TOPLAM PORTFÖY", f"{df['Değer'].sum():,.2f} ₺", f"{df['K/Z'].sum():,.2f} ₺ K/Z")
        
        # Tablo içinde 2 basamak formatı (column_config ile)
        st.dataframe(df[['Hisse', 'Adet', 'Maliyet', 'Güncel', 'Değer', 'K/Z']], 
                     use_container_width=True, 
                     hide_index=True,
                     column_config={
                         "Adet": st.column_config.NumberColumn(format="%.2f"),
                         "Maliyet": st.column_config.NumberColumn(format="%.2f"),
                         "Güncel": st.column_config.NumberColumn(format="%.2f"),
                         "Değer": st.column_config.NumberColumn(format="%.2f"),
                         "K/Z": st.column_config.NumberColumn(format="%.2f")
                     })
        
        if st.button("🗑️ Tümünü Temizle"):
            st.session_state.portfoy = []; save_data([]); st.rerun()

    with tab_g:
        if not df.empty:
            df['Renk'] = df['K/Z'].apply(lambda x: 'Kâr' if x >= 0 else 'Zarar')
            fig = px.bar(df, x='Hisse', y='K/Z', color='Renk', 
                         color_discrete_map={'Kâr': '#00ff41', 'Zarar': '#ff3131'},
                         title="Kar-Zarar Dağılımı")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)

    with tab_s:
        for _, r in df.iterrows():
            sig = "🟢 AL" if r['RSI'] < 35 else "🔴 SAT" if r['RSI'] > 70 else "⚪ TUT"
            st.markdown(f'<div class="signal-box"><b>{r["Hisse"]}</b>: {sig} (RSI: {r["RSI"]:.2f})</div>', unsafe_allow_html=True)
else:
    st.info("Portföy boş.")

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"Veriler 15sn'de bir güncellenir. Son Güncelleme: {tr_saati}")
