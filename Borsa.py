import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# ==========================================
# 1. AYARLAR & LOGO
# ==========================================
st.set_page_config(page_title="İmparator Portföy v5", page_icon="👑", layout="wide")

# --- KRİTİK: KALICI HAFIZA MEKANİZMASI (Local Storage) ---
# Bu bileşen, verileri tarayıcıda saklamanı sağlar.
from streamlit_javascript import st_javascript

def save_data(data):
    js_code = f"localStorage.setItem('kral_portfoy', '{json.dumps(data)}');"
    st_javascript(js_code)

def load_data():
    js_code = "localStorage.getItem('kral_portfoy');"
    stored_data = st_javascript(js_code)
    if stored_data:
        return json.loads(stored_data)
    return []

# Uygulama başladığında veriyi yükle
if 'portfoy' not in st.session_state:
    loaded = load_data()
    st.session_state.portfoy = loaded if loaded else []

# ==========================================
# 2. HİSSE LİSTELERİ
# ==========================================
BIST_LIST = sorted(["THYAO.IS", "ASELS.IS", "EREGL.IS", "TUPRS.IS", "SASA.IS", "SISE.IS", "GARAN.IS", "AKBNK.IS", "FROTO.IS", "KCHOL.IS", "PGSUS.IS", "BIMAS.IS"])
YABANCI_LIST = ["AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]
TUM_LISTE = sorted(BIST_LIST + YABANCI_LIST)

# ==========================================
# 3. YAN PANEL (GİRİŞ)
# ==========================================
with st.sidebar:
    st.header("👑 İmparator Menü")
    secilen = st.selectbox("Varlık Seç:", TUM_LISTE)
    adet = st.number_input("Adet:", min_value=0.0, step=1.0, value=1.0)
    maliyet = st.number_input("Birim Maliyet:", min_value=0.0, step=0.1, value=100.0)
    
    if st.button("📦 Portföye Ekle"):
        st.session_state.portfoy.append({"Hisse": secilen, "Adet": adet, "Maliyet": maliyet})
        save_data(st.session_state.portfoy) # Veriyi tarayıcıya kaydet
        st.success(f"{secilen} kaydedildi!")
        st.rerun()

    if st.button("🗑️ Tümünü Temizle"):
        st.session_state.portfoy = []
        save_data([]) # Boş listeyi kaydet
        st.rerun()

# ==========================================
# 4. ANA PANEL (TABLO VE GRAFİK ALANLARI)
# ==========================================
st.title("📈 İmparator Portföy Yönetimi")

if st.session_state.portfoy:
    # --- VERİ İŞLEME ---
    display_list = []
    t_maliyet = 0
    t_deger = 0

    with st.spinner('Piyasa verileri okunuyor...'):
        for item in st.session_state.portfoy:
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

    df = pd.DataFrame(display_list)

    # --- ÜST ÖZET ALANI ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Varlık", f"{t_deger:,.2f} TL")
    kz_genel = t_deger - t_maliyet
    c2.metric("Toplam Kâr/Zarar", f"{kz_genel:,.2f} TL", f"%{(kz_genel/t_maliyet*100):.2f}")
    c3.metric("Varlık Sayısı", len(df))

    st.markdown("---")

    # --- GRAFİK ALANI (Ayrı bir bölüm) ---
    st.subheader("📊 Analiz Grafikleri")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        fig_pie = px.pie(df, values='Toplam Değer', names='Varlık', hole=0.4, title="Varlık Dağılımı")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g_col2:
        fig_bar = px.bar(df, x='Varlık', y='Kâr/Zarar', color='Varlık', title="Kâr/Zarar Dağılımı")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # --- TABLO ALANI (Ayrı bir bölüm) ---
    st.subheader("📋 Detaylı Portföy Tablosu")
    
    # Renklendirme fonksiyonu
    def color_df(val):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'

    st.dataframe(
        df.style.applymap(color_df, subset=['Kâr/Zarar', 'Verim %']),
        use_container_width=True
    )

else:
    st.info("Henüz varlık eklemediniz. Sol taraftan ekleme yapabilirsiniz. Verileriniz bu tarayıcıda saklanacaktır.")

# Alt Bilgi
st.caption("Not: Verileriniz tarayıcınızın yerel depolama alanında saklanır. Tarayıcı geçmişini silmediğiniz sürece kaybolmaz.")
