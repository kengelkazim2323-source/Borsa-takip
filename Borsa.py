import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Kral Portföy Pro", layout="wide", initial_sidebar_state="expanded")

# --- STİL DOKUNUŞU ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Kral Portföy Yönetimi v3.0")

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = []

# --- YAN PANEL ---
with st.sidebar:
    st.header("💎 Varlık Ekle")
    kod = st.text_input("Hisse Sembolü (Örn: THYAO.IS):").upper()
    adet = st.number_input("Adet:", min_value=0.0, step=0.1)
    maliyet = st.number_input("Birim Maliyet:", min_value=0.0, step=0.01)
    
    if st.button("Portföye İşle"):
        if kod and adet > 0:
            st.session_state.portfoy.append({"Hisse": kod, "Adet": adet, "Maliyet": maliyet})
            st.success(f"{kod} Portföye eklendi!")
        else:
            st.error("Lütfen bilgileri tam girin.")

# --- ANALİZ BÖLÜMÜ ---
if st.session_state.portfoy:
    data = []
    
    with st.spinner('Veriler güncelleniyor...'):
        for kalem in st.session_state.portfoy:
            hisse = yf.Ticker(kalem['Hisse'])
            info = hisse.history(period="1d")
            guncel_fiyat = info['Close'].iloc[-1]
            
            toplam_maliyet = kalem['Adet'] * kalem['Maliyet']
            guncel_deger = kalem['Adet'] * guncel_fiyat
            kar_zarar = guncel_deger - toplam_maliyet
            yuzde = (kar_zarar / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
            
            data.append({
                "Hisse": kalem['Hisse'],
                "Adet": kalem['Adet'],
                "Maliyet": kalem['Maliyet'],
                "Güncel": round(guncel_fiyat, 2),
                "Kâr/Zarar": round(kar_zarar, 2),
                "Değişim %": round(yuzde, 2),
                "Toplam Değer": round(guncel_deger, 2)
            })

    df = pd.DataFrame(data)

    # Üst Özet Kartları
    total_val = df["Toplam Değer"].sum()
    total_prof = df["Kâr/Zarar"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Varlık", f"{total_val:,.2f} TL")
    col2.metric("Toplam Kâr/Zarar", f"{total_prof:,.2f} TL", f"{ (total_prof/(total_val-total_prof)*100):.2f}%")
    col3.metric("Hisse Sayısı", len(df))

    st.divider()

    # Grafikler
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("🎯 Portföy Dağılımı")
        fig = px.pie(df, values='Toplam Değer', names='Hisse', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("📈 Hisse Bazlı Performans")
        # Kârda olanları yeşil, zararda olanları kırmızı gösteren bar chart
        df['Renk'] = df['Kâr/Zarar'].apply(lambda x: 'Kâr' if x >= 0 else 'Zarar')
        fig2 = px.bar(df, x='Hisse', y='Kâr/Zarar', color='Renk', color_discrete_map={'Kâr': '#2ecc71', 'Zarar': '#e74c3c'})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Detaylı Takip Tablosu")
    st.dataframe(df.style.map(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else ('color: green' if isinstance(x, (int, float)) and x > 10 else None), subset=['Kâr/Zarar', 'Değişim %']), use_container_width=True)

    if st.button("🗑️ Tüm Verileri Sıfırla"):
        st.session_state.portfoy = []
        st.rerun()
else:
    st.info("Henüz veri girilmedi. Sol taraftaki menüyü kullanarak portföyünü oluşturabilirsin.")
