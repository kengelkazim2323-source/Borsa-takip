import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Kral Portföy", layout="wide")

# 2. HİSSE LİSTESİ (Arama kutusunda çıkacak olanlar)
# Buraya istediğin kadar hisse ekleyebilirsin.
BIST_LISTESI = [
    "THYAO.IS", "ASELS.IS", "EREGL.IS", "SASA.IS", "KCHOL.IS", 
    "SISE.IS", "AKBNK.IS", "GARAN.IS", "TUPRS.IS", "BIMAS.IS", 
    "ISCTR.IS", "YKBNK.IS", "HEKTS.IS", "PGSUS.IS", "EKGYO.IS",
    "FROTO.IS", "TOASO.IS", "ARCLK.IS", "PETKM.IS", "KOZAL.IS"
]
YABANCI_LISTE = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META"]
TUM_HISSELER = sorted(BIST_LISTESI + YABANCI_LISTE)

# 3. UYGULAMA BAŞLIĞI
st.title("📈 Kral Portföy Yönetim Paneli")
st.markdown("---")

# 4. VERİ DEPOLAMA (Tarayıcı hafızası)
if 'portfoy' not in st.session_state:
    st.session_state.portfoy = []

# 5. YAN PANEL (Giriş Alanı)
with st.sidebar:
    st.header("➕ Yeni Hisse Ekle")
    
    # Arama Kutusu (Otomatik tamamlamalı)
    secilen = st.selectbox("Listeden Seçin veya Yazın:", TUM_HISSELER)
    
    # Manuel Giriş (Listede yoksa buraya yazılır)
    manuel = st.text_input("Listede yoksa manuel kod gir (Örn: BTC-USD):").upper()
    
    # Hangi kodun kullanılacağına karar ver
    final_kod = manuel if manuel else secilen
    
    adet = st.number_input("Adet:", min_value=0.0, step=1.0, value=10.0)
    maliyet = st.number_input("Alış Fiyatı (Birim):", min_value=0.0, step=0.1, value=100.0)
    
    if st.button("Portföye Ekle"):
        st.session_state.portfoy.append({
            "Hisse": final_kod, 
            "Adet": adet, 
            "Maliyet": maliyet
        })
        st.success(f"{final_kod} Eklendi!")

# 6. HESAPLAMALAR VE GÖRSELLEŞTİRME
if st.session_state.portfoy:
    ekran_verisi = []
    toplam_maliyet_genel = 0
    toplam_deger_genel = 0

    with st.spinner('Fiyatlar çekiliyor...'):
        for kalem in st.session_state.portfoy:
            try:
                # Yahoo Finance'ten veri çek
                hisse_obj = yf.Ticker(kalem['Hisse'])
                # En hızlı güncel fiyatı 'fast_info' ile alıyoruz
                guncel_f = hisse_obj.fast_info['lastPrice']
                
                maliyet_toplam = kalem['Adet'] * kalem['Maliyet']
                deger_toplam = kalem['Adet'] * guncel_f
                kar_zarar = deger_toplam - maliyet_toplam
                yuzde = (kar_zarar / maliyet_toplam) * 100 if maliyet_toplam > 0 else 0
                
                toplam_maliyet_genel += maliyet_toplam
                toplam_deger_genel += deger_toplam

                ekran_verisi.append({
                    "Hisse": kalem['Hisse'],
                    "Adet": kalem['Adet'],
                    "Maliyet": round(kalem['Maliyet'], 2),
                    "Güncel": round(guncel_f, 2),
                    "Kâr/Zarar": round(kar_zarar, 2),
                    "Değişim (%)": f"%{yuzde:.2f}",
                    "Toplam Değer": round(deger_toplam, 2)
                })
            except:
                st.error(f"{kalem['Hisse']} verisi alınamadı!")

    if ekran_verisi:
        df = pd.DataFrame(ekran_verisi)
        genel_kar = toplam_deger_genel - toplam_maliyet_genel
        genel_yuzde = (genel_kar / toplam_maliyet_genel) * 100 if toplam_maliyet_genel > 0 else 0

        # Özet Metrikler
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Varlık", f"{toplam_deger_genel:,.2f} TL/$")
        c2.metric("Toplam Kâr/Zarar", f"{genel_kar:,.2f} TL/$", f"%{genel_yuzde:.2f}")
        c3.metric("Hisse Adedi", len(df))

        st.markdown("---")

        # Grafik Alanı
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("🎯 Portföy Dağılımı")
            fig_pie = px.pie(df, values='Toplam Değer', names='Hisse', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_graf2:
            st.subheader("📊 Hisse Bazlı Performans")
            fig_bar = px.bar(df, x='Hisse', y='Kâr/Zarar', color='Hisse')
            st.plotly_chart(fig_bar, use_container_width=True)

        # Tablo
        st.subheader("📋 Detaylı Liste")
        st.dataframe(df, use_container_width=True)

    if st.button("🗑️ Portföyü Sıfırla"):
        st.session_state.portfoy = []
        st.rerun()
else:
    st.info("Henüz hisse eklemedin. Sol taraftaki menüyü kullanarak ilk hisseni ekle!")
