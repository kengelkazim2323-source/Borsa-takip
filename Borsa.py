import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. UYGULAMA AYARLARI VE LOGO (FAVICON)
# ==========================================
# Buraya bir emoji veya bir resim linki koyabilirsin.
# Örnek resim linki: "https://marketplace.canva.com/EAGuCe94P4c/1/0/800w/canva-modern-ve-%C3%A7arp%C4%B1c%C4%B1-neon-sar%C4%B1-ve-siyah-gradyanl%C4%B1-finans-ekonomi-youtube-kanal%C4%B1-logosu-ap-NLSVYZlA.jpg"
APP_ICON = "👑" 

st.set_page_config(
    page_title="Borsa Portföy v4.0",
    page_icon=APP_ICON, # Tarayıcı sekmesindeki ikon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Koyu Mod stili (İsteğe bağlı, Streamlit ayarlarından da yapılabilir)
st.markdown("""
    <style>
    .stMetric { border-radius: 10px; background-color: #f0f2f6; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HİSSE LİSTELERİ (BIST 100 + YABANCI)
# ==========================================
# BIST 100 Hisselerinin Tamamı (Alfabetik)
BIST100_LISTESI = sorted([
    "AEEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKCNS.IS", "AKFGY.IS", "AKGRT.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS",
    "ALFAS.IS", "ALGYO.IS", "ALKIM.IS", "ANACM.IS", "ANELE.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "AYDEM.IS", "AYGAZ.IS",
    "BAGFS.IS", "BERA.IS", "BEYAZ.IS", "BIMAS.IS", "BIZIM.IS", "BRISA.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS", "CCOLA.IS",
    "CEMTS.IS", "CIMSA.IS", "CONSE.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "DOKTA.IS", "DYOBY.IS", "EGEEN.IS", "EGGUB.IS",
    "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "FROTO.IS", "GARAN.IS", "GESAN.IS", "GLYHO.IS", "GSDHO.IS",
    "GUBRF.IS", "GWIND.IS", "HALKB.IS", "HEKTS.IS", "IPEKE.IS", "ISCTR.IS", "ISDMR.IS", "ISGYO.IS", "ISMEN.IS", "IZMDC.IS",
    "KARDM.IS", "KAYSE.IS", "KCHOL.IS", "KMPUR.IS", "KONTR.IS", "KORDS.IS", "KOZAL.IS", "KOZAA.IS", "KRDMD.IS", "MAVI.IS",
    "MGROS.IS", "MIATK.IS", "NETAS.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PENTA.IS", "PETKM.IS", "PGSUS.IS", "QUAGR.IS",
    "SAHOL.IS", "SASA.IS", "SELEC.IS", "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SNGYO.IS", "SOKM.IS", "TARKM.IS", "TAVHL.IS",
    "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TOASO.IS", "TRGYO.IS", "TSKB.IS", "TTKOM.IS", "TTRAK.IS", "TUPRS.IS",
    "TURSG.IS", "ULKER.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", "YEOTK.IS", "YKBNK.IS", "ZOREN.IS"
])

# Popüler Yabancı Hisseler ve Kriptolar
DIGER_LISTE = sorted([
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "NFLX",
    "BTC-USD", "ETH-USD"
])

TUM_VARLIKLAR = sorted(BIST100_LISTESI + DIGER_LISTE)

# ==========================================
# 3. VERİ DEPOLAMA VE KONTROL
# ==========================================
if 'portfoy' not in st.session_state:
    st.session_state.portfoy = []

# Dolar Kurunu Çekme Fonksiyonu
@st.cache_data(ttl=3600) # Saatte bir güncellenir
def get_usd_try():
    try:
        usdt_data = yf.Ticker("USDTRY=X")
        return usdt_data.fast_info['lastPrice']
    except:
        return 0

usd_try_rate = get_usd_try()

# ==========================================
# 4. YAN PANEL (GİRİŞ) VE UYGULAMA BAŞLIĞI
# ==========================================
st.title(f"{APP_ICON} İmparator Portföy Yönetimi v4.0")
st.markdown("---")

with st.sidebar:
    st.header("➕ Varlık Ekle")
    
    # Otomatik Tamamlamalı Arama Kutusu (BIST 100 Dahil!)
    secilen = st.selectbox("Varlık Ara/Seç:", options=TUM_VARLIKLAR, index=TUM_VARLIKLAR.index("THYAO.IS"))
    
    manuel = st.text_input("Listede yoksa kod gir (Örn: FROTO.IS):").upper()
    final_kod = manuel if manuel else secilen
    
    col_g1, col_g2 = st.columns(2)
    adet = col_g1.number_input("Adet:", min_value=0.0, step=1.0, value=10.0)
    maliyet = col_g2.number_input("Birim Maliyet:", min_value=0.0, step=0.1, value=100.0)
    
    if st.button("Portföye İşle"):
        st.session_state.portfoy.append({"Hisse": final_kod, "Adet": adet, "Maliyet": maliyet})
        st.success(f"{final_kod} Eklendi!")

# ==========================================
# 5. ANALİZ VE GÖRSELLEŞTİRME
# ==========================================
if st.session_state.portfoy:
    ekran_verisi = []
    total_cost = 0
    total_value = 0

    with st.spinner('Piyasa verileri güncelleniyor...'):
        for kalem in st.session_state.portfoy:
            try:
                hisse_obj = yf.Ticker(kalem['Hisse'])
                # Hızlı fiyat çekme
                guncel_f = hisse_obj.fast_info['lastPrice']
                
                m_toplam = kalem['Adet'] * kalem['Maliyet']
                d_toplam = kalem['Adet'] * guncel_f
                k_z = d_toplam - m_toplam
                yuzde = (k_z / m_toplam) * 100 if m_toplam > 0 else 0
                
                total_cost += m_toplam
                total_value += d_toplam

                ekran_verisi.append({
                    "Hisse": kalem['Hisse'],
                    "Adet": kalem['Adet'],
                    "Maliyet": round(kalem['Maliyet'], 2),
                    "Güncel": round(guncel_f, 2),
                    "Kâr/Zarar": round(k_z, 2),
                    "Değişim %": round(yuzde, 2),
                    "Toplam Değer": round(d_toplam, 2)
                })
            except:
                st.error(f"{kalem['Hisse']} verisi alınamadı!")

    if ekran_verisi:
        df = pd.DataFrame(ekran_verisi)
        genel_kz = total_value - total_cost
        genel_yuzde = (genel_kz / total_cost) * 100 if total_cost > 0 else 0

        # --- ÖZET METRİKLER VE DOLAR ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Toplam Varlık (TL)", f"{total_value:,.2f} TL")
        
        # Dolar Değeri
        total_usd = total_value / usd_try_rate if usd_try_rate > 0 else 0
        col2.metric("Toplam Varlık ($)", f"${total_usd:,.2f}", f"Kur: {usd_try_rate:.2f}")
        
        # Kar/Zarar Renklendirme
        delta_color = "normal" if genel_kz >= 0 else "inverse"
        col3.metric("Toplam Kâr/Zarar", f"{genel_kz:,.2f} TL", f"%{genel_yuzde:.2f}", delta_color=delta_color)
        
        col4.metric("Varlık Sayısı", len(df))

        st.markdown("---")

        # --- GRAFİKLER ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("🎯 Portföy Dağılımı")
            fig_pie = px.pie(df, values='Toplam Değer', names='Hisse', hole=0.5, 
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_g2:
            st.subheader("📊 Hisse Bazlı Performans")
            # Kâr/Zarar durumuna göre renk haritası
            df['Renk'] = df['Kâr/Zarar'].apply(lambda x: 'Kâr' if x >= 0 else 'Zarar')
            fig_bar = px.bar(df, x='Hisse', y='Kâr/Zarar', color='Renk',
                             color_discrete_map={'Kâr': '#2ecc71', 'Zarar': '#e74c3c'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- DETAYLI LİSTE VE GRAFİK ETKİLEŞİMİ ---
        st.subheader("📋 Detaylı Portföy Listesi")
        
        # Tabloda Renk Kuralları (Kâr > %10 Yeşil, Zarar < -%5 Kırmızı)
        def style_rows(row):
            try:
                # 'Değişim %' sütununu kontrol et
                change = float(row['Değişim %'])
                if change > 10.0:
                    return ['background-color: #d4edda'] * len(row) # Açık Yeşil
                elif change < -5.0:
                    return ['background-color: #f8d7da'] * len(row) # Açık Kırmızı
                else:
                    return [''] * len(row)
            except:
                return [''] * len(row)

        # Tabloyu stillerle göster
        st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True)

        # --- HİSSE DETAY GRAFİĞİ (SEÇİM) ---
        st.divider()
        st.subheader("📈 Hisse Detay Grafiği")
        secilen_hisse_grafik = st.selectbox("Grafiğini görmek istediğiniz hisseyi seçin:", df["Hisse"])
        
        if secilen_hisse_grafik:
            with st.spinner(f"{secilen_hisse_grafik} grafiği yükleniyor..."):
                h_obj = yf.Ticker(secilen_hisse_grafik)
                hist = h_obj.history(period="1mo") # Son 1 aylık veri
                
                if not hist.empty:
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines+markers', name='Kapanış'))
                    fig_line.update_layout(title=f"{secilen_hisse_grafik} - Son 1 Aylık Fiyat",
                                          xaxis_title="Tarih", yaxis_title="Fiyat (TL/$)")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.warning("Bu hisse için grafik verisi bulunamadı.")

        if st.button("🗑️ Portföyü Sıfırla"):
            st.session_state.portfoy = []
            st.rerun()
else:
    st.info("Sol taraftan varlık ekleyerek İmparator Portföyünü oluşturmaya başla!")
