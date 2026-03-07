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
# 0. SAYI FORMATLAMA VE GELİŞMİŞ TEKNİK ANALİZ
# ==========================================
def tr_format(val):
    try:
        if val is None or pd.isna(val): return "0,00"
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

def get_signal(data):
    try:
        if data is None or len(data) < 35: return "YETERSİZ VERİ"
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        last_price = data['Close'].iloc[-1]
        buy_score = 0
        if rsi < 45: buy_score += 1
        if macd.iloc[-1] > signal_line.iloc[-1]: buy_score += 1
        if last_price > ma20: buy_score += 1
        sell_score = 0
        if rsi > 65: sell_score += 1
        if macd.iloc[-1] < signal_line.iloc[-1]: sell_score += 1
        if last_price < ma20: sell_score += 1
        if buy_score >= 2: return "🔥 GÜÇLÜ AL" if buy_score == 3 else "🟢 AL"
        elif sell_score >= 2: return "📉 GÜÇLÜ SAT" if sell_score == 3 else "🔴 SAT"
        else: return "🟡 TUT"
    except: return "⚠️ ANALİZ YOK"

# ==========================================
# 1. VERİ YÖNETİMİ
# ==========================================
PORTFOY_DOSYASI = "portfoy_kayitlari.json"
def load_data():
    if not os.path.exists(PORTFOY_DOSYASI): return []
    try:
        with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def save_data(data):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_data()

# ==========================================
# 2. GÖRSEL AYARLAR VE SAAT
# ==========================================
st.set_page_config(page_title="BORSA TAKİP", page_icon="📈", layout="wide")
st_autorefresh(interval=500, key="datarefresh")
main_color = "#1a73e8"
tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #ffffff; }} 
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="st-"] {{ font-family: 'JetBrains Mono', monospace; }}
    .top-right-clock {{ 
        position: fixed; top: 0px; right: 0px; color: #ffffff; font-weight: bold; font-size: 18px; 
        z-index: 9999; padding: 12px 20px; background: #202124;
        border-bottom-left-radius: 12px; border-left: 4px solid {main_color};
    }}
    .ticker-wrapper {{ width: 100%; overflow-x: auto; background: #f1f3f4; border-bottom: 1px solid #dadce0; margin-bottom: 25px; }}
    .ticker-container {{ display: flex; padding: 12px; gap: 40px; width: max-content; }}
    .up {{ color: #137333; font-weight: 700; }} .down {{ color: #d93025; font-weight: 700; }}
    </style>
    <div class="top-right-clock">🕒 {tr_saati}</div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. PİYASA BANDI
# ==========================================
piyasa_izleme = {"BIST 100": "XU100.IS", "GRAM ALTIN": "GAU-TRY", "ONS ALTIN": "GC=F", "ONS GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X"}
ticker_content = '<div class="ticker-wrapper"><div class="ticker-container">'
for isim, sembol in piyasa_izleme.items():
    try:
        tk = yf.Ticker(sembol)
        hist = tk.history(period="2d")
        if not hist.empty:
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            degisim = ((last - prev) / prev) * 100
            ticker_content += f'<div style="text-align:center;"><div style="font-size:11px; color:#5f6368">{isim}</div><div style="font-size:15px; font-weight:bold;">{tr_format(last)}</div><div class="{"up" if degisim >= 0 else "down"}" style="font-size:11px;">{degisim:+.2f}%</div></div>'
    except: continue
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 4. TAM BİST LİSTESİ (SABİT)
# ==========================================
BIST_FULL = sorted(["A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"])

st.markdown(f"<h2 style='text-align:center; color:{main_color}; margin-top:-20px;'>📈 BORSA TAKİP</h2>", unsafe_allow_html=True)

with st.container():
    col_v, col_a, col_m = st.columns([2, 1, 1])
    with col_v: s_varlik = st.selectbox("Hisse Seç", BIST_FULL)
    with col_a: s_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    with col_m: s_maliyet = st.number_input("Maliyet (₺)", min_value=0.0, format="%.2f")
    if st.button("🚀 PORTFÖYE EKLE", use_container_width=True):
        if s_varlik and s_adet > 0:
            st.session_state.portfoy.append({"Hisse": s_varlik, "Adet": s_adet, "Maliyet": s_maliyet})
            save_data(st.session_state.portfoy)
            st.rerun()

# ==========================================
# 5. ANALİZ VE TEMETTÜ HESABI
# ==========================================
if st.session_state.portfoy:
    p_data = []
    total_daily_gain = 0
    for item in st.session_state.portfoy:
        curr, d_pct, d_tl, val, kz, signal, n_temettu, t_verimi = 0.0, 0.0, 0.0, 0.0, 0.0, "🔴 VERİ YOK", 0.0, 0.0
        try:
            tk = yf.Ticker(item['Hisse'])
            hist = tk.history(period="60d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                adet = float(item['Adet'])
                d_pct = ((curr - prev) / prev) * 100
                d_tl = (curr - prev) * adet
                val = adet * curr
                kz = (curr - float(item['Maliyet'])) * adet
                signal = get_signal(hist)
                
                # Temettü hesaplama (son 1 yıl toplamı)
                divs = tk.dividends
                if not divs.empty:
                    divs.index = divs.index.tz_localize(None)
                    hisse_basi_toplam = divs[divs.index > (datetime.now() - timedelta(days=365))].sum()
                    n_temettu = hisse_basi_toplam * adet
                    # Temettü Verimi Getirisi (Hisse Başı Temettü / Güncel Fiyat)
                    if curr > 0:
                        t_verimi = (hisse_basi_toplam / curr) * 100
                
                total_daily_gain += d_tl
        except: pass
        p_data.append({
            "Varlık": item['Hisse'], 
            "Sinyal": signal, 
            "Adet": item['Adet'], 
            "Güncel": curr, 
            "Günlük (%)": d_pct, 
            "Günlük Fark (₺)": d_tl, 
            "Değer": val, 
            "K/Z": kz, 
            "Net Temettü": n_temettu,
            "Temettü Verimi (%)": t_verimi
        })

    df = pd.DataFrame(p_data)
    if not df.empty:
        t1, t2, t3 = st.tabs(["📊 PORTFÖY", "📈 ANALİZ", "💰 TEMETTÜ"])
        with t1:
            m1, m2, m3 = st.columns(3)
            m1.metric("TOPLAM DEĞER", f"{tr_format(df['Değer'].sum())} ₺")
            m2.metric("TOPLAM K/Z", f"{tr_format(df['K/Z'].sum())} ₺")
            m3.metric("GÜNLÜK K/Z", f"{tr_format(total_daily_gain)} ₺", delta=f"{total_daily_gain:,.2f}")
            df_disp = df.drop(columns=['Net Temettü', 'Temettü Verimi (%)']).copy()
            df_disp["Günlük (%)"] = df_disp["Günlük (%)"].apply(lambda x: f"%{x:+.2f}")
            for c in ["Güncel", "Değer", "K/Z", "Günlük Fark (₺)"]: df_disp[c] = df_disp[c].apply(tr_format)
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        with t2:
            st.plotly_chart(px.pie(df, values='Değer', names='Varlık', hole=0.5), use_container_width=True)
        with t3:
            # KRALIN İSTEDİĞİ KISIM + GETİRİ HESABI:
            st.markdown(f"### 💰 Yıllık Tahmini Net Temettü: **{tr_format(df['Net Temettü'].sum())} ₺**")
            
            # Sadece temettü verenleri göster ve verim oranını ekle
            div_df = df[df['Net Temettü'] > 0][['Varlık', 'Adet', 'Net Temettü', 'Temettü Verimi (%)']].copy()
            if not div_df.empty:
                div_df['Net Temettü'] = div_df['Net Temettü'].apply(tr_format)
                div_df['Temettü Verimi (%)'] = div_df['Temettü Verimi (%)'].apply(lambda x: f"%{x:.2f}")
                st.dataframe(div_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Portföyündeki hisselerin son 1 yıllık temettü verisi bulunamadı.")

    if st.button("🗑️ TEMİZLE"): st.session_state.portfoy = []; save_data([]); st.rerun()


tr_saati = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
st.caption(f"🕒 Son Güncelleme: {tr_saati} | BIST Tam Liste Yüklendi.")


