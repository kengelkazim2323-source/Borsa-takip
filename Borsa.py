import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from streamlit_javascript import st_javascript

# ==========================================
# 1. AYARLAR & LOGO
# ==========================================
st.set_page_config(page_title="İmparator Portföy v5.5", page_icon="👑", layout="wide")

# --- KALICI HAFIZA MEKANİZMASI ---
def save_data(data):
    js_code = f"localStorage.setItem('kral_portfoy', '{json.dumps(data)}');"
    st_javascript(js_code)

def load_data():
    js_code = "localStorage.getItem('kral_portfoy');"
    stored_data = st_javascript(js_code)
    if stored_data:
        try:
            return json.loads(stored_data)
        except:
            return []
    return []

if 'portfoy' not in st.session_state:
    loaded = load_data()
    st.session_state.portfoy = loaded if loaded else []

# ==========================================
# 2. DEV HİSSE LİSTESİ (BIST 100 + EKSTRALAR)
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

YABANCI_LIST = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "BTC-USD", "ETH-USD"]
TUM_LISTE = sorted(BIST_FULL + YABANCI_LIST)

# ==========================================
# 3. YAN PANEL (GİRİŞ)
# ==========================================
with st.sidebar:
    st.header("👑 Borsa Menü")
    secilen = st.selectbox("Hisse Ara/Seç:", TUM_LISTE, index=TUM_LISTE.index("THYAO.IS"))
    adet = st.number_input("Adet:", min_value=0.0, step=1.0, value=1.0)
    maliyet = st.number_input("Birim Maliyet:", min_value=0.0, step=0.1, value=100.0)
    
    if st.button("📦 Portföye Ekle"):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet})
        save_data(st.session_state.portfoy)
        st.success(f"{secilen} Eklendi!")
        st.rerun()

    if st.button("🗑️ Tümünü Temizle"):
        st.session_state.portfoy = []
        save_data([])
        st.rerun()

# ==========================================
# 4. ANA PANEL
# ==========================================
st.title("📈 Borsa Portföy Yönetimi")

if st.session_state.portfoy:
    display_list = []
    t_maliyet = 0
    t_deger = 0

    with st.spinner('Piyasa verileri okunuyor...'):
        for item in st.session_state.portfoy:
            try:
                h = yf.Ticker(item['Hisse'])
                fiyat = h.fast_info['lastPrice']
                
                m_toplam = item['Adet'] * item['Maliyet']
                d_toplam = item['Adet'] * fiyat
                kz = d_toplam - m_toplam
                yuzde = (kz / m_toplam * 100) if m_toplam > 0 else 0
                
                t_maliyet += m_toplam
                t_deger += d_toplam
                
                display_list.append({
                    "Varlık": item['Hisse'],
                    "Adet": item['Adet'],
                    "Maliyet": item['Maliyet'],
                    "Güncel": round(fiyat, 2),
                    "Kâr/Zarar": round(kz, 2),
                    "Verim %": round(yuzde, 2),
                    "Toplam Değer": round(d_toplam, 2)
                })
            except:
                st.error(f"{item['Hisse']} verisi çekilemedi.")

    df = pd.DataFrame(display_list)

    # Özet Kartları
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Varlık", f"{t_deger:,.2f} TL")
    kz_genel = t_deger - t_maliyet
    c2.metric("Toplam Kâr/Zarar", f"{kz_genel:,.2f} TL", f"%{(kz_genel/t_maliyet*100 if t_maliyet>0 else 0):.2f}")
    c3.metric("Varlık Sayısı", len(df))

    st.markdown("---")

    # --- GRAFİK ALANI ---
    st.subheader("📊 Analiz Grafikleri")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        fig_pie = px.pie(df, values='Toplam Değer', names='Varlık', hole=0.4, title="Varlık Dağılımı")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g_col2:
        fig_bar = px.bar(df, x='Varlık', y='Kâr/Zarar', color='Varlık', title="Kâr/Zarar Dağılımı")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # --- TABLO ALANI ---
    st.subheader("📋 Detaylı Portföy Tablosu")
    
    def color_df(val):
        if isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''

    st.dataframe(
        df.style.applymap(color_df, subset=['Kâr/Zarar', 'Verim %']),
        use_container_width=True
    )

else:
    st.info("Henüz varlık eklemediniz. Sol menüden ilk hisseni ekleyerek başla!")

st.caption("Verileriniz tarayıcınızın hafızasında saklanır. Sayfa yenilense de kaybolmaz.")
