import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# 0. VERİ YÖNETİMİ
# ==========================================
PORTFOY_DOSYASI = "portfoy_kayitlari.json"
IPO_DOSYASI = "halka_arz_kayitlari.json"
ALARM_DOSYASI = "alarm_kayitlari.json"

def load_json(dosya_adi):
    if not os.path.exists(dosya_adi): return []
    try:
        with open(dosya_adi, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x.get('Hisse', '')) if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"JSON yükleme hatası ({dosya_adi}): {e}")
        return []

def save_json(dosya_adi, data):
    try:
        with open(dosya_adi, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"JSON kaydetme hatası ({dosya_adi}): {e}")

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_json(PORTFOY_DOSYASI)
if 'ipo_liste' not in st.session_state:
    st.session_state.ipo_liste = load_json(IPO_DOSYASI)
if 'alarmlar' not in st.session_state:
    st.session_state.alarmlar = load_json(ALARM_DOSYASI)

# ==========================================
# VERİ ÇEKME FONKSİYONLARI
# ==========================================
@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="60d")   # MACD için 60 gün gerekli
        if hist.empty:
            logger.warning(f"Veri boş: {symbol}")
            return None

        divs = tk.dividends
        yillik_net_temettu = 0.0
        son_tarih = "-"

        if not divs.empty:
            try:
                # Timezone sorununu düzelt: tz-aware → tz-naive
                if divs.index.tz is not None:
                    divs.index = divs.index.tz_convert('UTC').tz_localize(None)
                else:
                    divs.index = divs.index.tz_localize(None)

                son_1_yil = datetime.now() - timedelta(days=365)
                son_1_yil_divs = divs[divs.index >= son_1_yil]

                if not son_1_yil_divs.empty:
                    # Son 1 yıl içinde dağıtım var → topla
                    yillik_brut_temettu = float(son_1_yil_divs.sum())
                    yillik_net_temettu = round(yillik_brut_temettu * 0.90, 4)
                    son_tarih = divs.index[-1].strftime('%d.%m.%Y')
                else:
                    # Son 1 yılda dağıtım yok → en son temettu değerini göster, tarihi işaretle
                    yillik_brut_temettu = float(divs.iloc[-1])
                    yillik_net_temettu = round(yillik_brut_temettu * 0.90, 4)
                    son_tarih = divs.index[-1].strftime('%d.%m.%Y') + " *"
            except Exception as e:
                logger.warning(f"Temettü işleme hatası ({symbol}): {e}")
                yillik_net_temettu = 0.0
                son_tarih = "-"

        return {"hist": hist, "temettu": yillik_net_temettu, "tarih": son_tarih}

    except Exception as e:
        logger.error(f"Hisse veri çekme hatası ({symbol}): {e}")
        return None

@st.cache_data(ttl=300)
def fetch_tefas_price(symbol):
    """TEFAS'tan fon fiyatı çeker. Çoklu regex ve hata durumu döner."""
    code = symbol.replace(".IS", "").upper()
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={code}"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')

        # Sırayla farklı regex dene
        patterns = [
            r'Son Fiyat \(TL\).*?<span[^>]*>([\d.,]+)</span>',
            r'top-list-right">([\d.,]+)</span>',
            r'"top-list-right">\s*([\d.,]+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.DOTALL)
            if m:
                price_str = m.group(1).strip().replace('.', '').replace(',', '.')
                try:
                    price = float(price_str)
                    if price > 0:
                        return {"fiyat": price, "durum": "ok"}
                except ValueError:
                    continue

        logger.warning(f"TEFAS fiyat parse edilemedi: {code}")
        return {"fiyat": None, "durum": "parse_hatası"}

    except urllib.error.URLError as e:
        logger.error(f"TEFAS bağlantı hatası ({code}): {e}")
        return {"fiyat": None, "durum": "bağlantı_hatası"}
    except Exception as e:
        logger.error(f"TEFAS genel hata ({code}): {e}")
        return {"fiyat": None, "durum": "genel_hata"}

def tr_format(val):
    try:
        if val is None or pd.isna(val): return "0,00"
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

# ==========================================
# GELİŞTİRİLMİŞ SİNYAL MOTORU
# RSI + MA20 + MACD + Bollinger Bands
# ==========================================
def get_signal(hist_data):
    try:
        if len(hist_data) < 26:
            return "VERİ YETERSİZ", 0.0, 0.0, 50.0

        close = hist_data['Close']

        # --- RSI (14) ---
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])

        # --- MA20 ---
        ma20 = float(close.rolling(window=20).mean().iloc[-1])
        last_price = float(close.iloc[-1])

        # --- MACD (12, 26, 9) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        macd_histogram = round(macd_val - signal_val, 4)

        # --- Bollinger Bands (20, 2σ) ---
        bb_ma = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = float((bb_ma + 2 * bb_std).iloc[-1])
        bb_lower = float((bb_ma - 2 * bb_std).iloc[-1])
        bb_pct = round(
            (last_price - bb_lower) / (bb_upper - bb_lower) * 100, 1
        ) if bb_upper != bb_lower else 50.0

        # --- Birleşik Skor ---
        skor = 0

        # RSI katkısı
        if rsi < 30:   skor += 3
        elif rsi < 40: skor += 2
        elif rsi < 50: skor += 1
        elif rsi > 75: skor -= 3
        elif rsi > 65: skor -= 2
        elif rsi > 55: skor -= 1

        # MA20 katkısı
        if last_price > ma20:  skor += 1
        else:                   skor -= 1

        # MACD katkısı (histogram yönü)
        if macd_val > signal_val:  skor += 2
        else:                       skor -= 2

        # Bollinger katkısı
        if last_price < bb_lower:   skor += 2   # Aşırı satım
        elif last_price > bb_upper: skor -= 2   # Aşırı alım

        # Sinyal kararı
        if   skor >= 6:  sinyal = "🟢 GÜÇLÜ AL"
        elif skor >= 3:  sinyal = "🟢 AL"
        elif skor <= -6: sinyal = "🔴 GÜÇLÜ SAT"
        elif skor <= -3: sinyal = "🔴 SAT"
        else:            sinyal = "🟡 TUT"

        return sinyal, round(rsi, 1), macd_histogram, bb_pct

    except Exception as e:
        logger.warning(f"Sinyal hesaplama hatası: {e}")
        return "---", 0.0, 0.0, 50.0

# ==========================================
# PARALEL VERİ HAZIRLAMA
# ==========================================
def fetch_single_item(args):
    """Tek bir portföy kalemini işler (ThreadPoolExecutor için)."""
    i, item = args
    piyasa_durumu = item.get("Piyasa", "Türk Borsası")
    d = fetch_stock_data(item['Hisse'])

    if piyasa_durumu == "Yatırım Fonu":
        tefas_result = fetch_tefas_price(item['Hisse'])
        fiyat = tefas_result.get("fiyat") if tefas_result else None
        tefas_durum = tefas_result.get("durum", "hata") if tefas_result else "hata"

        if fiyat:
            c = fiyat
            if d:
                sinyal_result = get_signal(d['hist'])
                sinyal, rsi_val, macd_h, bb_pct = sinyal_result
                pc = float(d['hist']['Close'].iloc[-2])
            else:
                sinyal = "VERİ YOK"; rsi_val = 0.0; macd_h = 0.0; bb_pct = 50.0; pc = c
        else:
            c = item['Maliyet']; pc = c
            sinyal = f"⚠️ {tefas_durum.replace('_', ' ').upper()}"
            rsi_val = 0.0; macd_h = 0.0; bb_pct = 50.0
        temettu = 0.0; tarih = "-"

    else:
        if d:
            c = float(d['hist']['Close'].iloc[-1])
            pc = float(d['hist']['Close'].iloc[-2])
            sinyal, rsi_val, macd_h, bb_pct = get_signal(d['hist'])
            temettu = d['temettu']; tarih = d['tarih']
        else:
            c = item['Maliyet']; pc = c
            sinyal = "⚠️ VERİ YOK"
            rsi_val = 0.0; macd_h = 0.0; bb_pct = 50.0
            temettu = 0.0; tarih = "-"

    adet_int = int(item['Adet'])
    return {
        "id": i, "Piyasa": piyasa_durumu, "Hisse": item['Hisse'],
        "Sinyal": sinyal, "RSI": rsi_val, "MACD_H": macd_h, "BB_PCT": bb_pct,
        "Adet": adet_int, "Maliyet": item['Maliyet'],
        "Güncel": c,
        "K/Z": round((c - item['Maliyet']) * adet_int, 2),
        "Değer": round(c * adet_int, 2),
        "Temettu": temettu,
        "NetTemettu": round(temettu * adet_int, 2),
        "DailyDiff": round((c - pc) * adet_int, 2),
        "Tarih": tarih
    }

# ==========================================
# 1. TEMA VE CSS
# ==========================================
st.set_page_config(page_title="Borsa Takip", page_icon="📈", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

tema_isimleri = [
    "Siyah-Beyaz (Klasik)", "Siyah-Beyaz (Koyu)", "Galaksi (VIP)", "Siber Punk", "Matrix", "Altın Vuruş",
    "Zümrüt Yeşili", "Lav Akışı", "Okyanus Derinliği", "Kuzey Işıkları", "Buzul (Dark)", "Mor Ötesi",
    "Bakır Buharı", "Gece Yarısı", "Safir Gece", "Çöl Fırtınası", "Kızıl Elmas", "Premium Koyu",
    "Retro Kehribar", "Derin Orman", "Antrasit VIP", "Neon Gecesi", "Gümüş", "Titanyum", "Platin",
    "Yakut", "Ametist", "Turkuaz", "Karanlık Madde", "Süpernova", "Karadelik", "Yıldız Tozu",
    "Kozmik Mavi", "Güneş Patlaması", "Zehirli Yeşil", "Çikolata Rüyası", "Vanilya Gökyüzü",
    "Kızıl Gezegen", "Buz Devi", "Volkanik Kül", "Şafak Vakti", "Alacakaranlık", "Gece Kuşu",
    "Şehir Işıkları", "Siber Gümüş", "Kripto Yeşili", "Hacker Terminali", "Galaktik Mor",
    "Kuantum Foton", "Biyolüminesans"
]

with st.sidebar:
    st.header("🎨 Tema Galerisi")
    tema = st.selectbox("Görünüm Seç", tema_isimleri)

tema_renkleri = {
    "Siyah-Beyaz (Klasik)": {"bg": "#FFFFFF", "text": "#000000", "box": "#F5F5F5", "accent": "#000000"},
    "Siyah-Beyaz (Koyu)":   {"bg": "#000000", "text": "#FFFFFF", "box": "#1A1A1A", "accent": "#FFFFFF"},
    "Galaksi (VIP)":        {"bg": "#0B0E14", "text": "#E0E0E0", "box": "#161B22", "accent": "#00D4FF"},
    "Siber Punk":           {"bg": "#0D0221", "text": "#FFFFFF", "box": "#190033", "accent": "#FF00FF"},
    "Matrix":               {"bg": "#000000", "text": "#00FF41", "box": "#0D0208", "accent": "#00FF41"},
    "Altın Vuruş":          {"bg": "#0F0F0F", "text": "#F5F5F5", "box": "#1A1A1A", "accent": "#D4AF37"},
    "Zümrüt Yeşili":        {"bg": "#06120B", "text": "#E8F5E9", "box": "#0D2114", "accent": "#00E676"},
    "Lav Akışı":            {"bg": "#1A0F0F", "text": "#F8F9FA", "box": "#2D1B1B", "accent": "#FF4D4D"},
    "Okyanus Derinliği":    {"bg": "#001B2E", "text": "#ADB5BD", "box": "#003554", "accent": "#24D1FF"},
    "Kuzey Işıkları":       {"bg": "#0B101B", "text": "#E9ECEF", "box": "#1B263B", "accent": "#A5FFD6"},
    "Buzul (Dark)":         {"bg": "#0D1117", "text": "#C9D1D9", "box": "#161B22", "accent": "#58A6FF"},
    "Mor Ötesi":            {"bg": "#120D1D", "text": "#E0D7FF", "box": "#1E1631", "accent": "#9D4EDD"},
    "Bakır Buharı":         {"bg": "#1B1510", "text": "#D4A373", "box": "#2C211A", "accent": "#E76F51"},
    "Gece Yarısı":          {"bg": "#050505", "text": "#FFFFFF", "box": "#121212", "accent": "#F72585"},
    "Safir Gece":           {"bg": "#03045E", "text": "#CAF0F8", "box": "#023E8A", "accent": "#00B4D8"},
    "Çöl Fırtınası":        {"bg": "#1C1917", "text": "#F5F5F4", "box": "#292524", "accent": "#EAB308"},
    "Kızıl Elmas":          {"bg": "#0F0202", "text": "#FFFFFF", "box": "#1F0505", "accent": "#D00000"},
    "Premium Koyu":         {"bg": "#121212", "text": "#ffffff", "box": "#4c4c4c", "accent": "#BB86FC"},
    "Retro Kehribar":       {"bg": "#0A0A0A", "text": "#FFB300", "box": "#1A1A1A", "accent": "#FF8F00"},
    "Derin Orman":          {"bg": "#081C15", "text": "#D8F3DC", "box": "#1B4332", "accent": "#95D5B2"},
    "Antrasit VIP":         {"bg": "#1B1B1B", "text": "#D1D1D1", "box": "#2D2D2D", "accent": "#E0E0E0"},
    "Neon Gecesi":          {"bg": "#000814", "text": "#FFFFFF", "box": "#001D3D", "accent": "#FFC300"},
    "Gümüş":                {"bg": "#111111", "text": "#E0E0E0", "box": "#222222", "accent": "#C0C0C0"},
    "Titanyum":             {"bg": "#1C1F22", "text": "#E8E9EA", "box": "#2B2F33", "accent": "#878681"},
    "Platin":               {"bg": "#151515", "text": "#FDFDFD", "box": "#252525", "accent": "#E5E4E2"},
    "Yakut":                {"bg": "#1A0505", "text": "#FDE0E0", "box": "#2B0A0A", "accent": "#E0115F"},
    "Ametist":              {"bg": "#140A1A", "text": "#EAD5F7", "box": "#251330", "accent": "#9966CC"},
    "Turkuaz":              {"bg": "#061A1C", "text": "#D5F4F7", "box": "#0A2D30", "accent": "#40E0D0"},
    "Karanlık Madde":       {"bg": "#020202", "text": "#808080", "box": "#0A0A0A", "accent": "#4B0082"},
    "Süpernova":            {"bg": "#1A0D00", "text": "#FFDAB9", "box": "#331A00", "accent": "#FF4500"},
    "Karadelik":            {"bg": "#000000", "text": "#4A4A4A", "box": "#050505", "accent": "#FFFFFF"},
    "Yıldız Tozu":          {"bg": "#0A0A12", "text": "#F0F8FF", "box": "#141424", "accent": "#FFD700"},
    "Kozmik Mavi":          {"bg": "#050B14", "text": "#B0C4DE", "box": "#0A1628", "accent": "#1E90FF"},
    "Güneş Patlaması":      {"bg": "#140500", "text": "#FFEFD5", "box": "#280A00", "accent": "#FF8C00"},
    "Zehirli Yeşil":        {"bg": "#051405", "text": "#E0FFE0", "box": "#0A280A", "accent": "#39FF14"},
    "Çikolata Rüyası":      {"bg": "#1E120D", "text": "#E8D8D0", "box": "#2D1B14", "accent": "#D2691E"},
    "Vanilya Gökyüzü":      {"bg": "#F3E5AB", "text": "#3E2723", "box": "#FFF3E0", "accent": "#5D4037"},
    "Kızıl Gezegen":        {"bg": "#1C0A00", "text": "#FFD1B3", "box": "#331400", "accent": "#B22222"},
    "Buz Devi":             {"bg": "#00111A", "text": "#CCEEFF", "box": "#002233", "accent": "#00FFFF"},
    "Volkanik Kül":         {"bg": "#1C1C1C", "text": "#A9A9A9", "box": "#2A2A2A", "accent": "#FF6347"},
    "Şafak Vakti":          {"bg": "#1A1016", "text": "#FADADD", "box": "#2B1A24", "accent": "#FF69B4"},
    "Alacakaranlık":        {"bg": "#0B0C10", "text": "#C5C6C7", "box": "#1F2833", "accent": "#66FCF1"},
    "Gece Kuşu":            {"bg": "#080808", "text": "#CCCCCC", "box": "#141414", "accent": "#7B68EE"},
    "Şehir Işıkları":       {"bg": "#0A0A0A", "text": "#F0F0F0", "box": "#171717", "accent": "#FF1493"},
    "Siber Gümüş":          {"bg": "#0D0D11", "text": "#D1D5DB", "box": "#1F2937", "accent": "#9CA3AF"},
    "Kripto Yeşili":        {"bg": "#0B110B", "text": "#E5FFE5", "box": "#152215", "accent": "#00FF00"},
    "Hacker Terminali":     {"bg": "#000000", "text": "#00FF00", "box": "#051105", "accent": "#008000"},
    "Galaktik Mor":         {"bg": "#0A0014", "text": "#E6CCFF", "box": "#140028", "accent": "#8A2BE2"},
    "Kuantum Foton":        {"bg": "#000A14", "text": "#CCE5FF", "box": "#001428", "accent": "#00BFFF"},
    "Biyolüminesans":       {"bg": "#001414", "text": "#CCFFFF", "box": "#002828", "accent": "#00FA9A"},
}

t_sec = tema_renkleri.get(tema, tema_renkleri["Galaksi (VIP)"])

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@700&display=swap');
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; font-family: 'Inter', sans-serif; }}
    [data-testid="stMetric"] {{ background: {t_sec['box']}; padding: 20px !important; border-radius: 12px !important; border: 1px solid {t_sec['accent']} !important; text-align: center; }}
    .kral-table {{ width: 100%; border-collapse: collapse; background: {t_sec['box']}22; margin-top: 10px; border: 1px solid {t_sec['accent']}33; border-radius: 10px; overflow: hidden; }}
    .kral-table th {{ padding: 12px; text-align: left; background: {t_sec['accent']}22; color: {t_sec['accent']}; font-weight: 700; border-bottom: 2px solid {t_sec['accent']}44; }}
    .kral-table td {{ padding: 12px; border-bottom: 1px solid {t_sec['accent']}11; color: {t_sec['text']}; }}
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; padding: 15px 0; border: 1px solid {t_sec['accent']}44; }}
    .ticker-content {{ display: flex; animation: ticker 25s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; }} .down {{ color: #ff1744; font-weight: bold; }}
    .alarm-aktif {{ color: #ff1744; font-weight: bold; animation: blink 1s step-start infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .indikator-bar {{ display: inline-block; height: 8px; border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. ÜST BİLGİ VE PİYASA
# ==========================================
clock_html = f"""
<div style="position: fixed; top: 10px; right: 10px; background: {t_sec['box']}; padding: 10px 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); z-index: 99999; display: flex; flex-direction: column; align-items: flex-end; border: 1px solid {t_sec['accent']};">
    <div id="digital-clock" style="font-size: 20px; font-weight: bold; font-family: 'JetBrains Mono', monospace; color: {t_sec['accent']};"></div>
    <div id="date-display" style="font-size: 11px; font-weight: 600; color: {t_sec['text']}; opacity: 0.8; letter-spacing: 1px;"></div>
</div>
<script>
function updateClock() {{
    const trTime = new Date(new Date().toLocaleString("en-US", {{timeZone: "Europe/Istanbul"}}));
    document.getElementById('digital-clock').innerText = trTime.toLocaleTimeString('tr-TR', {{hour12: false}});
    document.getElementById('date-display').innerText = trTime.toLocaleDateString('tr-TR', {{day: '2-digit', month: 'long', year: 'numeric', weekday: 'long'}}).toUpperCase();
}}
setInterval(updateClock, 1000); updateClock();
</script>
"""
st.components.v1.html(clock_html, height=80)

st.markdown(f"<h2 style='text-align:center; color:{t_sec['accent']};'>🚀 Borsa Takip</h2>", unsafe_allow_html=True)

piyasa_izleme = {"BIST 100": "XU100.IS", "ONS ALTIN": "GC=F", "ONS GÜMÜŞ": "SI=F", "USD/TRY": "USDTRY=X", "BTC": "BTC-USD"}
ticker_content = '<div class="ticker-wrapper"><div class="ticker-content">'
for isim, sembol in piyasa_izleme.items():
    d = fetch_stock_data(sembol)
    if d:
        try:
            last = float(d['hist']['Close'].iloc[-1])
            prev = float(d['hist']['Close'].iloc[-2])
            deg  = ((last - prev) / prev) * 100
            ticker_content += f'<div style="text-align:center;"><div>{isim}</div><div style="font-weight:bold;">{tr_format(last)}</div><div class="{"up" if deg>=0 else "down"}">{deg:+.2f}%</div></div>'
        except Exception as e:
            logger.warning(f"Ticker hatası ({sembol}): {e}")
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 3. PARALEL VERİ HAZIRLAMA
# ==========================================
BIST_FULL = sorted([
    "A1CAP.IS", "ACSEL.IS", "ADEL.IS", "ADESE.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS", "ALMAD.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS", "ASGYO.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "ATAKP.IS", "ATEKS.IS", "ATGRP.IS", "ATLAS.IS", "ATSYH.IS", "AVHOL.IS", "AVOD.IS", "AVPGY.IS", "AYDEM.IS", "AYEN.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENP.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS", "BOSSA.IS", "BRISA.IS", "BRKO.IS", "BRKSN.IS", "BRKVY.IS", "BRLSM.IS", "BRMEN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEVNY.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGHL.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS", "DERAS.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGGYO.IS", "DGNMO.IS", "DIRIT.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", "DOCO.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS", "ECZYT.IS", "EDATA.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKIZ.IS", "EKOS.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS", "ERBOS.IS", "EREGL.IS", "ERSU.IS", "ESCOM.IS", "ESEN.IS", "ETILER.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "FZLGY.IS", "GARAN.IS", "GBUFG.IS", "GENTS.IS", "GEREL.IS", "GESAN.IS", "GIPTA.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "IDAS.IS", "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "IPEKE.IS", "ISATR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISMEN.IS", "ISSEN.IS", "ISYAT.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS", "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS", "KAYSE.IS", "KBCOR.IS", "KCAER.IS", "KCHOL.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLMSN.IS", "KLNMA.IS", "KLKIM.IS", "KLRHO.IS", "KLSYN.IS", "KLYAS.IS", "KMEPU.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS", "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KRVGD.IS", "KSTUR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS", "LINK.IS", "LMKDC.IS", "LOGAS.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEKAG.IS", "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS", "MHRGY.IS", "MIATK.IS", "MIPAZ.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS", "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS", "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS", "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS", "PCILT.IS", "PEGYO.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS", "RAYYS.IS", "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SAMAT.IS", "SANEL.IS", "SANFO.IS", "SANIC.IS", "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS", "SEKOK.IS", "SELEC.IS", "SELGD.IS", "SERVE.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SKYMD.IS", "SKYLP.IS", "SMART.IS", "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKPA.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS", "TAPDI.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TIRE.IS", "TKFEN.IS", "TKNSA.IS", "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS", "ULUSE.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS", "VBTYM.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKGYO.IS", "VKING.IS", "VRGYO.IS", "YAPRK.IS", "YATAS.IS", "YAYLA.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS", "YKBNK.IS", "YONGA.IS", "YOTAS.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS", "ZOREN.IS", "ZRGYO.IS"
])
FON_LIST = sorted([
    "TTE.IS","AES.IS","AFO.IS","AYA.IS","KPH.IS","KPA.IS","ZGD.IS","ZRE.IS",
    "TAU.IS","MAC.IS","YZG.IS","OPB.IS","NNF.IS","IDH.IS","GSP.IS","IHY.IS"
])

full_data = []
if st.session_state.portfoy:
    args_list = list(enumerate(st.session_state.portfoy))
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_single_item, args_list))
    full_data = sorted(results, key=lambda x: x['Hisse'])

# ==========================================
# ALARM KONTROLÜ — sayfa yüklenince otomatik çalışır
# ==========================================
tetiklenen_alarmlar = []
for alarm in st.session_state.alarmlar:
    hisse = alarm.get("Hisse", "")
    hedef = alarm.get("Hedef", 0.0)
    yon   = alarm.get("Yon", "Üstüne Çıkınca")
    aktif = alarm.get("Aktif", True)

    if not aktif:
        continue

    # Anlık fiyatı bul
    for row in full_data:
        if row["Hisse"] == hisse:
            guncel = row["Güncel"]
            if yon == "Üstüne Çıkınca" and guncel >= hedef:
                tetiklenen_alarmlar.append(f"🔔 {hisse}: {tr_format(guncel)} ₺ → Hedef {tr_format(hedef)} ₺ aşıldı!")
            elif yon == "Altına Düşünce" and guncel <= hedef:
                tetiklenen_alarmlar.append(f"🔔 {hisse}: {tr_format(guncel)} ₺ → Hedef {tr_format(hedef)} ₺ altına indi!")
            break

if tetiklenen_alarmlar:
    for msg in tetiklenen_alarmlar:
        st.warning(msg, icon="🚨")

# ==========================================
# 4. TABLAR VE İÇERİK
# ==========================================
tab_tr, tab_fon, tab_div, tab_ipo, tab_alarm = st.tabs([
    "🇹🇷 TÜRK BORSASI",
    "📊 YATIRIM FONLARI",
    "💰 TEMETTÜ GELİRİ",
    "🚀 HALKA ARZ TAKİP",
    "🔔 FİYAT ALARMLARI"
])

with st.sidebar:
    st.divider()
    st.subheader("➕ Yeni Varlık")
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Yatırım Fonu"], horizontal=True)
    if piyasa_sec == "Türk Borsası":
        hisse_sec = st.selectbox("Hisse Seç", BIST_FULL)
    else:
        hisse_sec = st.selectbox("Fon Seç", FON_LIST + ["DİĞER"])
    if hisse_sec == "DİĞER":
        hisse_sec = st.text_input("Fon Kodu").upper()
    adet_sec    = st.number_input("Adet",    min_value=0,   step=1)
    maliyet_sec = st.number_input("Maliyet", min_value=0.000)
    if st.button("🚀 Portföye Ekle"):
        st.session_state.portfoy.append({
            "Piyasa": piyasa_sec, "Hisse": hisse_sec,
            "Adet": int(adet_sec), "Maliyet": float(maliyet_sec)
        })
        st.session_state.portfoy = sorted(st.session_state.portfoy, key=lambda x: x['Hisse'])
        save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
        st.rerun()

# ==========================================
# YÖNETİM FONKSİYONU
# ==========================================
def varlik_yonetimi_render(df_local):
    with st.expander("🛠️ VARLIK YÖNETİMİ"):
        for _, r in df_local.iterrows():
            c1, c2, c3, c4 = st.columns([1.5, 2, 2, 1])
            c1.markdown(f"<div style='margin-top:25px;'><b>{r['Hisse']}</b></div>", unsafe_allow_html=True)
            y_adet    = c2.number_input("Adet",    value=int(r['Adet']),      step=1,  key=f"a_{r['id']}")
            y_maliyet = c3.number_input("Maliyet", value=float(r['Maliyet']),          key=f"m_{r['id']}")
            c4.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            bc = c4.columns(2)
            if bc[0].button("💾", key=f"s_{r['id']}"):
                st.session_state.portfoy[r['id']]['Adet']    = y_adet
                st.session_state.portfoy[r['id']]['Maliyet'] = y_maliyet
                st.session_state.portfoy = sorted(st.session_state.portfoy, key=lambda x: x['Hisse'])
                save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
                st.rerun()
            if bc[1].button("❌", key=f"d_{r['id']}"):
                st.session_state.portfoy.pop(r['id'])
                save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
                st.rerun()

# ==========================================
# GELİŞTİRİLMİŞ TABLO — RSI + MACD + BB sütunu
# ==========================================
def render_kral_table(df_local, goster_indikatör=True):
    if goster_indikatör:
        baslik = "<tr><th>VARLIK</th><th>SİNYAL</th><th>RSI</th><th>MACD-H</th><th>BB%</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr>"
    else:
        baslik = "<tr><th>VARLIK</th><th>SİNYAL</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr>"

    table_html = f"<table class='kral-table'><thead>{baslik}</thead><tbody>"

    for _, r in df_local.iterrows():
        kz_color = "#00e676" if r['K/Z'] >= 0 else "#ff1744"

        if goster_indikatör:
            # RSI rengi
            rsi = r['RSI']
            if rsi < 35:   rsi_color = "#00e676"
            elif rsi > 65: rsi_color = "#ff1744"
            else:          rsi_color = "#ffc107"

            # MACD histogram
            macd_h = r['MACD_H']
            macd_color  = "#00e676" if macd_h > 0 else "#ff1744"
            macd_sembol = f"+{tr_format(macd_h)}" if macd_h > 0 else tr_format(macd_h)

            # Bollinger % bar
            bb_pct   = max(0, min(100, r['BB_PCT']))
            bb_color = "#00e676" if bb_pct < 30 else ("#ff1744" if bb_pct > 70 else "#ffc107")
            bb_bg = t_sec['box']

            extra = (
                f"<td style='color:{rsi_color};font-weight:bold;'>{rsi:.1f}</td>"
                f"<td style='color:{macd_color};font-weight:bold;'>{macd_sembol}</td>"
                f"<td>"
                f"<div style='background:{bb_bg}; border-radius:4px; width:80px; height:8px; display:inline-block; vertical-align:middle;'>"
                f"<div style='width:{bb_pct}%; background:{bb_color}; height:8px; border-radius:4px;'></div>"
                f"</div> <span style='font-size:11px;color:{bb_color};'>{bb_pct:.0f}%</span>"
                f"</td>"
                f"<td>{r['Adet']}</td>"
            )
            table_html += (
                f"<tr>"
                f"<td><b>{r['Hisse']}</b></td>"
                f"<td>{r['Sinyal']}</td>"
                f"{extra}"
                f"<td>{tr_format(r['Maliyet'])} ₺</td>"
                f"<td>{tr_format(r['Güncel'])} ₺</td>"
                f"<td style='color:{kz_color};font-weight:bold;'>{tr_format(r['K/Z'])} ₺</td>"
                f"<td><b>{tr_format(r['Değer'])} ₺</b></td>"
                f"</tr>"
            )
        else:
            table_html += (
                f"<tr>"
                f"<td><b>{r['Hisse']}</b></td><td>{r['Sinyal']}</td>"
                f"<td>{r['Adet']}</td>"
                f"<td>{tr_format(r['Maliyet'])} ₺</td>"
                f"<td>{tr_format(r['Güncel'])} ₺</td>"
                f"<td style='color:{kz_color};font-weight:bold;'>{tr_format(r['K/Z'])} ₺</td>"
                f"<td><b>{tr_format(r['Değer'])} ₺</b></td>"
                f"</tr>"
            )

    return table_html + "</tbody></table>"

# ==========================================
# TÜRK BORSASI TABU
# ==========================================
with tab_tr:
    df_bist = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Türk Borsası'])
    if not df_bist.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("PORTFÖY DEĞERİ",  f"{tr_format(df_bist['Değer'].sum())} ₺")
        m2.metric("TOPLAM K/Z",       f"{tr_format(df_bist['K/Z'].sum())} ₺")
        m3.metric("GÜNLÜK DEĞİŞİM",  f"{tr_format(df_bist['DailyDiff'].sum())} ₺")

        st.markdown(
            f"<small style='color:{t_sec['accent']}88;'>RSI: &lt;35 aşırı satım &gt;65 aşırı alım | MACD-H: + bullish / - bearish | BB%: &lt;30 alt bant &gt;70 üst bant</small>",
            unsafe_allow_html=True
        )
        st.markdown(render_kral_table(df_bist, goster_indikatör=True), unsafe_allow_html=True)
        varlik_yonetimi_render(df_bist)

        df_chart = df_bist[df_bist['Değer'] > 0]
        if not df_chart.empty:
            st.divider()
            fig = px.pie(
                df_chart, values='Değer', names='Hisse', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=t_sec['text'])
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Hisse senedi bulunamadı.")

# ==========================================
# YATIRIM FONLARI TABU
# ==========================================
with tab_fon:
    df_fon = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Yatırım Fonu'])
    if not df_fon.empty:
        # TEFAS hata uyarıları
        hata_fonlar = df_fon[df_fon['Sinyal'].str.startswith('⚠️', na=False)]
        if not hata_fonlar.empty:
            st.warning(
                f"⚠️ {', '.join(hata_fonlar['Hisse'].tolist())} için TEFAS verisi alınamadı. "
                "Maliyet fiyatı gösteriliyor.",
                icon="⚠️"
            )

        mf1, mf2, mf3 = st.columns(3)
        mf1.metric("FON PORTFÖY DEĞERİ", f"{tr_format(df_fon['Değer'].sum())} ₺")
        mf2.metric("TOPLAM K/Z",          f"{tr_format(df_fon['K/Z'].sum())} ₺")
        mf3.metric("GÜNLÜK DEĞİŞİM",     f"{tr_format(df_fon['DailyDiff'].sum())} ₺")

        st.markdown(render_kral_table(df_fon, goster_indikatör=False), unsafe_allow_html=True)
        varlik_yonetimi_render(df_fon)

        df_chart_f = df_fon[df_fon['Değer'] > 0]
        if not df_chart_f.empty:
            st.divider()
            fig_f = px.pie(
                df_chart_f, values='Değer', names='Hisse', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_f.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=t_sec['text'])
            )
            st.plotly_chart(fig_f, use_container_width=True)
    else:
        st.info("Fon bulunamadı.")

# ==========================================
# TEMETTÜ GELİRİ TABU — Düzeltilmiş
# ==========================================
with tab_div:
    st.markdown("### 💰 Yıllık Projeksiyon (Net Değerler)")
    st.markdown(
        f"<small style='color:{t_sec['accent']}88;'>* işareti: Son 1 yılda dağıtım yapılmamış, gösterilen değer en son temettüdür.</small>",
        unsafe_allow_html=True
    )

    df_div = pd.DataFrame([x for x in full_data if x['Temettu'] > 0])
    if not df_div.empty:
        toplam_temettu = df_div['NetTemettu'].sum()
        st.metric(
            "TAHMİNİ YILLIK NAKİT AKIŞI",
            f"{tr_format(toplam_temettu)} ₺",
            delta=f"Aylık: {tr_format(toplam_temettu / 12)} ₺"
        )

        div_table = (
            "<table class='kral-table'><thead>"
            "<tr>"
            "<th>HİSSE</th>"
            "<th>SON DAĞITIM TARİHİ</th>"
            "<th>ADET</th>"
            "<th>BRÜT HİSSE BAŞI</th>"
            "<th>NET HİSSE BAŞI (%10 stopaj)</th>"
            "<th>YILLIK TOPLAM (NET)</th>"
            "<th>NET VERİM (%)</th>"
            "</tr>"
            "</thead><tbody>"
        )
        for _, r in df_div.iterrows():
            verim = (r['Temettu'] / r['Güncel']) * 100 if r['Güncel'] > 0 else 0
            brut  = round(r['Temettu'] / 0.90, 4)   # Net'ten brüte çevir
            tarih_goster = r['Tarih']
            tarih_color  = t_sec['text'] if '*' not in str(tarih_goster) else "#ffc107"

            div_table += (
                f"<tr>"
                f"<td><b>{r['Hisse']}</b></td>"
                f"<td style='color:{tarih_color};'>{tarih_goster}</td>"
                f"<td>{r['Adet']}</td>"
                f"<td style='color:#ffc107;'>{tr_format(brut)} ₺</td>"
                f"<td style='color:#00e676;'>{tr_format(r['Temettu'])} ₺</td>"
                f"<td><b style='color:#00e676;'>{tr_format(r['NetTemettu'])} ₺</b></td>"
                f"<td>%{verim:.2f}</td>"
                f"</tr>"
            )
        st.markdown(div_table + "</tbody></table>", unsafe_allow_html=True)
    else:
        st.warning("Temettü verisi bulunamadı.")

# ==========================================
# HALKA ARZ TABU
# ==========================================
with tab_ipo:
    st.subheader("🚀 Yeni Halka Arz Ekle")
    with st.form("ipo_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        ipo_isim  = ic1.text_input("Şirket Kodu (Örn: BINHO)")
        ipo_fiyat = ic2.number_input("Halka Arz Fiyatı", min_value=0.0)
        ipo_adet  = ic3.number_input("Lot Sayısı", min_value=0, step=1)
        if st.form_submit_button("➕ Listeye Ekle"):
            if ipo_isim:
                st.session_state.ipo_liste.append({
                    "Isim": ipo_isim.upper(),
                    "Fiyat": ipo_fiyat,
                    "Adet": int(ipo_adet)
                })
                save_json(IPO_DOSYASI, st.session_state.ipo_liste)
                st.rerun()

    if st.session_state.ipo_liste:
        for idx, ipo in enumerate(st.session_state.ipo_liste):
            with st.expander(f"📈 {ipo['Isim']} - Tavan Simülasyonu"):
                col1, col2 = st.columns([6, 1])
                maliyet   = ipo['Adet'] * ipo['Fiyat']
                tavan_html = (
                    "<table class='kral-table' style='text-align:center;'>"
                    "<thead><tr>"
                    "<th style='text-align:center;'>GÜN</th>"
                    "<th style='text-align:center;'>FİYAT</th>"
                    "<th style='text-align:center;'>TOPLAM KAR</th>"
                    "</tr></thead><tbody>"
                )
                p = ipo['Fiyat']
                for g in range(1, 11):
                    p  *= 1.10
                    kar = (p * ipo['Adet']) - maliyet
                    tavan_html += (
                        f"<tr><td><b>{g}. Tavan</b></td>"
                        f"<td>{tr_format(p)} ₺</td>"
                        f"<td style='color:#00e676;font-weight:bold;'>+{tr_format(kar)} ₺</td></tr>"
                    )
                tavan_html += "</tbody></table>"
                col1.markdown(tavan_html, unsafe_allow_html=True)

                if col2.button("❌ LİSTEDEN SİL", key=f"del_ipo_{idx}"):
                    st.session_state.ipo_liste.pop(idx)
                    save_json(IPO_DOSYASI, st.session_state.ipo_liste)
                    st.rerun()

# ==========================================
# FİYAT ALARMLARI TABU — YENİ
# ==========================================
with tab_alarm:
    st.subheader("🔔 Fiyat Alarmı Ekle")
    st.markdown(
        f"<small style='color:{t_sec['accent']}88;'>"
        "Belirlediğin fiyat seviyesine ulaşıldığında sayfa başında uyarı gösterilir."
        "</small>",
        unsafe_allow_html=True
    )

    # Portföydeki tüm hisseler + manuel giriş
    portfoy_hisseler = sorted(set(x['Hisse'] for x in st.session_state.portfoy))

    with st.form("alarm_form", clear_on_submit=True):
        al1, al2, al3, al4 = st.columns([2, 2, 2, 1])
        if portfoy_hisseler:
            alarm_hisse = al1.selectbox("Hisse", portfoy_hisseler + ["MANUEL GİRİŞ"])
        else:
            alarm_hisse = al1.selectbox("Hisse", ["MANUEL GİRİŞ"])

        if alarm_hisse == "MANUEL GİRİŞ":
            alarm_hisse = al1.text_input("Hisse Kodu").upper()

        alarm_hedef = al2.number_input("Hedef Fiyat (₺)", min_value=0.0, step=0.01)
        alarm_yon   = al3.selectbox("Koşul", ["Üstüne Çıkınca", "Altına Düşünce"])
        al4.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

        if st.form_submit_button("🔔 Alarm Ekle"):
            if alarm_hisse and alarm_hedef > 0:
                st.session_state.alarmlar.append({
                    "Hisse": alarm_hisse,
                    "Hedef": alarm_hedef,
                    "Yon":   alarm_yon,
                    "Aktif": True,
                    "Tarih": datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M')
                })
                save_json(ALARM_DOSYASI, st.session_state.alarmlar)
                st.success(f"✅ {alarm_hisse} için {tr_format(alarm_hedef)} ₺ alarmı eklendi.")
                st.rerun()

    st.divider()

    if st.session_state.alarmlar:
        st.markdown("#### 📋 Aktif Alarmlar")
        alarm_table = (
            "<table class='kral-table'><thead>"
            "<tr><th>HİSSE</th><th>HEDEF</th><th>KOŞUL</th><th>ANLİK</th><th>DURUM</th><th>EKLENME</th><th>İŞLEM</th></tr>"
            "</thead><tbody>"
        )
        for idx, alarm in enumerate(st.session_state.alarmlar):
            hisse  = alarm.get("Hisse", "-")
            hedef  = alarm.get("Hedef", 0.0)
            yon    = alarm.get("Yon",   "-")
            aktif  = alarm.get("Aktif", True)
            tarih  = alarm.get("Tarih", "-")

            # Anlık fiyatı portföyden bul
            anlik_fiyat = None
            for row in full_data:
                if row["Hisse"] == hisse:
                    anlik_fiyat = row["Güncel"]
                    break

            # Tetiklenme durumu
            tetiklendi = False
            if anlik_fiyat is not None:
                if yon == "Üstüne Çıkınca" and anlik_fiyat >= hedef:
                    tetiklendi = True
                elif yon == "Altına Düşünce" and anlik_fiyat <= hedef:
                    tetiklendi = True

            durum_str = (
                "<span class='alarm-aktif'>🚨 TETİKLENDİ</span>"
                if tetiklendi else
                ("<span style='color:#00e676;'>✅ Aktif</span>" if aktif else "<span style='color:#888;'>⏸ Pasif</span>")
            )
            anlik_str  = tr_format(anlik_fiyat) + " ₺" if anlik_fiyat else "—"
            yon_sembol = "⬆️" if "Üstüne" in yon else "⬇️"

            alarm_table += (
                f"<tr>"
                f"<td><b>{hisse}</b></td>"
                f"<td style='color:{t_sec['accent']};font-weight:bold;'>{tr_format(hedef)} ₺</td>"
                f"<td>{yon_sembol} {yon}</td>"
                f"<td>{anlik_str}</td>"
                f"<td>{durum_str}</td>"
                f"<td style='font-size:11px;'>{tarih}</td>"
                f"<td>—</td>"
                f"</tr>"
            )
        st.markdown(alarm_table + "</tbody></table>", unsafe_allow_html=True)

        # Silme işlemleri (tablo dışında, Streamlit butonları)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🗑️ Alarm Sil / Duraklat"):
            for idx, alarm in enumerate(st.session_state.alarmlar):
                hisse = alarm.get("Hisse", "-")
                hedef = alarm.get("Hedef", 0.0)
                aktif = alarm.get("Aktif", True)
                bc1, bc2, bc3 = st.columns([3, 1, 1])
                bc1.markdown(f"**{hisse}** → {tr_format(hedef)} ₺ ({alarm.get('Yon', '')})")

                if bc2.button("⏸ Duraklat" if aktif else "▶️ Aktifleştir", key=f"pause_{idx}"):
                    st.session_state.alarmlar[idx]['Aktif'] = not aktif
                    save_json(ALARM_DOSYASI, st.session_state.alarmlar)
                    st.rerun()

                if bc3.button("❌ Sil", key=f"del_alarm_{idx}"):
                    st.session_state.alarmlar.pop(idx)
                    save_json(ALARM_DOSYASI, st.session_state.alarmlar)
                    st.rerun()
    else:
        st.info("Henüz alarm eklenmemiş.")

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption(
    f"🕒 Son Güncelleme: {datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')}  |  "
    f"Sinyal: RSI + MA20 + MACD + Bollinger Bands  |  * Son 1 yılda temettü dağıtımı yapılmamış hisseler"
)
