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
# 0. YARDIMCI FONKSİYONLAR
# ==========================================
def tr_format(val):
    try:
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

# ==========================================
# 1. VERİ YÖNETİMİ (KAYBOLMAYI ENGELLER)
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

# ==========================================
# 2. TEMA VE SAAT (BEYAZ TEMA & SAĞ ÜST)
# ==========================================
st.set_page_config(page_title="BORSA ASLANI", page_icon="🦁", layout="wide")
st_autorefresh(interval=1000, key="datarefresh")

main_color = "#1a73e8"
bg_color = "#ffffff"

tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: {bg_color}; }} 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] {{ font-family: 'JetBrains Mono', monospace; color: #202124; }}
    .top-right-clock {{ 
        position: fixed; top: 0px; right: 0px; color: #ffffff; font-weight: bold; font-size: 20px; 
        z-index: 9999; padding: 10px 25px; background: linear-gradient(135deg, #202124 0%, #3c4043 100%);
        border-bottom-left-radius: 15px; box-shadow: -2px 2px 10px rgba(0,0,0,0.2);
        letter-spacing: 2px; border-left: 3px solid {main_color};
    }}
    .ticker-wrapper {{ width: 100%; overflow-x: auto; background: #f8f9fa; border-bottom: 2px solid #e8eaed; margin-bottom: 20px; }}
    .ticker-container {{ display: flex; padding: 10px 15px; gap: 30px; width: max-content; }}
    .up {{ color: #137333; font-weight: bold; }} .down {{ color: #d93025; font-weight: bold; }}
    .stMetric {{ background: #ffffff; border: 1px solid #dadce0; padding: 15px; border-radius: 12px; }}
    </style>
    <div class="top-right-clock">🕒 {tr_saati}</div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. PİYASA BANDI
# ==========================================
piyasa_izleme = {"GRAM ALTIN": "GAU-TRY", "GÜMÜŞ TRY": "GAG-TRY", "ONS ALTIN": "GC=F", "BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X"}
ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        hist = tk.history(period="2d")
        if not hist.empty:
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            degisim = ((last - prev) / prev) * 100
            ticker_content += f'<div style="text-align:center; border-right:1px solid #e8eaed; padding-right:20px;"><div style="font-size:10px; color:#5f6368">{isim}</div><div style="font-weight:bold;">{tr_format(last)}</div><div class="{"up" if degisim >= 0 else "down"}" style="font-size:11px;">{degisim:+.2f}%</div></div>'
    except: continue
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. TÜM BİST HİSSELERİ VE EKLEME
# ==========================================
# Tüm BİST hisselerini içeren geniş liste (A-Z)
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

st.markdown(f"<h2 style='text-align: center; color:{main_color};'>🦁 BORSA ASLANI</h2>", unsafe_allow_html=True)

with st.expander("➕ Yeni Varlık Ekle", expanded=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: s_varlik = st.selectbox("Hisse/Varlık Seç", BIST_FULL)
    with c2: s_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    with c3: s_maliyet = st.number_input("Maliyet", min_value=0.0, format="%.2f")
    if st.button("🚀 PORTFÖYE EKLE", use_container_width=True):
        if s_varlik and s_adet > 0:
            st.session_state.portfoy.append({"Hisse": s_varlik, "Adet": s_adet, "Maliyet": s_maliyet})
            save_data(st.session_state.portfoy)
            st.rerun()

# ==========================================
# 5. VERİ İŞLEME VE TEMETTÜ HESABI
# ==========================================
if st.session_state.portfoy:
    p_data = []
    for item in st.session_state.portfoy:
        try:
            tk = yf.Ticker(item['Hisse'])
            curr = tk.history(period="1d")['Close'].iloc[-1]
            kz = (curr - float(item['Maliyet'])) * float(item['Adet'])
            
            # --- Temettü Hesaplama ---
            info = tk.info
            div_yield = info.get('dividendYield', 0) # Verim (örn: 0.05)
            div_rate = info.get('dividendRate', 0)   # Hisse başı TL
            
            # Eğer dividendRate yoksa verim üzerinden tahmini TL hesapla
            if not div_rate and div_yield:
                div_rate = curr * div_yield
                
            yillik_temettu = (div_rate or 0) * float(item['Adet'])
            
            p_data.append({
                "Varlık": item['Hisse'], "Adet": item['Adet'], "Maliyet": item['Maliyet'],
                "Güncel": curr, "Değer": item['Adet'] * curr, "K/Z": kz,
                "Tahmini Yıllık Temettü": yillik_temettu
            })
        except: continue
    
    df = pd.DataFrame(p_data)

    tab_p, tab_t, tab_g = st.tabs(["📊 PORTFÖYÜM", "💰 TEMETTÜ GELİRİ", "📈 DAĞILIM"])

    with tab_p:
        m1, m2 = st.columns(2)
        m1.metric("TOPLAM PORTFÖY", f"{tr_format(df['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺", delta=f"{tr_format(df['K/Z'].sum())}")
        df_disp = df.copy()
        for col in ['Maliyet', 'Güncel', 'Değer', 'K/Z', 'Tahmini Yıllık Temettü']:
            df_disp[col] = df_disp[col].apply(tr_format)
        st.dataframe(df_disp.drop(columns=["Tahmini Yıllık Temettü"]), use_container_width=True, hide_index=True)

    with tab_t:
        total_div = df['Tahmini Yıllık Temettü'].sum()
        st.markdown(f"### 💵 Toplam Tahmini Yıllık Gelir: **{tr_format(total_div)} ₺**")
        st.markdown(f"#### 📅 Aylık Ortalama: **{tr_format(total_div/12)} ₺**")
        st.write("---")
        t_df = df[df['Tahmini Yıllık Temettü'] > 0][["Varlık", "Tahmini Yıllık Temettü"]]
        if not t_df.empty:
            st.table(t_df.style.format({"Tahmini Yıllık Temettü": "{:,.2f} ₺"}))
        else:
            st.warning("Portföyündeki hisselerin güncel temettü verisi bulunamadı.")

    with tab_g:
        fig = px.pie(df, values='Değer', names='Varlık', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🗑️ Portföyü Sıfırla"):
        st.session_state.portfoy = []
        save_data([])
        st.rerun()
else:
    st.info("Portföy boş kral, ekleme yapmanı bekliyorum.")
