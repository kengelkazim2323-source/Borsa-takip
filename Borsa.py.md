import streamlit as st  
import yfinance as yf  
import pandas as pd  
  
# Sayfa Genişliği ve Başlık  
st.set_page_config(page_title="Kral'ın Portföyü", layout="wide")  
  
st.title("📈 Mobil Borsa Takip Paneli")  
st.write("Hisselerini ekle, anlık kâr/zarar durumunu izle.")  
  
# --- VERİ SAKLAMA ---  
if 'portfoy' not in st.session_state:  
    st.session_state.portfoy = []  
  
# --- YAN PANEL: HİSSE EKLEME ---  
with st.sidebar:  
    st.header("➕ Yeni Hisse Ekle")  
    st.info("BIST hisseleri için sonuna .IS ekle (Örn: THYAO.IS)")  
      
    kod = st.text_input("Hisse Kodu:", "THYAO.IS").upper()  
    adet = st.number_input("Adet:", min_value=1, value=1, step=1)  
    maliyet = st.number_input("Alış Fiyatı (Maliyet):", min_value=0.1, value=10.0)  
      
    if st.button("Portföye Ekle"):  
        st.session_state.portfoy.append({"Hisse": kod, "Adet": adet, "Maliyet": maliyet})  
        st.success(f"{kod} başarıyla eklendi!")  
  
# --- ANA EKRAN: HESAPLAMALAR ---  
if st.session_state.portfoy:  
    tablo_verisi = []  
    toplam_portfoy_degeri = 0  
    toplam_kar_zarar = 0  
  
    st.subheader("📊 Güncel Durum")  
      
    for kalem in st.session_state.portfoy:  
        try:  
            # Veriyi Çek  
            hisse = yf.Ticker(kalem['Hisse'])  
            guncel_fiyat = hisse.history(period="1d")['Close'].iloc[-1]  
              
            # Hesaplamalar  
            toplam_maliyet = kalem['Adet'] * kalem['Maliyet']  
            guncel_deger = kalem['Adet'] * guncel_fiyat  
            kar_zarar = guncel_deger - toplam_maliyet  
            yuzde_degisim = (kar_zarar / toplam_maliyet) * 100  
              
            toplam_portfoy_degeri += guncel_deger  
            toplam_kar_zarar += kar_zarar  
              
            tablo_verisi.append({  
                "Hisse": kalem['Hisse'],  
                "Adet": kalem['Adet'],  
                "Maliyet": f"{kalem['Maliyet']:.2f}",  
                "Güncel": f"{guncel_fiyat:.2f}",  
                "Kâr/Zarar": f"{kar_zarar:.2f}",  
                "Değişim %": f"%{yuzde_degisim:.2f}"  
            })  
        except:  
            st.error(f"{kalem['Hisse']} verisi alınamadı. Kodun doğruluğunu kontrol et.")  
  
    # Özet Kartları  
    c1, c2 = st.columns(2)  
    c1.metric("Toplam Portföy Değeri", f"{toplam_portfoy_degeri:.2f} TL")  
    c2.metric("Toplam Kâr / Zarar", f"{toplam_kar_zarar:.2f} TL", f"%{(toplam_kar_zarar/(toplam_portfoy_degeri-toplam_kar_zarar)*100):.2f}")  
  
    # Detaylı Tablo  
    st.dataframe(pd.DataFrame(tablo_verisi), use_container_width=True)  
  
    if st.button("Tüm Portföyü Temizle"):  
        st.session_state.portfoy = []  
        st.rerun()  
else:  
    st.warning("Henüz portföyüne hisse eklemedin. Yan panelden eklemeye başla!")  
  
st.divider()  
st.caption("Veriler Yahoo Finance üzerinden anlık çekilmektedir.")  
