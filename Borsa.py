import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import pytz
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time as _time
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
# Dosyaları daima bu script'in bulunduğu dizine kaydet.
# Böylece kod güncellendiğinde veya farklı dizinden çalıştırıldığında
# veriler kaybolmaz.
_VERI_DIZIN = os.path.dirname(os.path.abspath(__file__))

def _veri_yolu(dosya_adi):
    """Dosya adını, script'in dizinine göre mutlak yola çevirir."""
    return os.path.join(_VERI_DIZIN, dosya_adi)

PORTFOY_DOSYASI    = _veri_yolu("portfoy_kayitlari.json")
IPO_DOSYASI        = _veri_yolu("halka_arz_kayitlari.json")
ALARM_DOSYASI      = _veri_yolu("alarm_kayitlari.json")
PERFORMANS_DOSYASI = _veri_yolu("portfoy_performans.json")
NOTLAR_DOSYASI     = _veri_yolu("hisse_notlari.json")
ISLEM_DOSYASI      = _veri_yolu("islem_gunlugu.json")
WATCHLIST_DOSYASI  = _veri_yolu("watchlist.json")
HEDEF_DOSYASI      = _veri_yolu("hedefler.json")

def portfoy_dosyasi(isim="Ana"):
    """Portföy adına göre JSON dosya yolunu döner."""
    guvenli = re.sub(r'[^a-zA-Z0-9_\-]', '_', isim)
    return _veri_yolu(f"portfoy_{guvenli}.json")

def load_json(dosya_adi):
    """
    JSON dosyasını yükler.
    Dosya bozuksa .bak yedeğini dener.
    Veri yoksa boş liste döner — asla exception fırlatmaz.
    """
    for deneme in [dosya_adi, dosya_adi + ".bak"]:
        if not os.path.exists(deneme):
            continue
        try:
            with open(deneme, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    continue
                # Performans dosyası 'tarih' key'i kullanır
                if data and 'tarih' in data[0] and 'Hisse' not in data[0]:
                    return sorted(data, key=lambda x: x.get('tarih', ''))
                return sorted(data, key=lambda x: x.get('Hisse', ''))
        except Exception as e:
            logger.error(f"JSON yükleme hatası ({deneme}): {e}")
    return []

def save_json(dosya_adi, data):
    """
    JSON dosyasını kaydeder.
    Kaydetmeden önce mevcut dosyayı .bak olarak yedekler.
    Atomic write: önce .tmp'ye yazar, sonra rename eder — yarım kayıt olmaz.
    """
    try:
        # Varsa mevcut dosyayı yedekle
        if os.path.exists(dosya_adi):
            try:
                import shutil
                shutil.copy2(dosya_adi, dosya_adi + ".bak")
            except Exception as e:
                logger.warning(f"Yedekleme başarısız ({dosya_adi}): {e}")

        # Geçici dosyaya yaz → atomic rename
        tmp = dosya_adi + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, dosya_adi)   # atomic: yarım kayıt imkansız

    except Exception as e:
        logger.error(f"JSON kaydetme hatası ({dosya_adi}): {e}")
        # Geçici dosya kaldıysa temizle
        try:
            if os.path.exists(dosya_adi + ".tmp"):
                os.remove(dosya_adi + ".tmp")
        except Exception:
            pass

if 'portfoy_listesi' not in st.session_state:
    # Tüm kayıtlı portföy isimlerini bul
    _mevcut_portfoyler = []
    for _f in os.listdir(_VERI_DIZIN):
        if _f.startswith('portfoy_') and _f.endswith('.json') and 'performans' not in _f:
            _isim = _f.replace('portfoy_','').replace('.json','')
            _mevcut_portfoyler.append(_isim)
    if not _mevcut_portfoyler:
        _mevcut_portfoyler = ['Ana']
    st.session_state.portfoy_listesi = _mevcut_portfoyler

if 'aktif_portfoy' not in st.session_state:
    st.session_state.aktif_portfoy = st.session_state.portfoy_listesi[0]

if 'portfoy' not in st.session_state:
    st.session_state.portfoy = load_json(portfoy_dosyasi(st.session_state.aktif_portfoy))
    # Eski portfoy_kayitlari.json varsa migrasyonu yap
    if not st.session_state.portfoy and os.path.exists(PORTFOY_DOSYASI):
        st.session_state.portfoy = load_json(PORTFOY_DOSYASI)

if 'ipo_liste' not in st.session_state:
    st.session_state.ipo_liste = load_json(IPO_DOSYASI)
if 'alarmlar' not in st.session_state:
    st.session_state.alarmlar = load_json(ALARM_DOSYASI)
if 'performans' not in st.session_state:
    st.session_state.performans = load_json(PERFORMANS_DOSYASI)
if 'notlar' not in st.session_state:
    raw_notlar = load_json(NOTLAR_DOSYASI)
    st.session_state.notlar = {n['Hisse']: n for n in raw_notlar} if raw_notlar else {}
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'islemler' not in st.session_state:
    st.session_state.islemler = load_json(ISLEM_DOSYASI)
if 'mobil_mod' not in st.session_state:
    st.session_state.mobil_mod = False
if 'tablo_font' not in st.session_state:
    st.session_state.tablo_font = 13
if 'tablo_padding' not in st.session_state:
    st.session_state.tablo_padding = 12
if 'gizli_sutunlar' not in st.session_state:
    st.session_state.gizli_sutunlar = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_json(WATCHLIST_DOSYASI)
if 'hedefler' not in st.session_state:
    raw_hedef = load_json(HEDEF_DOSYASI)
    st.session_state.hedefler = {h['id']: h for h in raw_hedef} if raw_hedef else {}

@st.cache_data(ttl=3600)
def fetch_temel_veri(symbol):
    """yfinance'tan F/K, PD/DD, Piyasa Değeri ve Borç/Özsermaye oranını çeker."""
    code = symbol.replace(".IS", "").upper()
    try:
        tk   = yf.Ticker(symbol)
        info = tk.info
        if not info:
            return None
        def safe(key, fallback=None):
            v = info.get(key)
            return v if v is not None else fallback

        pd_dd  = safe('priceToBook')
        fk     = safe('trailingPE') or safe('forwardPE')
        borc   = safe('totalDebt', 0)
        ozserm = safe('totalStockholderEquity') or safe('bookValue', 0)
        borc_ozserm = round(borc / ozserm, 2) if ozserm and ozserm > 0 else None
        piyasa_degeri = safe('marketCap')
        temttu_verimi = safe('dividendYield')

        return {
            'FK':           round(fk, 2)            if fk          else None,
            'PD_DD':        round(pd_dd, 2)          if pd_dd       else None,
            'Borc_Ozserm':  borc_ozserm,
            'Piyasa_Degeri': piyasa_degeri,
            'Temettu_Verimi': round(temttu_verimi * 100, 2) if temttu_verimi else None,
        }
    except Exception as e:
        logger.warning(f"Temel veri hatası ({code}): {e}")
        return None


@st.cache_data(ttl=900)
def fetch_haberler(hisse_listesi):
    """
    Çoklu RSS kaynağından Türkçe borsa haberleri çeker.
    Kaynak önceliği:
      1. Google News RSS — hisse kodu bazlı Türkçe arama
      2. Bloomberg HT RSS — genel piyasa
      3. Dünya Gazetesi Ekonomi RSS
      4. Reuters TR RSS
    yfinance'a bağımlılık sıfır.
    """
    import xml.etree.ElementTree as ET
    import urllib.parse
    from email.utils import parsedate_to_datetime

    def _zaman(pub_str):
        if not pub_str:
            return 0
        try:
            return int(parsedate_to_datetime(pub_str).timestamp())
        except Exception:
            pass
        try:
            from datetime import datetime
            return int(datetime.fromisoformat(pub_str.replace("Z", "+00:00")).timestamp())
        except Exception:
            return 0

    def _rss_cek(url, kaynak_adi, hisse_kodu="GENEL", max_items=5):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept-Language': 'tr-TR,tr;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=6) as resp:
                xml_bytes = resp.read(400_000)   # max 400 KB
            root = ET.fromstring(xml_bytes)
            sonuc = []
            for item in root.findall('.//item')[:max_items]:
                baslik = (item.findtext('title') or '').strip()
                link   = (item.findtext('link')  or '').strip()
                kaynak = item.findtext('source')  or kaynak_adi
                zaman  = _zaman(item.findtext('pubDate') or '')
                if baslik and link:
                    sonuc.append({'hisse': hisse_kodu, 'baslik': baslik,
                                  'url': link, 'kaynak': str(kaynak), 'zaman': zaman})
            return sonuc
        except Exception as e:
            logger.debug(f"RSS hata ({kaynak_adi}): {e}")
            return []

    haberler = []

    # 1. Google News — her hisse için ayrı arama
    for symbol in list(hisse_listesi)[:6]:
        code = symbol.replace(".IS", "")
        q    = urllib.parse.quote(f"{code} hisse BIST borsa")
        url  = f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"
        haberler += _rss_cek(url, "Google News", hisse_kodu=code, max_items=3)

    # 2. Genel Borsa İstanbul haberleri — Google News
    q_bist = urllib.parse.quote("Borsa İstanbul BIST hisse")
    haberler += _rss_cek(
        f"https://news.google.com/rss/search?q={q_bist}&hl=tr&gl=TR&ceid=TR:tr",
        "Google News", hisse_kodu="PİYASA", max_items=5
    )

    # 3. Bloomberg HT
    haberler += _rss_cek(
        "https://www.bloomberght.com/rss",
        "Bloomberg HT", hisse_kodu="PİYASA", max_items=6
    )

    # 4. Dünya Gazetesi Ekonomi
    haberler += _rss_cek(
        "https://www.dunya.com/rss/ekonomi.xml",
        "Dünya Gazetesi", hisse_kodu="PİYASA", max_items=5
    )

    # 5. Reuters TR
    haberler += _rss_cek(
        "https://tr.reuters.com/rssFeed/businessNews",
        "Reuters TR", hisse_kodu="PİYASA", max_items=4
    )

    # Tekrarlananları temizle, en yeni önce sırala
    seen, temiz = set(), []
    for h in sorted(haberler, key=lambda x: x['zaman'], reverse=True):
        anahtar = h['url'] or h['baslik']
        if anahtar and anahtar not in seen:
            seen.add(anahtar)
            temiz.append(h)

    return temiz[:40]


@st.cache_data(ttl=300)
def fetch_bist100_karsilastirma(portfoy_hisseleri):
    """BIST100 ve portföy günlük getiri verilerini karşılaştırma için çeker."""
    try:
        bist = fetch_stock_data("XU100.IS")
        if not bist:
            return None, None
        bist_close = bist['hist']['Close']

        # Portföy ağırlıklı ortalama getirisi
        portfoy_close = {}
        for h in portfoy_hisseleri:
            d = fetch_stock_data(h)
            if d and not d['hist'].empty:
                portfoy_close[h] = d['hist']['Close']

        if not portfoy_close:
            return bist_close, None

        # Ortak tarih aralığına normalize et
        min_len = min(len(bist_close), min(len(v) for v in portfoy_close.values()))
        bist_norm = (bist_close.iloc[-min_len:] / bist_close.iloc[-min_len] * 100)

        portfoy_df = pd.DataFrame({h: v.iloc[-min_len:].values for h, v in portfoy_close.items()})
        portfoy_ort = portfoy_df.mean(axis=1)
        portfoy_norm = (portfoy_ort / portfoy_ort.iloc[0] * 100)
        portfoy_norm.index = bist_close.iloc[-min_len:].index

        return bist_norm, portfoy_norm
    except Exception as e:
        logger.warning(f"Karşılaştırma hatası: {e}")
        return None, None


@st.cache_data(ttl=3600)
def fetch_temettu_isyatirim(symbol):
    """isyatirim.com.tr API'sinden net temettü verisini çeker (birincil kaynak)."""
    code = symbol.replace(".IS", "").upper()
    try:
        ts       = int(_time.time() * 1000)
        bugun    = datetime.now()
        bitis    = bugun.strftime("%d-%m-%Y")
        baslangic = (bugun - timedelta(days=730)).strftime("%d-%m-%Y")
        url = (
            f"https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/"
            f"HisseTemettuTablosu?hisse={code}&baslangic={baslangic}&bitis={bitis}&_={ts}"
        )
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'https://www.isyatirim.com.tr/analiz-ve-raporlar/analiz/hisse/{code}',
        })
        response = urllib.request.urlopen(req, timeout=8)
        data = json.loads(response.read().decode('utf-8'))

        kayitlar = data.get('value') or data.get('Value') or []
        if not kayitlar:
            return None

        son_1_yil  = datetime.now() - timedelta(days=365)
        son_2_yil  = datetime.now() - timedelta(days=730)
        parsed = []
        for item in kayitlar:
            # Net temettü tutarı — farklı field isimlerine karşı güvenli
            net = (item.get('NET_TEMETTU_TUTARI') or item.get('NetTemettuTutari')
                   or item.get('netTemettuTutari') or item.get('NetTemettu') or 0)
            brut = (item.get('BRUT_TEMETTU_TUTARI') or item.get('BrutTemettuTutari')
                    or item.get('brutTemettuTutari') or item.get('BrutTemettu') or 0)
            tarih_str = (item.get('TEMETTU_ODEME_TARIHI') or item.get('OdemeTarihi')
                         or item.get('Tarih') or item.get('tarih') or '')
            try:
                net_val  = float(str(net).replace(',', '.').replace(' ', ''))
                brut_val = float(str(brut).replace(',', '.').replace(' ', ''))
                if not tarih_str:
                    continue
                # Tarih formatları: dd.mm.yyyy veya yyyy-mm-dd
                for fmt in ('%d.%m.%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(tarih_str[:10], fmt)
                        break
                    except ValueError:
                        dt = None
                if dt and net_val > 0:
                    parsed.append({'dt': dt, 'net': net_val, 'brut': brut_val,
                                   'tarih_str': dt.strftime('%d.%m.%Y')})
            except Exception:
                continue

        if not parsed:
            return None

        parsed.sort(key=lambda x: x['dt'], reverse=True)
        son_1_yil_list = [p for p in parsed if p['dt'] >= son_1_yil]
        son_2_yil_list = [p for p in parsed if p['dt'] >= son_2_yil]

        if son_1_yil_list:
            net_toplam = sum(p['net'] for p in son_1_yil_list)
            n = len(son_1_yil_list)
            son_tarih = son_1_yil_list[0]['tarih_str'] + (f" ({n}x)" if n > 1 else "")
            return {'net': round(net_toplam, 6), 'tarih': son_tarih, 'kaynak': 'isyatirim'}
        elif son_2_yil_list:
            net_val = son_2_yil_list[0]['net']
            son_tarih = son_2_yil_list[0]['tarih_str'] + " *"
            return {'net': round(net_val, 6), 'tarih': son_tarih, 'kaynak': 'isyatirim'}

        return None
    except Exception as e:
        logger.warning(f"isyatirim temettü hatası ({code}): {e}")
        return None


def piyasa_acik_mi():
    """BIST'in şu an açık olup olmadığını İstanbul saatine göre döner."""
    try:
        tz      = pytz.timezone('Europe/Istanbul')
        su_an   = datetime.now(tz)
        gun     = su_an.weekday()      # 0=Pzt … 6=Paz
        saat    = su_an.hour
        dakika  = su_an.minute
        if gun >= 5:
            return False, "Hafta Sonu"
        toplam_dakika = saat * 60 + dakika
        acilis  = 10 * 60          # 10:00
        kapanis = 18 * 60          # 18:00
        if acilis <= toplam_dakika <= kapanis:
            return True, f"Açık · Kapanışa {18*60 - toplam_dakika} dk"
        elif toplam_dakika < acilis:
            return False, f"Kapalı · {10*60 - toplam_dakika} dk'ya açılıyor"
        else:
            return False, "Kapandı"
    except Exception:
        return None, "?"


def kaydet_performans_snapshot(full_data_list):
    """Her yüklemede o günkü portföy değerini performans geçmişine kaydeder."""
    if not full_data_list:
        return
    try:
        bugun       = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y-%m-%d')
        toplam_deger = round(sum(x['Değer'] for x in full_data_list), 2)
        toplam_kz   = round(sum(x['K/Z']   for x in full_data_list), 2)

        kayitlar = load_json(PERFORMANS_DOSYASI)
        # list formatına dönüştür (load_json sıralı döndürür, biz dict listesi tutuyoruz)
        if not isinstance(kayitlar, list):
            kayitlar = []

        guncellendi = False
        for k in kayitlar:
            if k.get('tarih') == bugun:
                k['deger'] = toplam_deger
                k['kz']    = toplam_kz
                guncellendi = True
                break
        if not guncellendi:
            kayitlar.append({'tarih': bugun, 'deger': toplam_deger, 'kz': toplam_kz})

        kayitlar = sorted(kayitlar, key=lambda x: x.get('tarih', ''))[-365:]
        save_json(PERFORMANS_DOSYASI, kayitlar)
        st.session_state.performans = kayitlar
    except Exception as e:
        logger.error(f"Performans kayıt hatası: {e}")


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

                bugun          = datetime.now()
                son_1_yil      = bugun - timedelta(days=365)
                son_2_yil      = bugun - timedelta(days=730)
                son_1_yil_divs = divs[divs.index >= son_1_yil]
                son_2_yil_divs = divs[divs.index >= son_2_yil]

                if not son_1_yil_divs.empty:
                    # Son 1 yılda dağıtım var → tümünü topla (brüt)
                    yillik_brut_temettu = float(son_1_yil_divs.sum())
                    yillik_net_temettu  = round(yillik_brut_temettu * 0.90, 6)
                    son_tarih = divs.index[-1].strftime('%d.%m.%Y')
                    # Birden fazla dağıtım varsa "(Nx)" göster
                    n = len(son_1_yil_divs)
                    if n > 1:
                        son_tarih += f" ({n}x)"
                elif not son_2_yil_divs.empty:
                    # 1-2 yıl arası dağıtım var → en güncel tane
                    yillik_brut_temettu = float(divs.iloc[-1])
                    yillik_net_temettu  = round(yillik_brut_temettu * 0.90, 6)
                    son_tarih = divs.index[-1].strftime('%d.%m.%Y') + " *"
                else:
                    # Hiç son verisi yok
                    yillik_net_temettu = 0.0
                    son_tarih = "-"
            except Exception as e:
                logger.warning(f"Temettü işleme hatası ({symbol}): {e}")
                yillik_net_temettu = 0.0
                son_tarih = "-"

        # isyatirim.com.tr birincil kaynak — fetch_single_item'da çağrılır
        # (nested @cache_data uyarısını önlemek için burada değil)
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

def tr_format4(val):
    """Maliyet gibi hassas değerler için 4 ondalık basamak."""
    try:
        if val is None or pd.isna(val): return "0,0000"
        return f"{val:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,0000"

def hex_rgba(hex_color, alpha=0.08):
    """6-digit hex rengi plotly uyumlu rgba() string'e çevirir."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(128,128,128,{alpha})"

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
            # isyatirim.com.tr birincil temettü kaynağı (nested cache sorununu önlemek için burada)
            try:
                isy = fetch_temettu_isyatirim(item['Hisse'])
                if isy:
                    temettu = isy['net']
                    tarih   = isy['tarih']
            except Exception:
                pass
        else:
            c = item['Maliyet']; pc = c
            sinyal = "⚠️ VERİ YOK"
            rsi_val = 0.0; macd_h = 0.0; bb_pct = 50.0
            temettu = 0.0; tarih = "-"

    adet_int = int(item['Adet'])

    # Son 7 günlük kapanış verisi (sparkline için)
    spark_prices = []
    if d and not d['hist'].empty:
        try:
            spark_prices = [round(float(v), 4) for v in d['hist']['Close'].iloc[-7:].tolist()]
        except Exception:
            spark_prices = []

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
        "Tarih": tarih,
        "Sparkline": spark_prices,
    }

# ==========================================
# 1. TEMA VE CSS
# ==========================================
st.set_page_config(page_title="Borsa Takip", page_icon="📈", layout="wide")

# Yenileme süresi session_state'ten okunur (sidebar'dan ayarlanabilir)
if 'yenileme_suresi' not in st.session_state:
    st.session_state.yenileme_suresi = 60   # saniye

st_autorefresh(interval=st.session_state.yenileme_suresi * 1000, key="datarefresh")

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

FONT_SECENEKLERI = {
    "Inter (Varsayılan)":    ("Inter", "https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"),
    "Roboto":                ("Roboto", "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"),
    "Poppins":               ("Poppins", "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap"),
    "Nunito":                ("Nunito", "https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap"),
    "Raleway":               ("Raleway", "https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap"),
    "Source Code Pro":       ("Source Code Pro", "https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600&display=swap"),
    "Exo 2":                 ("Exo 2", "https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600&display=swap"),
    "Orbitron (Sci-Fi)":     ("Orbitron", "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap"),
    "Share Tech Mono":       ("Share Tech Mono", "https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap"),
    "Syne":                  ("Syne", "https://fonts.googleapis.com/css2?family=Syne:wght@400;700&display=swap"),
}

with st.sidebar:
    st.header("🎨 Tema Galerisi")
    # session_state ile seçim kalıcı kalır (tema değişince rerun da etkilemez)
    if 'tema_secim' not in st.session_state:
        st.session_state.tema_secim = "Galaksi (VIP)"
    if 'font_secim' not in st.session_state:
        st.session_state.font_secim = "Inter (Varsayılan)"

    tema = st.selectbox(
        "Görünüm Seç", tema_isimleri,
        index=tema_isimleri.index(st.session_state.tema_secim)
              if st.session_state.tema_secim in tema_isimleri else 2,
        key="tema_widget"
    )
    st.session_state.tema_secim = tema

    secili_font_adi = st.selectbox(
        "🔤 Font Seç", list(FONT_SECENEKLERI.keys()),
        index=list(FONT_SECENEKLERI.keys()).index(st.session_state.font_secim)
              if st.session_state.font_secim in FONT_SECENEKLERI else 0,
        key="font_widget"
    )
    st.session_state.font_secim = secili_font_adi
    secili_font, secili_font_url = FONT_SECENEKLERI[secili_font_adi]

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
    @import url('{secili_font_url}');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700&display=swap');
    .stApp {{ background-color: {t_sec['bg']}; color: {t_sec['text']}; font-family: '{secili_font}', sans-serif; }}
    [data-testid="stMetric"] {{ background: {t_sec['box']}; padding: 20px !important; border-radius: 12px !important; border: 1px solid {t_sec['accent']} !important; text-align: center; }}
    .kral-table {{ width: 100%; border-collapse: collapse; background: {t_sec['box']}22; margin-top: 10px; border: 1px solid {t_sec['accent']}33; border-radius: 10px; overflow-x: auto; display: block; font-family: '{secili_font}', sans-serif; }}
    .kral-table th {{ padding: {st.session_state.tablo_padding}px; text-align: left; background: {t_sec['accent']}22; color: {t_sec['accent']}; font-weight: 700; font-size: {st.session_state.tablo_font}px; border-bottom: 2px solid {t_sec['accent']}44; white-space: nowrap; }}
    .kral-table td {{ padding: {st.session_state.tablo_padding}px; border-bottom: 1px solid {t_sec['accent']}11; color: {t_sec['text']}; font-size: {st.session_state.tablo_font}px; white-space: nowrap; }}
    .ticker-wrapper {{ width: 100%; overflow: hidden; background: {t_sec['box']}; border-radius: 8px; margin-bottom: 30px; padding: 15px 0; border: 1px solid {t_sec['accent']}44; }}
    .ticker-content {{ display: flex; animation: ticker 25s linear infinite; white-space: nowrap; gap: 60px; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .up {{ color: #00e676; font-weight: bold; }} .down {{ color: #ff1744; font-weight: bold; }}
    .alarm-aktif {{ color: #ff1744; font-weight: bold; animation: blink 1s step-start infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .indikator-bar {{ display: inline-block; height: 8px; border-radius: 4px; }}
    .vy-kart {{ background: {t_sec['box']}; border: 1px solid {t_sec['accent']}33; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; }}
    .vy-etiket {{ font-size: 10px; opacity: 0.5; margin-bottom: 2px; letter-spacing: 0.8px; }}
    .vy-deger {{ font-size: 13px; font-weight: 600; }}
    {'/* MOBİL MOD */ .kral-table th, .kral-table td { padding: 6px 8px !important; font-size: 11px !important; } [data-testid="stMetric"] { padding: 10px !important; } .ticker-content { gap: 30px; }' if st.session_state.mobil_mod else ''}
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

# --- ONBOARDING (portföy boşsa) ---
if not st.session_state.portfoy:
    st.markdown(
        f"<div style='background:{t_sec['box']};border:2px dashed {t_sec['accent']}44;"
        f"border-radius:12px;padding:24px 28px;text-align:center;margin:16px 0;'>"
        f"<div style='font-size:32px;margin-bottom:12px;'>📈</div>"
        f"<div style='font-size:18px;font-weight:700;color:{t_sec['accent']};margin-bottom:8px;'>"
        f"Portföyünü oluşturmaya başla</div>"
        f"<div style='font-size:13px;opacity:0.7;margin-bottom:16px;'>"
        f"Sol menüden hisse ekle — GARAN.IS, THYAO.IS, AKBNK.IS gibi</div>"
        f"<div style='display:flex;justify-content:center;gap:12px;flex-wrap:wrap;'>"
        + "".join(
            f"<span style='background:{t_sec['accent']}22;color:{t_sec['accent']};"
            f"border-radius:6px;padding:5px 12px;font-size:12px;font-weight:600;'>{h}</span>"
            for h in ["GARAN.IS", "THYAO.IS", "AKBNK.IS", "EREGL.IS", "SASA.IS"]
        ) +
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

piyasa_izleme = {
    "BIST 100":  "XU100.IS",
    "USD/TRY":   "USDTRY=X",
    "EUR/TRY":   "EURTRY=X",
    "ONS ALTIN": "GC=F",
    "ONS GÜMÜŞ": "SI=F",
    "BTC":       "BTC-USD",
}
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

# Gram Altın ve Gram Gümüş — önbellek sayesinde ek API çağrısı yok
try:
    _gc     = fetch_stock_data("GC=F")
    _si     = fetch_stock_data("SI=F")
    _usdtry = fetch_stock_data("USDTRY=X")
    if _gc and _usdtry:
        _ust  = float(_usdtry['hist']['Close'].iloc[-1])
        _gc_s = float(_gc['hist']['Close'].iloc[-1])
        _gc_p = float(_gc['hist']['Close'].iloc[-2])
        _gr_a = _gc_s * _ust / 31.1035
        _gr_ap = _gc_p * _ust / 31.1035
        _deg_a = ((_gr_a - _gr_ap) / _gr_ap) * 100
        ticker_content += (
            f'<div style="text-align:center;">'
            f'<div>GRAM ALTIN</div>'
            f'<div style="font-weight:bold;">{tr_format(_gr_a)}</div>'
            f'<div class="{"up" if _deg_a>=0 else "down"}">{_deg_a:+.2f}%</div>'
            f'</div>'
        )
    if _si and _usdtry:
        _ust  = float(_usdtry['hist']['Close'].iloc[-1])
        _si_s = float(_si['hist']['Close'].iloc[-1])
        _si_p = float(_si['hist']['Close'].iloc[-2])
        _gr_g = _si_s * _ust / 31.1035
        _gr_gp = _si_p * _ust / 31.1035
        _deg_g = ((_gr_g - _gr_gp) / _gr_gp) * 100
        ticker_content += (
            f'<div style="text-align:center;">'
            f'<div>GRAM GÜMÜŞ</div>'
            f'<div style="font-weight:bold;">{tr_format(_gr_g)}</div>'
            f'<div class="{"up" if _deg_g>=0 else "down"}">{_deg_g:+.2f}%</div>'
            f'</div>'
        )
except Exception as e:
    logger.warning(f"Gram fiyat hesaplama hatası: {e}")
st.markdown(ticker_content + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 3. PARALEL VERİ HAZIRLAMA
# ==========================================
BIST_FULL = sorted([
    "A1CAP.IS","ACSEL.IS","ADEL.IS","ADESE.IS","AEFES.IS","AFYON.IS","AGESA.IS","AGHOL.IS",
    "AGROT.IS","AHGAZ.IS","AKBNK.IS","AKCNS.IS","AKENR.IS","AKFGY.IS","AKFYE.IS","AKGRT.IS",
    "AKMGY.IS","AKSA.IS","AKSEN.IS","ALARK.IS","ALBRK.IS","ALFAS.IS","ALGYO.IS","ALKIM.IS",
    "ALMAD.IS","ANELE.IS","ANGEN.IS","ANHYT.IS","ANSGR.IS","ARCLK.IS","ARDYZ.IS","ARENA.IS",
    "ARSAN.IS","ASGYO.IS","ASELS.IS","ASTOR.IS","ASUZU.IS","ATEKS.IS","ATLAS.IS","ATSYH.IS",
    "AVHOL.IS","AVOD.IS","AYDEM.IS","AYEN.IS","AYGAZ.IS","BAGFS.IS","BAKAB.IS","BALAT.IS",
    "BANVT.IS","BASGZ.IS","BAYRK.IS","BEGYO.IS","BERA.IS","BFREN.IS","BIMAS.IS","BINHO.IS",
    "BIOEN.IS","BIZIM.IS","BJKAS.IS","BLCYT.IS","BMSTL.IS","BNTAS.IS","BOBET.IS","BORLS.IS",
    "BORSK.IS","BOSSA.IS","BRISA.IS","BRKO.IS","BRKSN.IS","BRKVY.IS","BRLSM.IS","BRMEN.IS",
    "BRYAT.IS","BSOKE.IS","BTCIM.IS","BUCIM.IS","BURCE.IS","BURVA.IS","BVSAN.IS","BYDNR.IS",
    "CANTE.IS","CASA.IS","CATES.IS","CCOLA.IS","CELHA.IS","CEMAS.IS","CEMTS.IS","CEVNY.IS",
    "CIMSA.IS","CLEBI.IS","CMBTN.IS","CMENT.IS","CONSE.IS","COSMO.IS","CRDFA.IS","CRFSA.IS",
    "CUSAN.IS","CVKMD.IS","CWENE.IS","DAGHL.IS","DAGI.IS","DAPGM.IS","DARDL.IS","DENGE.IS",
    "DERAS.IS","DERIM.IS","DESA.IS","DESPC.IS","DEVA.IS","DGGYO.IS","DIRIT.IS","DITAS.IS",
    "DMSAS.IS","DOAS.IS","DOCO.IS","DOHOL.IS","DOKTA.IS","DURDO.IS","DYOBY.IS","DZGYO.IS",
    "EBEBK.IS","ECILC.IS","ECZYT.IS","EDATA.IS","EDIP.IS","EGEEN.IS","EGEPO.IS","EGGUB.IS",
    "EGPRO.IS","EGSER.IS","EKGYO.IS","EKIZ.IS","EKOS.IS","EKSUN.IS","ELITE.IS","EMKEL.IS",
    "ENERY.IS","ENJSA.IS","ENKAI.IS","ERBOS.IS","EREGL.IS","ERSU.IS","ESCOM.IS","ESEN.IS",
    "EUPWR.IS","EUREN.IS","EYGYO.IS","FMIZP.IS","FONET.IS","FORMT.IS","FORTE.IS","FROTO.IS",
    "FZLGY.IS","GARAN.IS","GENTS.IS","GEREL.IS","GESAN.IS","GIPTA.IS","GLBMD.IS","GLCVY.IS",
    "GLRYH.IS","GLYHO.IS","GMTAS.IS","GOKNR.IS","GOLTS.IS","GOODY.IS","GOZDE.IS","GRNYO.IS",
    "GRSEL.IS","GSDDE.IS","GSDHO.IS","GUBRF.IS","GWIND.IS","GZNMI.IS","HALKB.IS","HATEK.IS",
    "HATSN.IS","HEDEF.IS","HEKTS.IS","HKTM.IS","HLGYO.IS","HTTBT.IS","HUBVC.IS","HUNER.IS",
    "HURGZ.IS","ICBCT.IS","IDAS.IS","IDEAS.IS","IDGYO.IS","IEYHO.IS","IHEVA.IS","IHGZT.IS",
    "IHLAS.IS","IHLGM.IS","IHYAY.IS","IMASM.IS","INDES.IS","INFO.IS","INTEM.IS","IPEKE.IS",
    "ISATR.IS","ISBTR.IS","ISCTR.IS","ISDMR.IS","ISFIN.IS","ISGSY.IS","ISGYO.IS","ISMEN.IS",
    "ISSEN.IS","ISYAT.IS","ITTFH.IS","IZENR.IS","IZFAS.IS","IZINV.IS","IZMDC.IS","JANTS.IS",
    "KAPLM.IS","KAREL.IS","KARSN.IS","KARTN.IS","KARYE.IS","KATMR.IS","KAYSE.IS","KBCOR.IS",
    "KCAER.IS","KCHOL.IS","KFEIN.IS","KGYO.IS","KIMMR.IS","KLGYO.IS","KLMSN.IS","KLNMA.IS",
    "KLKIM.IS","KLRHO.IS","KLSYN.IS","KLYAS.IS","KMEPU.IS","KMPUR.IS","KNFRT.IS","KONTR.IS",
    "KONYA.IS","KORDS.IS","KOZAA.IS","KOZAL.IS","KRDMA.IS","KRDMB.IS","KRDMD.IS","KRGYO.IS",
    "KRONT.IS","KRPLS.IS","KRSTL.IS","KRTEK.IS","KRVGD.IS","KSTUR.IS","KUTPO.IS","KUVVA.IS",
    "KUYAS.IS","KZBGY.IS","KZGYO.IS","LIDER.IS","LIDFA.IS","LINK.IS","LMKDC.IS","LOGAS.IS",
    "LOGO.IS","LRSHO.IS","LUKSK.IS","MAALT.IS","MACKO.IS","MAGEN.IS","MAKIM.IS","MAKTK.IS",
    "MANAS.IS","MARKA.IS","MARTI.IS","MAVI.IS","MEDTR.IS","MEGAP.IS","MEKAG.IS","MEPET.IS",
    "MERCN.IS","MERKO.IS","METRO.IS","METUR.IS","MHRGY.IS","MIATK.IS","MIPAZ.IS","MNDRS.IS",
    "MNDTR.IS","MOBTL.IS","MPARK.IS","MRGYO.IS","MRSHL.IS","MSGYO.IS","MTRKS.IS","MUDO.IS",
    "MZHLD.IS","NATEN.IS","NETAS.IS","NIBAS.IS","NTGAZ.IS","NTHOL.IS","NUGYO.IS","NUHCM.IS",
    "OBAMS.IS","OBASE.IS","ODAS.IS","ONCSM.IS","ORCAY.IS","ORGE.IS","ORMA.IS","OSMEN.IS",
    "OSTIM.IS","OTKAR.IS","OYAKC.IS","OYAYO.IS","OYLUM.IS","OYYAT.IS","OZGYO.IS","OZKGY.IS",
    "OZRDN.IS","OZSUB.IS","PAGYO.IS","PAMEL.IS","PAPIL.IS","PARSN.IS","PASEU.IS","PATEK.IS",
    "PCILT.IS","PEGYO.IS","PEKGY.IS","PENTA.IS","PETKM.IS","PETUN.IS","PGSUS.IS","PINSU.IS",
    "PKART.IS","PKENT.IS","PNLSN.IS","PNSUT.IS","POLHO.IS","POLTK.IS","PRKAB.IS","PRKME.IS",
    "PRZMA.IS","PSDTC.IS","PSGYO.IS","QNBFB.IS","QNBFL.IS","QUAGR.IS","RALYH.IS","RAYYS.IS",
    "REEDR.IS","RNPOL.IS","RODRG.IS","ROYAL.IS","RTALB.IS","RUBNS.IS","RYGYO.IS","RYSAS.IS",
    "SAHOL.IS","SAMAT.IS","SANEL.IS","SANFO.IS","SANIC.IS","SARKY.IS","SASA.IS","SAYAS.IS",
    "SDTTR.IS","SEGYO.IS","SEKFK.IS","SEKOK.IS","SELEC.IS","SELGD.IS","SERVE.IS","SEYKM.IS",
    "SILVR.IS","SISE.IS","SKBNK.IS","SKTAS.IS","SKYMD.IS","SKYLP.IS","SMART.IS","SMRTG.IS",
    "SNGYO.IS","SNICA.IS","SNKPA.IS","SOKM.IS","SONME.IS","SRVGY.IS","SUMAS.IS","SUNTK.IS",
    "SURGY.IS","SUWEN.IS","TABGD.IS","TAPDI.IS","TARKM.IS","TATEN.IS","TATGD.IS","TAVHL.IS",
    "TBORG.IS","TCELL.IS","TDGYO.IS","TEKTU.IS","TERA.IS","TETMT.IS","TEZOL.IS","TGSAS.IS",
    "THYAO.IS","TIRE.IS","TKFEN.IS","TKNSA.IS","TMSN.IS","TOASO.IS","TRCAS.IS","TRGYO.IS",
    "TRILC.IS","TSKB.IS","TSPOR.IS","TTKOM.IS","TTRAK.IS","TUCLK.IS","TUKAS.IS","TUPRS.IS",
    "TURSG.IS","UFUK.IS","ULAS.IS","ULKER.IS","ULUFA.IS","ULUSE.IS","VAKBN.IS","VAKFN.IS",
    "VAKKO.IS","VANGD.IS","VBTYM.IS","VERTU.IS","VERUS.IS","VESBE.IS","VESTL.IS","VKGYO.IS",
    "VKING.IS","VRGYO.IS","YAPRK.IS","YATAS.IS","YAYLA.IS","YEOTK.IS","YESIL.IS","YGGYO.IS",
    "YGYO.IS","YKBNK.IS","YONGA.IS","YOTAS.IS","YUNSA.IS","YYLGD.IS","ZEDUR.IS","ZOREN.IS",
    "ZRGYO.IS",
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

# Günlük performans snapshot kaydet
kaydet_performans_snapshot(full_data)

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
tab_tr, tab_fon, tab_div, tab_ipo, tab_analiz, tab_haberler, tab_temel, tab_takvim, tab_olcek = st.tabs([
    "🇹🇷 TÜRK BORSASI",
    "📊 YATIRIM FONLARI",
    "💰 TEMETTÜ GELİRİ",
    "🚀 HALKA ARZ",
    "📈 ANALİZ",
    "📰 HABERLER",
    "🏦 TEMEL VERİLER",
    "📅 EKONOMİK TAKVİM",
    "📐 AYARLAR",
])

with st.sidebar:

    # --- KARANLIK MOD TOGGLE ---
    _dm_col1, _dm_col2 = st.columns([3, 1])
    _dm_col1.markdown(
        f"<div style='padding-top:6px;font-size:12px;color:{t_sec['text']};opacity:0.7;'>"
        f"{'🌙 Karanlık Mod' if st.session_state.dark_mode else '☀️ Açık Mod'}</div>",
        unsafe_allow_html=True
    )
    if _dm_col2.button("⇄", key="dm_toggle", help="Karanlık/Açık mod"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        # Tema'yı otomatik ayarla
        if st.session_state.dark_mode:
            if st.session_state.tema_secim in ["Siyah-Beyaz (Klasik)", "Vanilya Gökyüzü"]:
                st.session_state.tema_secim = "Galaksi (VIP)"
        else:
            st.session_state.tema_secim = "Siyah-Beyaz (Klasik)"
        st.rerun()

    # --- PİYASA DURUMU ---
    _acik, _durum_msg = piyasa_acik_mi()
    _durum_color = "#00e676" if _acik else "#ff1744"
    _durum_icon  = "🟢" if _acik else "🔴"
    st.markdown(
        f"<div style='background:{t_sec['box']};border:1px solid {_durum_color}55;"
        f"border-radius:10px;padding:8px 14px;margin-bottom:8px;"
        f"display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-size:11px;color:{t_sec['text']};opacity:0.6;'>BIST DURUMU</span>"
        f"<span style='font-size:11px;color:{_durum_color};font-weight:700;'>{_durum_icon} {_durum_msg}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- MİNİ PORTFÖY ÖZETİ ---
    if full_data:
        _deger   = sum(x['Değer']     for x in full_data)
        _kz      = sum(x['K/Z']       for x in full_data)
        _gunluk  = sum(x['DailyDiff'] for x in full_data)
        _pozisyon = len(full_data)
        _kz_color = "#00e676" if _kz     >= 0 else "#ff1744"
        _gd_color = "#00e676" if _gunluk >= 0 else "#ff1744"
        _box  = t_sec['box']
        _acc  = t_sec['accent']
        _txt  = t_sec['text']
        st.markdown(f"""
        <div style='background:{_box};border:1px solid {_acc}55;border-radius:12px;padding:14px 16px;margin-bottom:4px;'>
            <div style='color:{_acc};font-weight:700;font-size:11px;letter-spacing:1.5px;margin-bottom:10px;'>
                📊 PORTFÖY ÖZETİ
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
                <span style='color:{_txt};opacity:0.6;font-size:11px;'>Toplam Değer</span>
                <span style='color:{_txt};font-weight:600;font-size:12px;'>{tr_format(_deger)} ₺</span>
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
                <span style='color:{_txt};opacity:0.6;font-size:11px;'>Toplam K/Z</span>
                <span style='color:{_kz_color};font-weight:700;font-size:12px;'>{tr_format(_kz)} ₺</span>
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
                <span style='color:{_txt};opacity:0.6;font-size:11px;'>Günlük</span>
                <span style='color:{_gd_color};font-weight:700;font-size:12px;'>{tr_format(_gunluk)} ₺</span>
            </div>
            <div style='border-top:1px solid {_acc}22;margin-top:8px;padding-top:8px;display:flex;justify-content:space-between;'>
                <span style='color:{_txt};opacity:0.5;font-size:10px;'>Pozisyon</span>
                <span style='color:{_acc};font-size:10px;font-weight:600;'>{_pozisyon} adet</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- YENİ VARLIK EKLE ---
    _acc2 = t_sec['accent']
    st.markdown(f"<div style='color:{_acc2};font-weight:700;font-size:13px;letter-spacing:1px;margin-bottom:8px;'>➕ YENİ VARLIK EKLE</div>", unsafe_allow_html=True)
    piyasa_sec = st.radio("Piyasa", ["Türk Borsası", "Yatırım Fonu"], horizontal=True)
    if piyasa_sec == "Türk Borsası":
        hisse_sec = st.selectbox("Hisse Seç", BIST_FULL)
    else:
        hisse_sec = st.selectbox("Fon Seç", FON_LIST + ["DİĞER"])
    if hisse_sec == "DİĞER":
        hisse_sec = st.text_input("Fon Kodu").upper()

    _col_a, _col_b = st.columns(2)
    adet_sec    = _col_a.number_input("Adet",    min_value=0,   step=1,  label_visibility="visible")
    maliyet_sec = _col_b.number_input("Maliyet (₺)", min_value=0.0, format="%.4f", label_visibility="visible")

    if st.button("🚀 Portföye Ekle", use_container_width=True):
        st.session_state.portfoy.append({
            "Piyasa": piyasa_sec, "Hisse": hisse_sec,
            "Adet": int(adet_sec), "Maliyet": float(maliyet_sec)
        })
        st.session_state.portfoy = sorted(st.session_state.portfoy, key=lambda x: x['Hisse'])
        save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
        st.rerun()

    st.divider()

    # --- DÖVİZ ÇEVİRİCİ ---
    _acc3 = t_sec['accent']
    st.markdown(f"<div style='color:{_acc3};font-weight:700;font-size:13px;letter-spacing:1px;margin-bottom:8px;'>💱 DÖVİZ ÇEVİRİCİ</div>", unsafe_allow_html=True)
    try:
        _d_usd = fetch_stock_data("USDTRY=X")
        _d_eur = fetch_stock_data("EURTRY=X")
        _d_gc  = fetch_stock_data("GC=F")
        _d_si  = fetch_stock_data("SI=F")
        _usd_try_r = float(_d_usd['hist']['Close'].iloc[-1]) if _d_usd else 0.0
        _eur_try_r = float(_d_eur['hist']['Close'].iloc[-1]) if _d_eur else 0.0
        _gc_r      = float(_d_gc['hist']['Close'].iloc[-1])  if _d_gc  else 0.0
        _si_r      = float(_d_si['hist']['Close'].iloc[-1])  if _d_si  else 0.0
        _gram_altin = _gc_r * _usd_try_r / 31.1035 if _usd_try_r and _gc_r else 0.0
        _gram_gumus = _si_r * _usd_try_r / 31.1035 if _usd_try_r and _si_r else 0.0

        _doviz_rates = {
            "TRY (₺)":          1.0,
            "USD ($)":          _usd_try_r,
            "EUR (€)":          _eur_try_r,
            "Gram Altın":       _gram_altin,
            "Gram Gümüş":       _gram_gumus,
        }
        _cv1, _cv2 = st.columns(2)
        _cv_miktar = _cv1.number_input("Miktar", value=1.0, min_value=0.0, format="%.4f", key="cv_miktar")
        _cv_kaynak = _cv2.selectbox("Kaynak", list(_doviz_rates.keys()), key="cv_kaynak")
        _cv_hedef  = st.selectbox("Hedef", list(_doviz_rates.keys()), index=3, key="cv_hedef")

        if _doviz_rates[_cv_kaynak] > 0 and _doviz_rates[_cv_hedef] > 0:
            _sonuc = _cv_miktar * _doviz_rates[_cv_kaynak] / _doviz_rates[_cv_hedef]
            st.markdown(
                f"<div style='background:{t_sec['box']};border:1px solid {_acc3}44;"
                f"border-radius:8px;padding:10px 14px;text-align:center;'>"
                f"<span style='color:{t_sec['text']};opacity:0.6;font-size:11px;'>{tr_format(_cv_miktar)} {_cv_kaynak}</span><br>"
                f"<span style='color:{_acc3};font-size:18px;font-weight:700;'>{tr_format4(_sonuc)} {_cv_hedef}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    except Exception as _e:
        st.caption("Kur verisi yükleniyor...")


    # --- VERİ KORUMA PANELİ ---
    _acc_v = t_sec['accent']
    _txt_v = t_sec['text']
    _box_v = t_sec['box']

    # Kaç hisse var ve JSON nerede?
    _hisse_sayisi = len(st.session_state.portfoy)
    _json_var     = os.path.exists(PORTFOY_DOSYASI)
    _bak_var      = os.path.exists(PORTFOY_DOSYASI + ".bak")
    _json_boyut   = round(os.path.getsize(PORTFOY_DOSYASI) / 1024, 1) if _json_var else 0
    _durum_renk   = "#00e676" if _json_var and _hisse_sayisi > 0 else "#ff1744"

    st.markdown(
        f"<div style='background:{_box_v};border:1px solid {_acc_v}33;"
        f"border-radius:10px;padding:10px 14px;'>"
        f"<div style='color:{_acc_v};font-weight:700;font-size:11px;letter-spacing:1px;margin-bottom:8px;'>"
        f"💾 VERİ KORUMA"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
        f"<span style='font-size:10px;opacity:0.55;'>Kayıtlı hisse</span>"
        f"<span style='color:{_durum_renk};font-size:10px;font-weight:700;'>{_hisse_sayisi} adet</span>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
        f"<span style='font-size:10px;opacity:0.55;'>JSON dosyası</span>"
        f"<span style='font-size:10px;color:{_durum_renk};'>{'✅ Var · ' + str(_json_boyut) + ' KB' if _json_var else '❌ Bulunamadı'}</span>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;'>"
        f"<span style='font-size:10px;opacity:0.55;'>Yedek (.bak)</span>"
        f"<span style='font-size:10px;color:{'#00e676' if _bak_var else '#888'};'>{'✅ Var' if _bak_var else '—'}</span>"
        f"</div>"
        f"<div style='font-size:9px;opacity:0.35;margin-top:6px;word-break:break-all;'>"
        f"{os.path.dirname(PORTFOY_DOSYASI)}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # El ile yedek al butonu
    if st.button("📁 Şimdi Yedek Al", key="manuel_yedek", use_container_width=True):
        try:
            import shutil, zipfile
            _zip_adi = os.path.join(_VERI_DIZIN,
                f"portfoy_yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            with zipfile.ZipFile(_zip_adi, 'w', zipfile.ZIP_DEFLATED) as zf:
                for _dosya in [PORTFOY_DOSYASI, IPO_DOSYASI, ALARM_DOSYASI,
                               PERFORMANS_DOSYASI, NOTLAR_DOSYASI]:
                    if os.path.exists(_dosya):
                        zf.write(_dosya, os.path.basename(_dosya))
            st.success(f"✅ Yedek oluşturuldu: {os.path.basename(_zip_adi)}")
        except Exception as _ez:
            st.error(f"Yedek alınamadı: {_ez}")

    st.divider()

    # --- OTOMATİK YENİLEME ---
    _acc_yr = t_sec['accent']
    st.markdown(
        f"<div style='color:{_acc_yr};font-weight:700;font-size:11px;"
        f"letter-spacing:1px;margin-bottom:6px;'>🔄 OTOMATİK YENİLEME</div>",
        unsafe_allow_html=True
    )
    _sure_sec = st.select_slider(
        "Yenileme",
        options=[15, 30, 60, 120, 300],
        value=st.session_state.get('yenileme_suresi', 60),
        format_func=lambda x: f"{x}sn" if x < 60 else f"{x//60}dk",
        key="yenileme_slider",
        label_visibility="collapsed"
    )
    if _sure_sec != st.session_state.get('yenileme_suresi', 60):
        st.session_state.yenileme_suresi = _sure_sec
        st.rerun()
    st.caption(f"Her {_sure_sec}sn'de otomatik yenileniyor")

    st.divider()

    # --- GİRİŞ / KULLANICI SİSTEMİ ---
    _acc_us = t_sec['accent']
    st.markdown(
        f"<div style='color:{_acc_us};font-weight:700;font-size:11px;"
        f"letter-spacing:1px;margin-bottom:6px;'>👤 KULLANICI</div>",
        unsafe_allow_html=True
    )

    # Basit PIN tabanlı kullanıcı sistemi (veritabanı gerektirmez)
    if 'kullanici_giris' not in st.session_state:
        st.session_state.kullanici_giris = False
    if 'kullanici_adi' not in st.session_state:
        st.session_state.kullanici_adi = ""

    # Kullanıcı listesi JSON'dan oku
    _KULLANICI_DOSYASI = _veri_yolu("kullanicilar.json")

    def _kullanicilar_yukle():
        if not os.path.exists(_KULLANICI_DOSYASI):
            # İlk açılışta default admin kullanıcısı oluştur
            import hashlib
            _varsayilan = [{"kullanici": "admin", "pin_hash": hashlib.sha256("1234".encode()).hexdigest(), "rol": "admin"}]
            save_json(_KULLANICI_DOSYASI, _varsayilan)
            return _varsayilan
        try:
            with open(_KULLANICI_DOSYASI, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _pin_dogrula(kullanici, pin):
        import hashlib
        _kl = _kullanicilar_yukle()
        _ph = hashlib.sha256(pin.encode()).hexdigest()
        return any(k['kullanici'] == kullanici and k['pin_hash'] == _ph for k in _kl)

    if not st.session_state.kullanici_giris:
        with st.form("giris_form", clear_on_submit=True):
            _giris_kul = st.text_input("Kullanıcı adı", placeholder="admin", key="giris_kul")
            _giris_pin = st.text_input("PIN", type="password", placeholder="••••", key="giris_pin",
                                        help="Varsayılan: admin / 1234")
            if st.form_submit_button("🔓 Giriş Yap", use_container_width=True):
                if _pin_dogrula(_giris_kul.strip(), _giris_pin.strip()):
                    st.session_state.kullanici_giris = True
                    st.session_state.kullanici_adi   = _giris_kul.strip()
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya PIN hatalı.")
        st.caption("İlk giriş: kullanıcı **admin**, PIN **1234** · Ayarlar sekmesinden değiştir")
    else:
        _us1, _us2 = st.columns([3, 1])
        _us1.markdown(
            f"<div style='font-size:11px;color:{_acc_us};'>"
            f"👤 <b>{st.session_state.kullanici_adi}</b> giriş yaptı</div>",
            unsafe_allow_html=True
        )
        if _us2.button("🚪", key="cikis_btn", help="Çıkış Yap"):
            st.session_state.kullanici_giris = False
            st.session_state.kullanici_adi   = ""
            st.rerun()


# ==========================================
# YÖNETİM FONKSİYONU — Kart Bazlı Yeni Tasarım
# ==========================================
def varlik_yonetimi_render(df_local):
    # Güvenlik kalkanı: None, boş veya DataFrame olmayan girdi
    if df_local is None or not isinstance(df_local, pd.DataFrame) or df_local.empty:
        st.info("Gösterilecek varlık bulunamadı.")
        return

    acc = t_sec['accent']
    box = t_sec['box']
    txt = t_sec['text']
    with st.expander("🛠️ VARLIK YÖNETİMİ"):
        for _, r in df_local.iterrows():
            try:
                kz_color   = "#00e676" if r.get('K/Z', 0) >= 0 else "#ff1744"
                kz_pct     = ((r.get('Güncel', 0) - r.get('Maliyet', 0)) / r.get('Maliyet', 1) * 100) if r.get('Maliyet', 0) > 0 else 0.0
                sinyal_str = str(r.get('Sinyal', '—'))

                # Bilgi kartı
                st.markdown(
                    f"<div class='vy-kart'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>"
                    f"  <span style='color:{acc};font-weight:700;font-size:15px;letter-spacing:0.5px;'>{r.get('Hisse','?')}</span>"
                    f"  <span style='color:{txt};opacity:0.45;font-size:10px;letter-spacing:1px;'>{str(r.get('Piyasa','')).upper()}</span>"
                    f"</div>"
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;'>"
                    f"  <div><div class='vy-etiket'>ADET</div>"
                    f"      <div class='vy-deger' style='color:{txt};'>{r.get('Adet',0)}</div></div>"
                    f"  <div><div class='vy-etiket'>MALİYET</div>"
                    f"      <div class='vy-deger' style='color:{txt};'>{tr_format4(r.get('Maliyet',0))} ₺</div></div>"
                    f"  <div><div class='vy-etiket'>GÜNCEL</div>"
                    f"      <div class='vy-deger' style='color:{acc};'>{tr_format4(r.get('Güncel',0))} ₺</div></div>"
                    f"  <div><div class='vy-etiket'>K/Z</div>"
                    f"      <div class='vy-deger' style='color:{kz_color};'>{tr_format(r.get('K/Z',0))} ₺"
                    f"          <span style='font-size:10px;opacity:0.8;'> ({kz_pct:+.1f}%)</span></div></div>"
                    f"</div>"
                    f"<div style='margin-top:8px;padding-top:8px;border-top:1px solid {acc}18;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"  <span style='font-size:11px;opacity:0.45;'>Sinyal: {sinyal_str}</span>"
                    f"  <span style='font-size:11px;opacity:0.45;'>Toplam: {tr_format(r.get('Değer',0))} ₺</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Düzenleme satırı
                _row_id = int(r.get('id', 0))
                ec1, ec2, ec3, ec4 = st.columns([2, 2, 1, 1])
                y_adet    = ec1.number_input("Yeni Adet",       value=int(r.get('Adet', 0)),       step=1,       key=f"a_{_row_id}")
                y_maliyet = ec2.number_input("Yeni Maliyet (₺)", value=float(r.get('Maliyet', 0.0)), format="%.4f", key=f"m_{_row_id}")
                ec3.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                ec4.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

                if ec3.button("💾 Kaydet", key=f"s_{_row_id}", use_container_width=True):
                    if _row_id < len(st.session_state.portfoy):
                        st.session_state.portfoy[_row_id]['Adet']    = y_adet
                        st.session_state.portfoy[_row_id]['Maliyet'] = y_maliyet
                        st.session_state.portfoy = sorted(st.session_state.portfoy, key=lambda x: x['Hisse'])
                        save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
                        st.rerun()
                if ec4.button("❌ Sil", key=f"d_{_row_id}", use_container_width=True):
                    if _row_id < len(st.session_state.portfoy):
                        st.session_state.portfoy.pop(_row_id)
                        save_json(PORTFOY_DOSYASI, st.session_state.portfoy)
                        st.rerun()
                st.markdown("<div style='margin-bottom:4px;'></div>", unsafe_allow_html=True)

            except Exception as _ve:
                logger.error(f"Varlık yönetimi render hatası ({r.get('Hisse','?')}): {_ve}")
                st.warning(f"⚠️ {r.get('Hisse','?')} için gösterim hatası: {_ve}")

def make_sparkline_svg(prices, width=80, height=28, renk_kz=None):
    """
    Verilen fiyat listesinden inline SVG sparkline üretir.
    renk_kz: None ise ilk-son fiyata göre otomatik renk seçer.
    """
    if not prices or len(prices) < 2:
        return "<span style='opacity:0.25;font-size:10px;'>—</span>"

    try:
        mn   = min(prices)
        mx   = max(prices)
        span = mx - mn if mx != mn else 1.0
        pad  = 3   # üst/alt boşluk (px)

        # x koordinatları eşit aralıklı
        xs = [round(i * (width - 1) / (len(prices) - 1), 2) for i in range(len(prices))]
        # y koordinatları: yüksek fiyat = düşük y (SVG y ekseni ters)
        ys = [round(pad + (1 - (p - mn) / span) * (height - 2 * pad), 2) for p in prices]

        # Renk: son - ilk fiyata göre
        if renk_kz is not None:
            renk = "#00e676" if renk_kz >= 0 else "#ff1744"
        else:
            renk = "#00e676" if prices[-1] >= prices[0] else "#ff1744"

        # Polylon noktaları
        pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))

        # Dolgu için alan kapatma (altına in, sola git, kapat)
        alan_pts = (
            f"0,{height} "      # sol alt köşe
            + pts +
            f" {width},{height}" # sağ alt köşe
        )

        svg = (
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
            f"xmlns='http://www.w3.org/2000/svg' style='vertical-align:middle;overflow:visible;'>"
            # Alan dolgusu (şeffaf)
            f"<polygon points='{alan_pts}' fill='{renk}' fill-opacity='0.12'/>"
            # Çizgi
            f"<polyline points='{pts}' fill='none' stroke='{renk}' "
            f"stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/>"
            # Son nokta
            f"<circle cx='{xs[-1]}' cy='{ys[-1]}' r='2' fill='{renk}'/>"
            f"</svg>"
        )
        return svg
    except Exception:
        return "<span style='opacity:0.25;font-size:10px;'>—</span>"


@st.cache_data(ttl=600)
def hesapla_korelasyon(hisse_listesi):
    """Son 30 gün kapanış fiyatları üzerinden korelasyon matrisi hesaplar."""
    kapanis = {}
    for h in hisse_listesi:
        d = fetch_stock_data(h)
        if d and not d['hist'].empty:
            kapanis[h] = d['hist']['Close'].values[-30:]
    if len(kapanis) < 2:
        return None
    min_uzunluk = min(len(v) for v in kapanis.values())
    df_kap = pd.DataFrame({k: v[-min_uzunluk:] for k, v in kapanis.items()})
    return df_kap.corr()

# ==========================================
# GELİŞTİRİLMİŞ TABLO — RSI + MACD + BB sütunu
# ==========================================
def render_kral_table(df_local, goster_indikatör=True):
    # Güvenlik kalkanı
    if df_local is None or not isinstance(df_local, pd.DataFrame) or df_local.empty:
        return "<table class='kral-table'><tbody><tr><td style='opacity:0.5;padding:16px;'>Veri bulunamadı.</td></tr></tbody></table>"

    # Mobil modda sadece 5 kritik sütun göster
    _mobil = st.session_state.get('mobil_mod', False)

    if _mobil:
        baslik = "<tr><th>VARLIK</th><th>7G</th><th>GÜNCEL</th><th>K/Z</th><th>SİNYAL</th></tr>"
        table_html = f"<table class='kral-table'><thead>{baslik}</thead><tbody>"
        for _, r in df_local.iterrows():
            try:
                kz_color = "#00e676" if r.get('K/Z', 0) >= 0 else "#ff1744"
                spark_prices = r.get('Sparkline', [])
                if not isinstance(spark_prices, list):
                    spark_prices = []
                spark_svg = make_sparkline_svg(spark_prices, renk_kz=r.get('K/Z', 0))
                table_html += (
                    f"<tr>"
                    f"<td><b>{r.get('Hisse','?')}</b></td>"
                    f"<td style='padding:6px 8px;'>{spark_svg}</td>"
                    f"<td>{tr_format4(r.get('Güncel',0))} ₺</td>"
                    f"<td style='color:{kz_color};font-weight:bold;'>{tr_format(r.get('K/Z',0))} ₺</td>"
                    f"<td style='font-size:11px;'>{r.get('Sinyal','—')}</td>"
                    f"</tr>"
                )
            except Exception as _te:
                logger.error(f"Mobil tablo satır hatası: {_te}")
        return table_html + "</tbody></table>"

    if goster_indikatör:
        baslik = "<tr><th>VARLIK</th><th>7G</th><th>SİNYAL</th><th>RSI</th><th>MACD-H</th><th>BB%</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr>"
    else:
        baslik = "<tr><th>VARLIK</th><th>7G</th><th>SİNYAL</th><th>ADET</th><th>MALİYET</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr>"

    table_html = f"<table class='kral-table'><thead>{baslik}</thead><tbody>"

    for _, r in df_local.iterrows():
        try:
            kz_color = "#00e676" if r.get('K/Z', 0) >= 0 else "#ff1744"

            # Sparkline SVG
            spark_prices = r.get('Sparkline', [])
            if not isinstance(spark_prices, list):
                spark_prices = []
            spark_svg = make_sparkline_svg(spark_prices, renk_kz=r.get('K/Z', 0))

            if goster_indikatör:
                rsi = float(r.get('RSI', 50))
                if rsi < 35:   rsi_color = "#00e676"
                elif rsi > 65: rsi_color = "#ff1744"
                else:          rsi_color = "#ffc107"

                macd_h      = float(r.get('MACD_H', 0))
                macd_color  = "#00e676" if macd_h > 0 else "#ff1744"
                macd_sembol = f"+{tr_format(macd_h)}" if macd_h > 0 else tr_format(macd_h)

                bb_pct   = max(0, min(100, float(r.get('BB_PCT', 50))))
                bb_color = "#00e676" if bb_pct < 30 else ("#ff1744" if bb_pct > 70 else "#ffc107")
                bb_bg    = t_sec['box']

                extra = (
                    f"<td style='color:{rsi_color};font-weight:bold;'>{rsi:.1f}</td>"
                    f"<td style='color:{macd_color};font-weight:bold;'>{macd_sembol}</td>"
                    f"<td>"
                    f"<div style='background:{bb_bg};border-radius:4px;width:80px;height:8px;display:inline-block;vertical-align:middle;'>"
                    f"<div style='width:{bb_pct}%;background:{bb_color};height:8px;border-radius:4px;'></div>"
                    f"</div> <span style='font-size:11px;color:{bb_color};'>{bb_pct:.0f}%</span>"
                    f"</td>"
                    f"<td>{r.get('Adet', 0)}</td>"
                )
                table_html += (
                    f"<tr>"
                    f"<td><b>{r.get('Hisse','?')}</b></td>"
                    f"<td style='padding:8px 12px;'>{spark_svg}</td>"
                    f"<td>{r.get('Sinyal','—')}</td>"
                    f"{extra}"
                    f"<td>{tr_format4(r.get('Maliyet',0))} ₺</td>"
                    f"<td>{tr_format4(r.get('Güncel',0))} ₺</td>"
                    f"<td style='color:{kz_color};font-weight:bold;'>{tr_format(r.get('K/Z',0))} ₺</td>"
                    f"<td><b>{tr_format(r.get('Değer',0))} ₺</b></td>"
                    f"</tr>"
                )
            else:
                table_html += (
                    f"<tr>"
                    f"<td><b>{r.get('Hisse','?')}</b></td>"
                    f"<td style='padding:8px 12px;'>{spark_svg}</td>"
                    f"<td>{r.get('Sinyal','—')}</td>"
                    f"<td>{r.get('Adet',0)}</td>"
                    f"<td>{tr_format4(r.get('Maliyet',0))} ₺</td>"
                    f"<td>{tr_format4(r.get('Güncel',0))} ₺</td>"
                    f"<td style='color:{kz_color};font-weight:bold;'>{tr_format(r.get('K/Z',0))} ₺</td>"
                    f"<td><b>{tr_format(r.get('Değer',0))} ₺</b></td>"
                    f"</tr>"
                )
        except Exception as _te:
            logger.error(f"Tablo satır hatası ({r.get('Hisse','?')}): {_te}")
            table_html += f"<tr><td colspan='11' style='opacity:0.4;font-size:11px;'>⚠️ {r.get('Hisse','?')} — gösterim hatası</td></tr>"

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
            _total  = df_chart['Değer'].sum()
            _labels = df_chart['Hisse'].tolist()
            _values = df_chart['Değer'].tolist()
            _palette = [
                "#00D4FF","#FF6B6B","#FFD93D","#6BCB77","#A78BFA",
                "#F97316","#38BDF8","#F472B6","#34D399","#FBBF24",
                "#E879F9","#60A5FA","#FB923C","#4ADE80","#C084FC",
            ]
            _colors = (_palette * (len(_labels) // len(_palette) + 1))[:len(_labels)]

            fig = go.Figure(data=[go.Pie(
                labels=_labels,
                values=_values,
                hole=0.58,
                textinfo='label+percent',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>Değer: %{value:,.2f} ₺<br>Oran: %{percent}<extra></extra>',
                marker=dict(colors=_colors, line=dict(color=t_sec['bg'], width=2)),
                pull=[0.02] * len(_labels),
            )])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=t_sec['text'], size=12, family=secili_font),
                showlegend=False,
                margin=dict(t=60, b=20, l=60, r=60),
                height=400,
                title=dict(
                    text="📊 Hisse Dağılımı",
                    font=dict(size=15, color=t_sec['accent']),
                    x=0.5, xanchor='center', y=0.97,
                ),
                annotations=[dict(
                    text=f"<b>{tr_format(_total)}</b><br>₺ TOPLAM",
                    x=0.5, y=0.5,
                    font=dict(size=14, color=t_sec['accent']),
                    showarrow=False, align='center',
                    xref='paper', yref='paper',
                )]
            )
            st.plotly_chart(fig, use_container_width=True)

            # Yatay mini kart grid — her hisse için renkli kutu
            _pct_list = [v / _total * 100 for v in _values]
            _kartlar = "".join(
                f"<div style='"
                f"display:inline-flex;flex-direction:column;align-items:flex-start;"
                f"background:{t_sec['box']};border:1px solid {_colors[i]}55;"
                f"border-left:4px solid {_colors[i]};"
                f"border-radius:8px;padding:8px 12px;margin:4px;"
                f"min-width:110px;max-width:160px;vertical-align:top;'>"
                f"<span style='display:flex;align-items:center;gap:6px;margin-bottom:4px;'>"
                f"  <span style='width:8px;height:8px;border-radius:50%;"
                f"  background:{_colors[i]};flex-shrink:0;'></span>"
                f"  <b style='font-size:12px;color:{t_sec['text']};'>{_labels[i]}</b>"
                f"</span>"
                f"<span style='font-size:13px;font-weight:700;color:{_colors[i]};'>"
                f"%{_pct_list[i]:.1f}</span>"
                f"<span style='font-size:10px;opacity:0.6;margin-top:2px;'>"
                f"{tr_format(_values[i])} ₺</span>"
                f"</div>"
                for i in range(len(_labels))
            )
            st.markdown(
                f"<div style='display:flex;flex-wrap:wrap;gap:0;margin-top:8px;'>"
                f"{_kartlar}</div>",
                unsafe_allow_html=True
            )
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
            _total_f  = df_chart_f['Değer'].sum()
            _labels_f = df_chart_f['Hisse'].tolist()
            _values_f = df_chart_f['Değer'].tolist()
            _palette_f = [
                "#A78BFA","#34D399","#F97316","#38BDF8","#F472B6",
                "#FBBF24","#60A5FA","#6BCB77","#E879F9","#00D4FF",
                "#FB923C","#4ADE80","#C084FC","#FFD93D","#FF6B6B",
            ]
            _colors_f = (_palette_f * (len(_labels_f) // len(_palette_f) + 1))[:len(_labels_f)]

            fig_f = go.Figure(data=[go.Pie(
                labels=_labels_f,
                values=_values_f,
                hole=0.58,
                textinfo='label+percent',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>Değer: %{value:,.2f} ₺<br>Oran: %{percent}<extra></extra>',
                marker=dict(colors=_colors_f, line=dict(color=t_sec['bg'], width=2)),
                pull=[0.02] * len(_labels_f),
            )])
            fig_f.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=t_sec['text'], size=12, family=secili_font),
                showlegend=False,
                margin=dict(t=60, b=20, l=60, r=60),
                height=400,
                title=dict(
                    text="📊 Fon Dağılımı",
                    font=dict(size=15, color=t_sec['accent']),
                    x=0.5, xanchor='center', y=0.97,
                ),
                annotations=[dict(
                    text=f"<b>{tr_format(_total_f)}</b><br>₺ TOPLAM",
                    x=0.5, y=0.5,
                    font=dict(size=14, color=t_sec['accent']),
                    showarrow=False, align='center',
                    xref='paper', yref='paper',
                )]
            )
            st.plotly_chart(fig_f, use_container_width=True)

            # Yatay mini kart grid — her fon için renkli kutu
            _pct_f = [v / _total_f * 100 for v in _values_f]
            _kartlar_f = "".join(
                f"<div style='"
                f"display:inline-flex;flex-direction:column;align-items:flex-start;"
                f"background:{t_sec['box']};border:1px solid {_colors_f[i]}55;"
                f"border-left:4px solid {_colors_f[i]};"
                f"border-radius:8px;padding:8px 12px;margin:4px;"
                f"min-width:110px;max-width:160px;vertical-align:top;'>"
                f"<span style='display:flex;align-items:center;gap:6px;margin-bottom:4px;'>"
                f"  <span style='width:8px;height:8px;border-radius:50%;"
                f"  background:{_colors_f[i]};flex-shrink:0;'></span>"
                f"  <b style='font-size:12px;color:{t_sec['text']};'>{_labels_f[i]}</b>"
                f"</span>"
                f"<span style='font-size:13px;font-weight:700;color:{_colors_f[i]};'>"
                f"%{_pct_f[i]:.1f}</span>"
                f"<span style='font-size:10px;opacity:0.6;margin-top:2px;'>"
                f"{tr_format(_values_f[i])} ₺</span>"
                f"</div>"
                for i in range(len(_labels_f))
            )
            st.markdown(
                f"<div style='display:flex;flex-wrap:wrap;gap:0;margin-top:8px;'>"
                f"{_kartlar_f}</div>",
                unsafe_allow_html=True
            )
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
                f"<td style='color:#ffc107;'>{tr_format4(brut)} ₺</td>"
                f"<td style='color:#00e676;'>{tr_format4(r['Temettu'])} ₺</td>"
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
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>🚀 Halka Arz Takip</h4>", unsafe_allow_html=True)

    with st.form("ipo_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        ipo_isim  = ic1.text_input("Şirket Kodu", placeholder="BINHO")
        ipo_fiyat = ic2.number_input("Halka Arz Fiyatı (₺)", min_value=0.0, format="%.4f")
        ipo_adet  = ic3.number_input("Lot Sayısı", min_value=0, step=1)
        if st.form_submit_button("➕ Listeye Ekle", use_container_width=True):
            if ipo_isim:
                st.session_state.ipo_liste.append({
                    "Isim": ipo_isim.upper().strip(),
                    "Fiyat": float(ipo_fiyat),
                    "Adet": int(ipo_adet)
                })
                save_json(IPO_DOSYASI, st.session_state.ipo_liste)
                st.rerun()

    if st.session_state.ipo_liste:
        for idx, ipo in enumerate(st.session_state.ipo_liste):
            maliyet = ipo['Adet'] * ipo['Fiyat']
            baslik  = f"📈 {ipo['Isim']}  |  {tr_format4(ipo['Fiyat'])} ₺  |  {ipo['Adet']} Lot  |  {tr_format(maliyet)} ₺"
            with st.expander(baslik):
                ri1, ri2, ri3, ri4 = st.columns([2, 2, 2, 1])
                ri1.markdown(
                    f"<div style='padding:8px 0;'>"
                    f"<div style='font-size:10px;opacity:0.55;'>HALKA ARZ FİYATI</div>"
                    f"<div style='font-weight:700;font-size:14px;color:{acc};'>{tr_format4(ipo['Fiyat'])} ₺</div>"
                    f"</div>", unsafe_allow_html=True
                )
                ri2.markdown(
                    f"<div style='padding:8px 0;'>"
                    f"<div style='font-size:10px;opacity:0.55;'>LOT SAYISI</div>"
                    f"<div style='font-weight:700;font-size:14px;'>{ipo['Adet']} Lot</div>"
                    f"</div>", unsafe_allow_html=True
                )
                ri3.markdown(
                    f"<div style='padding:8px 0;'>"
                    f"<div style='font-size:10px;opacity:0.55;'>TOPLAM MALİYET</div>"
                    f"<div style='font-weight:700;font-size:14px;'>{tr_format(maliyet)} ₺</div>"
                    f"</div>", unsafe_allow_html=True
                )
                ri4.markdown("<div style='padding-top:18px;'></div>", unsafe_allow_html=True)
                if ri4.button("❌ Sil", key=f"del_ipo_{idx}", use_container_width=True):
                    st.session_state.ipo_liste.pop(idx)
                    save_json(IPO_DOSYASI, st.session_state.ipo_liste)
                    st.rerun()

                st.divider()

                # Tavan simülasyon tablosu
                tavan_html = (
                    "<table class='kral-table' style='text-align:center;'>"
                    "<thead><tr>"
                    "<th style='text-align:center;'>GÜN</th>"
                    "<th style='text-align:center;'>FİYAT</th>"
                    "<th style='text-align:center;'>TOPLAM KAR</th>"
                    "<th style='text-align:center;'>GETIRI %</th>"
                    "</tr></thead><tbody>"
                )
                p = ipo['Fiyat']
                for g in range(1, 11):
                    p  *= 1.10
                    kar = (p * ipo['Adet']) - maliyet
                    getiri_pct = (kar / maliyet * 100) if maliyet > 0 else 0
                    tavan_html += (
                        f"<tr><td><b>{g}. Tavan</b></td>"
                        f"<td>{tr_format4(p)} ₺</td>"
                        f"<td style='color:#00e676;font-weight:bold;'>+{tr_format(kar)} ₺</td>"
                        f"<td style='color:#00e676;'>+{getiri_pct:.1f}%</td></tr>"
                    )
                tavan_html += "</tbody></table>"
                st.markdown(tavan_html, unsafe_allow_html=True)

                # Portföye Aktar
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                pa1, pa2, pa3 = st.columns([2, 2, 1])
                aktar_hisse = pa1.text_input(
                    "BIST Kodu (.IS ekli)", value=ipo['Isim'] + ".IS",
                    key=f"aktar_kod_{idx}", placeholder="Örn: BINHO.IS"
                )
                aktar_maliyet = pa2.number_input(
                    "Alış Maliyeti (₺)", value=float(ipo['Fiyat']),
                    format="%.4f", key=f"aktar_maliyet_{idx}"
                )
                pa3.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                if pa3.button("📥 Portföye", key=f"aktar_btn_{idx}", use_container_width=True):
                    if aktar_hisse:
                        st.session_state.portfoy.append({
                            "Piyasa": "Türk Borsası",
                            "Hisse":  aktar_hisse.upper(),
                            "Adet":   int(ipo['Adet']),
                            "Maliyet": float(aktar_maliyet)
                        })
                        st.session_state.portfoy = sorted(st.session_state.portfoy, key=lambda x: x['Hisse'])
                        save_json(portfoy_dosyasi(st.session_state.aktif_portfoy), st.session_state.portfoy)
                        st.success(f"✅ {aktar_hisse.upper()} portföye eklendi!")
                        st.rerun()
    else:
        st.info("Henüz halka arz takip listesi boş. Yukarıdan ekleyebilirsin.")

with tab_analiz:
    acc = t_sec['accent']
    txt = t_sec['text']
    box = t_sec['box']
    bg  = t_sec['bg']

    # ---------- A) HİSSE FİYAT GRAFİĞİ + ÇİZİM ARAÇLARI ----------
    st.markdown(f"<h4 style='color:{acc};'>🕯️ Hisse Fiyat Grafiği & Çizim Araçları</h4>", unsafe_allow_html=True)
    portfoy_hisseler_a = sorted(set(x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası'))
    if portfoy_hisseler_a:
        _ca1, _ca2, _ca3, _ca4 = st.columns([3, 1, 2, 2])
        cs_hisse = _ca1.selectbox("Hisse Seç", portfoy_hisseler_a, key="cs_hisse")
        cs_tip   = _ca2.selectbox("Grafik Tipi", ["Candlestick", "Çizgi"], key="cs_tip")

        # Gösterge seçimi
        _gosterge_secim = _ca3.multiselect(
            "Göstergeler",
            ["MA20", "MA50", "Bollinger Bands", "Destek/Direnç", "Fibonacci", "Trendline"],
            default=["MA20", "Destek/Direnç"],
            key="cs_gostergeler"
        )

        # Zaman dilimi seçimi
        _zaman_secenekleri = {
            "1 Saat":   ("1h",  "7d"),
            "4 Saat":   ("1h",  "30d"),
            "1 Gün":    ("1d",  "60d"),
            "1 Hafta":  ("1wk", "365d"),
            "1 Ay":     ("1mo", "1825d"),
        }
        _zaman_sec = _ca4.selectbox(
            "Zaman Dilimi",
            list(_zaman_secenekleri.keys()),
            index=2,   # Varsayılan: 1 Gün
            key="cs_zaman"
        )
        _interval, _period = _zaman_secenekleri[_zaman_sec]

        # Seçilen zaman dilimine göre veri çek
        @st.cache_data(ttl=180)
        def _fetch_grafik(symbol, interval, period):
            try:
                tk = yf.Ticker(symbol)
                hist = tk.history(period=period, interval=interval)
                if hist.empty:
                    return None
                return hist
            except Exception as e:
                logger.warning(f"Grafik veri hatası ({symbol} {interval}/{period}): {e}")
                return None

        _grafik_hist = _fetch_grafik(cs_hisse, _interval, _period)
        # 1d için mevcut fetch_stock_data kullan (MACD hesabı için 60 gün lazım)
        if _interval == "1d":
            cs_data = fetch_stock_data(cs_hisse)
            _grafik_hist = cs_data['hist'].copy() if cs_data else _grafik_hist

        if _grafik_hist is not None and not _grafik_hist.empty:
            hist = _grafik_hist.copy()
            hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index

            if cs_tip == "Candlestick":
                cs_fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name=cs_hisse,
                )])
                cs_fig.update_traces(
                    selector=dict(type='candlestick'),
                    increasing=dict(line=dict(color='#00e676')),
                    decreasing=dict(line=dict(color='#ff1744')),
                )
            else:
                cs_fig = go.Figure(data=[go.Scatter(
                    x=hist.index, y=hist['Close'],
                    mode='lines',
                    line=dict(color=acc, width=2),
                    fill='tozeroy',
                    fillcolor=hex_rgba(acc, 0.09),
                    name=cs_hisse,
                )])

            # MA20
            if "MA20" in _gosterge_secim:
                ma20 = hist['Close'].rolling(20).mean()
                cs_fig.add_trace(go.Scatter(
                    x=hist.index, y=ma20, mode='lines',
                    line=dict(color='#ffc107', width=1.2, dash='dot'),
                    name='MA20', opacity=0.85,
                ))

            # MA50
            if "MA50" in _gosterge_secim:
                ma50 = hist['Close'].rolling(50).mean()
                cs_fig.add_trace(go.Scatter(
                    x=hist.index, y=ma50, mode='lines',
                    line=dict(color='#60a5fa', width=1.2, dash='dash'),
                    name='MA50', opacity=0.85,
                ))

            # Trendline (lineer regresyon ile otomatik)
            if "Trendline" in _gosterge_secim and len(hist) >= 5:
                try:
                    _tr_x   = np.arange(len(hist))
                    _tr_y   = hist['Close'].values.astype(float)
                    # Tüm veri üzerinde lineer regresyon
                    _tr_koef = np.polyfit(_tr_x, _tr_y, 1)
                    _tr_line = np.polyval(_tr_koef, _tr_x)
                    _tr_yon  = "yukarı" if _tr_koef[0] > 0 else "aşağı"
                    _tr_renk = '#00e676' if _tr_koef[0] > 0 else '#ff1744'
                    cs_fig.add_trace(go.Scatter(
                        x=hist.index, y=_tr_line,
                        mode='lines', name=f'Trend ({_tr_yon})',
                        line=dict(color=_tr_renk, width=1.5, dash='longdash'),
                        opacity=0.75,
                        hovertemplate='Trend: %{y:.4f}<extra></extra>',
                    ))
                    # Son 1/3 verisi için kısa vadeli trend
                    _tr_son = max(5, len(hist) // 3)
                    _tr_x2  = np.arange(_tr_son)
                    _tr_y2  = hist['Close'].values[-_tr_son:].astype(float)
                    _tr_k2  = np.polyfit(_tr_x2, _tr_y2, 1)
                    _tr_l2  = np.polyval(_tr_k2, _tr_x2)
                    _tr_r2  = '#00bcd4'
                    cs_fig.add_trace(go.Scatter(
                        x=hist.index[-_tr_son:], y=_tr_l2,
                        mode='lines', name='Kısa Vadeli Trend',
                        line=dict(color=_tr_r2, width=1.2, dash='dot'),
                        opacity=0.7,
                        hovertemplate='K.V. Trend: %{y:.4f}<extra></extra>',
                    ))
                except Exception as _tre:
                    logger.warning(f"Trendline hatası: {_tre}")

            # Bollinger Bands
            if "Bollinger Bands" in _gosterge_secim:
                _bb_mid = hist['Close'].rolling(20).mean()
                _bb_std = hist['Close'].rolling(20).std()
                _bb_ust = _bb_mid + 2 * _bb_std
                _bb_alt = _bb_mid - 2 * _bb_std
                cs_fig.add_trace(go.Scatter(
                    x=hist.index, y=_bb_ust, mode='lines',
                    line=dict(color='#a78bfa', width=0.8, dash='dot'),
                    name='BB Üst', opacity=0.7,
                ))
                cs_fig.add_trace(go.Scatter(
                    x=hist.index, y=_bb_alt, mode='lines',
                    line=dict(color='#a78bfa', width=0.8, dash='dot'),
                    fill='tonexty', fillcolor=hex_rgba('#a78bfa', 0.05),
                    name='BB Alt', opacity=0.7,
                ))

            # Otomatik Destek/Direnç (son 60 günün yüksek/düşük seviyeleri)
            if "Destek/Direnç" in _gosterge_secim:
                _son_yuksek = float(hist['High'].max())
                _son_dusuk  = float(hist['Low'].min())
                _son_kapanis = float(hist['Close'].iloc[-1])
                # Pivot hesapla
                _pivot = (_son_yuksek + _son_dusuk + _son_kapanis) / 3
                _r1 = 2 * _pivot - _son_dusuk
                _s1 = 2 * _pivot - _son_yuksek
                for _lvl, _lbl, _lc in [
                    (_son_yuksek, f"60G Yüksek: {tr_format4(_son_yuksek)}", '#ff1744'),
                    (_son_dusuk,  f"60G Düşük: {tr_format4(_son_dusuk)}",  '#00e676'),
                    (_pivot,       f"Pivot: {tr_format4(_pivot)}",           '#ffc107'),
                    (_r1,          f"R1: {tr_format4(_r1)}",                 '#ff7043'),
                    (_s1,          f"S1: {tr_format4(_s1)}",                 '#66bb6a'),
                ]:
                    cs_fig.add_hline(
                        y=_lvl, line_dash="dash", line_color=_lc,
                        line_width=0.8, opacity=0.7,
                        annotation_text=_lbl,
                        annotation_position="right",
                        annotation_font_size=9,
                        annotation_font_color=_lc,
                    )

            # Fibonacci Retracement
            if "Fibonacci" in _gosterge_secim:
                _fib_yuk = float(hist['High'].max())
                _fib_dus = float(hist['Low'].min())
                _fib_aralik = _fib_yuk - _fib_dus
                for _oran, _fib_renk in [(0.236,'#ffd700'),(0.382,'#ffaa00'),
                                          (0.5,'#ff8800'),(0.618,'#ff5500'),(0.786,'#ff2200')]:
                    _fib_lvl = _fib_yuk - _oran * _fib_aralik
                    cs_fig.add_hline(
                        y=_fib_lvl, line_dash="dot", line_color=_fib_renk,
                        line_width=0.7, opacity=0.6,
                        annotation_text=f"Fib {_oran:.3f}: {tr_format4(_fib_lvl)}",
                        annotation_position="right",
                        annotation_font_size=9,
                        annotation_font_color=_fib_renk,
                    )

            cs_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=txt, size=11, family=secili_font),
                height=460,
                margin=dict(t=40, b=40, l=40, r=120),
                xaxis=dict(
                    showgrid=True, gridcolor=hex_rgba(acc, 0.08),
                    rangeslider=dict(visible=False),
                    color=txt,
                ),
                yaxis=dict(
                    showgrid=True, gridcolor=hex_rgba(acc, 0.08),
                    color=txt, side='right',
                ),
                legend=dict(
                    orientation='h', x=0, y=1.08,
                    font=dict(size=10, color=txt),
                    bgcolor='rgba(0,0,0,0)',
                ),
                title=dict(
                    text=f"{cs_hisse} — {_zaman_sec}",
                    font=dict(size=13, color=acc),
                    x=0.5, xanchor='center',
                ),
            )
            st.plotly_chart(cs_fig, use_container_width=True)
            st.caption(f"📊 {cs_hisse} · {_zaman_sec} · {len(hist)} mum · yfinance")
        else:
            st.warning(f"{cs_hisse} için veri alınamadı. yfinance bazı intraday verilerini (1h/4h) desteklemeyebilir.")
    else:
        st.info("Türk Borsası'nda hisse bulunamadı.")

    st.divider()

    # ---------- B) PORTFÖY PERFORMANS GRAFİĞİ ----------
    st.markdown(f"<h4 style='color:{acc};'>📉 Portföy Performans Geçmişi</h4>", unsafe_allow_html=True)
    perf_kayitlar = st.session_state.get('performans', [])
    if len(perf_kayitlar) >= 2:
        perf_df = pd.DataFrame(perf_kayitlar)
        perf_df['tarih'] = pd.to_datetime(perf_df['tarih'])
        perf_df = perf_df.sort_values('tarih')

        pf_fig = go.Figure()
        pf_fig.add_trace(go.Scatter(
            x=perf_df['tarih'], y=perf_df['deger'],
            mode='lines+markers',
            name='Portföy Değeri',
            line=dict(color=acc, width=2.5),
            marker=dict(size=5, color=acc),
            fill='tozeroy', fillcolor=hex_rgba(acc, 0.08),
            hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Değer: %{y:,.0f} ₺<extra></extra>',
        ))
        pf_fig.add_trace(go.Bar(
            x=perf_df['tarih'], y=perf_df['kz'],
            name='Günlük K/Z',
            marker_color=[('#00e676' if v >= 0 else '#ff1744') for v in perf_df['kz']],
            opacity=0.6,
            yaxis='y2',
            hovertemplate='<b>%{x|%d.%m.%Y}</b><br>K/Z: %{y:,.0f} ₺<extra></extra>',
        ))
        pf_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=txt, size=11, family=secili_font),
            height=360,
            margin=dict(t=50, b=40, l=40, r=60),
            xaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt),
            yaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt,
                       title=dict(text='Değer (₺)', font=dict(size=11))),
            yaxis2=dict(overlaying='y', side='right', showgrid=False, color=txt,
                        title=dict(text='K/Z (₺)', font=dict(size=11))),
            legend=dict(orientation='h', x=0, y=1.08,
                        font=dict(size=10, color=txt), bgcolor='rgba(0,0,0,0)'),
            title=dict(text="Günlük Portföy Değeri & K/Z",
                       font=dict(size=13, color=acc), x=0.5, xanchor='center'),
            barmode='overlay',
        )
        st.plotly_chart(pf_fig, use_container_width=True)

        # Özet istatistikler
        _ilk  = perf_df['deger'].iloc[0]
        _son  = perf_df['deger'].iloc[-1]
        _max  = perf_df['deger'].max()
        _min  = perf_df['deger'].min()
        _perf = ((_son - _ilk) / _ilk * 100) if _ilk > 0 else 0
        _pc   = "#00e676" if _perf >= 0 else "#ff1744"
        ps1, ps2, ps3, ps4 = st.columns(4)
        ps1.metric("Dönem Başı",        f"{tr_format(_ilk)} ₺")
        ps2.metric("Bugün",             f"{tr_format(_son)} ₺")
        ps3.metric("Dönem Getirisi",    f"%{_perf:+.2f}")
        ps4.metric("En Yüksek Değer",   f"{tr_format(_max)} ₺")
    else:
        st.info("Performans geçmişi için en az 2 günlük veri gerekli. Uygulama her açıldığında o günün değerini kaydeder.")

    st.divider()

    # ---------- C) KORELASYON MATRİSİ ----------
    st.markdown(f"<h4 style='color:{acc};'>🔗 Hisse Korelasyon Matrisi</h4>", unsafe_allow_html=True)
    portfoy_bist = [x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası']
    if len(portfoy_bist) >= 2:
        kor_df = hesapla_korelasyon(tuple(portfoy_bist))
        if kor_df is not None and not kor_df.empty:
            n = len(kor_df)
            kor_z = kor_df.values
            labels = kor_df.columns.tolist()

            # Renk skalası: kırmızı(-1) → beyaz(0) → yeşil(+1)
            kor_fig = go.Figure(data=go.Heatmap(
                z=kor_z,
                x=labels,
                y=labels,
                colorscale=[
                    [0.0,  '#ff1744'],
                    [0.5,  box],
                    [1.0,  '#00e676'],
                ],
                zmin=-1, zmax=1,
                text=[[f"{kor_z[i][j]:.2f}" for j in range(n)] for i in range(n)],
                texttemplate="%{text}",
                textfont=dict(size=11, color=txt),
                hovertemplate='<b>%{y} × %{x}</b><br>Korelasyon: %{z:.3f}<extra></extra>',
                showscale=True,
                colorbar=dict(
                    thickness=12, len=0.8,
                    tickfont=dict(size=10, color=txt),
                    title=dict(text='r', font=dict(color=txt)),
                ),
            ))
            kor_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=txt, size=11, family=secili_font),
                height=max(300, n * 44 + 80),
                margin=dict(t=50, b=60, l=60, r=80),
                xaxis=dict(color=txt, tickangle=-35),
                yaxis=dict(color=txt),
                title=dict(
                    text="Son 30 Gün Kapanış Korelasyonu",
                    font=dict(size=13, color=acc),
                    x=0.5, xanchor='center',
                ),
            )
            st.plotly_chart(kor_fig, use_container_width=True)
            st.markdown(
                f"<small style='color:{acc}88;'>+1,00 = Tam pozitif korelasyon &nbsp;|&nbsp; "
                f"0,00 = İlişkisiz &nbsp;|&nbsp; -1,00 = Tam negatif korelasyon</small>",
                unsafe_allow_html=True
            )
        else:
            st.warning("Korelasyon hesaplanamadı (yeterli veri yok).")
    else:
        st.info("Korelasyon matrisi için portföyde en az 2 Türk Borsası hissesi gerekli.")

    st.divider()

    # ---------- D) HİSSE KARŞILAŞTIRMA ----------
    st.markdown(f"<h4 style='color:{acc};'>⚔️ Hisse Karşılaştırma</h4>", unsafe_allow_html=True)
    _tum_hisseler = sorted(set(x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası'))
    if len(_tum_hisseler) >= 2:
        _kc1, _kc2 = st.columns(2)
        _kars_a = _kc1.selectbox("1. Hisse", _tum_hisseler, index=0, key="kars_a")
        _kars_b = _kc2.selectbox("2. Hisse", _tum_hisseler, index=min(1, len(_tum_hisseler)-1), key="kars_b")
        if _kars_a != _kars_b:
            _da = fetch_stock_data(_kars_a)
            _db = fetch_stock_data(_kars_b)
            if _da and _db and not _da['hist'].empty and not _db['hist'].empty:
                _ha = _da['hist']['Close'].copy()
                _hb = _db['hist']['Close'].copy()
                _ha.index = _ha.index.tz_localize(None) if _ha.index.tz else _ha.index
                _hb.index = _hb.index.tz_localize(None) if _hb.index.tz else _hb.index
                _min_len = min(len(_ha), len(_hb))
                _na = (_ha.iloc[-_min_len:] / _ha.iloc[-_min_len] * 100)
                _nb = (_hb.iloc[-_min_len:] / _hb.iloc[-_min_len] * 100)
                _kars_fig = go.Figure()
                _kars_fig.add_trace(go.Scatter(
                    x=_na.index, y=_na.values, name=_kars_a,
                    line=dict(color=acc, width=2),
                    hovertemplate=f'<b>{_kars_a}</b><br>%{{y:.1f}}<extra></extra>',
                ))
                _kars_fig.add_trace(go.Scatter(
                    x=_nb.index, y=_nb.values, name=_kars_b,
                    line=dict(color='#ffc107', width=2, dash='dash'),
                    hovertemplate=f'<b>{_kars_b}</b><br>%{{y:.1f}}<extra></extra>',
                ))
                _kars_fig.add_hline(y=100, line_dash='dot', line_color=txt, opacity=0.2)
                _kars_fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=txt, size=11, family=secili_font),
                    height=320, margin=dict(t=40, b=40, l=40, r=20),
                    xaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt,
                               rangeslider=dict(visible=False)),
                    yaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt,
                               title=dict(text='Normalize (Başlangıç=100)', font=dict(size=10))),
                    legend=dict(orientation='h', x=0, y=1.08, font=dict(size=11, color=txt),
                                bgcolor='rgba(0,0,0,0)'),
                    title=dict(text=f"{_kars_a} vs {_kars_b}",
                               font=dict(size=13, color=acc), x=0.5, xanchor='center'),
                )
                st.plotly_chart(_kars_fig, use_container_width=True)
                # Özet
                _ret_a = float(_na.iloc[-1] - 100)
                _ret_b = float(_nb.iloc[-1] - 100)
                _cc1, _cc2 = st.columns(2)
                _cc1.metric(f"{_kars_a} 60G getiri", f"%{_ret_a:+.2f}",
                            delta="↑ Daha iyi" if _ret_a > _ret_b else None)
                _cc2.metric(f"{_kars_b} 60G getiri", f"%{_ret_b:+.2f}",
                            delta="↑ Daha iyi" if _ret_b > _ret_a else None)
            else:
                st.warning("Karşılaştırma için veri alınamadı.")
        else:
            st.info("Farklı iki hisse seç.")
    else:
        st.info("Karşılaştırma için en az 2 hisse gerekli.")

    st.divider()

    # ---------- E) K/Z TRENDİ (30 GÜN) ----------
    st.markdown(f"<h4 style='color:{acc};'>📆 30 Günlük K/Z Trendi</h4>", unsafe_allow_html=True)
    _perf_data = load_json(PERFORMANS_DOSYASI)
    if len(_perf_data) >= 2:
        _pdf = pd.DataFrame(_perf_data[-30:])
        _pdf = _pdf.sort_values('tarih')
        _kz_vals = _pdf['kz'].tolist() if 'kz' in _pdf.columns else []
        if _kz_vals:
            _trend_fig = go.Figure()
            _trend_colors = ['#00e676' if v >= 0 else '#ff1744' for v in _kz_vals]
            _trend_fig.add_trace(go.Bar(
                x=_pdf['tarih'].tolist(), y=_kz_vals,
                marker_color=_trend_colors, name='Günlük K/Z',
                hovertemplate='<b>%{x}</b><br>K/Z: %{y:,.0f} ₺<extra></extra>',
            ))
            if 'deger' in _pdf.columns:
                _trend_fig.add_trace(go.Scatter(
                    x=_pdf['tarih'].tolist(), y=_pdf['deger'].tolist(),
                    name='Portföy Değeri', yaxis='y2',
                    line=dict(color=acc, width=2),
                    hovertemplate='Değer: %{y:,.0f} ₺<extra></extra>',
                ))
            _trend_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=txt, size=11, family=secili_font),
                height=300, margin=dict(t=40, b=50, l=50, r=60),
                xaxis=dict(color=txt, showgrid=True, gridcolor=hex_rgba(acc,0.08),
                           tickangle=-30, tickfont=dict(size=9)),
                yaxis=dict(color=txt, showgrid=True, gridcolor=hex_rgba(acc,0.08),
                           title=dict(text='K/Z (₺)', font=dict(size=10))),
                yaxis2=dict(overlaying='y', side='right', color=acc,
                            title=dict(text='Değer (₺)', font=dict(size=10, color=acc))),
                legend=dict(orientation='h', x=0, y=1.08, font=dict(size=10, color=txt),
                            bgcolor='rgba(0,0,0,0)'),
                barmode='overlay',
            )
            st.plotly_chart(_trend_fig, use_container_width=True)
            _toplam_kz_30 = sum(_kz_vals)
            _kz_color_30 = "#00e676" if _toplam_kz_30 >= 0 else "#ff1744"
            st.markdown(
                f"<div style='text-align:center;font-size:12px;opacity:0.7;'>"
                f"Son 30 gün toplam K/Z: "
                f"<b style='color:{_kz_color_30};'>{tr_format(_toplam_kz_30)} ₺</b></div>",
                unsafe_allow_html=True
            )
        else:
            st.info("Yeterli performans verisi yok.")
    else:
        st.info("K/Z trendi için en az 2 günlük snapshot gerekli. Uygulama her açılışta otomatik kaydeder.")

    st.divider()

    # ---------- F) PORTFÖY RİSK SKORU ----------
    st.markdown(f"<h4 style='color:{acc};'>🎯 Portföy Risk Skoru</h4>", unsafe_allow_html=True)
    _risk_bist = [x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası']
    if _risk_bist:
        _risk_rsi_list  = [x.get('RSI', 50)    for x in full_data if x['Piyasa'] == 'Türk Borsası']
        _risk_bb_list   = [x.get('BB_PCT', 50)  for x in full_data if x['Piyasa'] == 'Türk Borsası']
        _risk_macd_list = [x.get('MACD_H', 0)   for x in full_data if x['Piyasa'] == 'Türk Borsası']

        # Beta (var mı?)
        _beta_val = None
        try:
            _bist_n, _port_n = fetch_bist100_karsilastirma(tuple(_risk_bist))
            if _bist_n is not None and _port_n is not None and len(_bist_n) > 10:
                _br = np.array(_bist_n.pct_change().dropna())
                _pr = np.array(_port_n.pct_change().dropna())
                _ml = min(len(_br), len(_pr))
                _cov = np.cov(_pr[-_ml:], _br[-_ml:])
                if _cov[1,1] != 0:
                    _beta_val = round(_cov[0,1] / _cov[1,1], 2)
        except Exception:
            pass

        # Korelasyon yoğunluğu
        _kor_skoru = 0
        if len(_risk_bist) >= 2:
            try:
                _km = hesapla_korelasyon(tuple(_risk_bist))
                if _km is not None:
                    _kor_skoru = float(_km.values[np.triu_indices(len(_km), k=1)].mean())
            except Exception:
                pass

        # RSI aşırı alım skoru
        _rsi_asiri = sum(1 for r in _risk_rsi_list if r > 70) / len(_risk_rsi_list)

        # Bileşik risk skoru (0–10)
        _risk_beta   = min(10, abs(_beta_val or 1.0) * 5)
        _risk_kor    = min(10, abs(_kor_skoru) * 10)
        _risk_rsi    = _rsi_asiri * 10
        _risk_puan   = round((_risk_beta * 0.4 + _risk_kor * 0.3 + _risk_rsi * 0.3), 1)

        _risk_renk   = '#00e676' if _risk_puan < 4 else ('#ffc107' if _risk_puan < 7 else '#ff1744')
        _risk_etiket = 'DÜŞÜK RİSK' if _risk_puan < 4 else ('ORTA RİSK' if _risk_puan < 7 else 'YÜKSEK RİSK')

        _rp1, _rp2, _rp3, _rp4 = st.columns(4)
        _rp1.metric("Risk Skoru", f"{_risk_puan}/10")
        _rp2.metric("Beta", f"β {_beta_val}" if _beta_val else "—")
        _rp3.metric("Ort. Korelasyon", f"{_kor_skoru:.2f}" if _kor_skoru else "—")
        _rp4.metric("Aşırı Alım", f"%{_rsi_asiri*100:.0f}")

        # Görsel ölçek
        _bar_w = int(_risk_puan / 10 * 100)
        st.markdown(
            f"<div style='margin-top:8px;'>"
            f"<div style='background:{t_sec['box']};border-radius:8px;height:22px;"
            f"border:1px solid {_risk_renk}44;overflow:hidden;'>"
            f"  <div style='width:{_bar_w}%;background:{_risk_renk};height:100%;"
            f"  display:flex;align-items:center;justify-content:flex-end;padding-right:8px;"
            f"  font-size:11px;font-weight:700;color:{t_sec['bg']};transition:width 0.3s;'>"
            f"  {_risk_etiket}</div></div>"
            f"<div style='font-size:9px;opacity:0.4;margin-top:4px;'>"
            f"Beta %40 · Korelasyon %30 · RSI aşırı alım %30</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Risk skoru için portföyde Türk Borsası hissesi gerekli.")

    st.divider()

    # ---------- G) DÖVİZ KORUMAL GETIRI ----------
    st.markdown(f"<h4 style='color:{acc};'>💵 Döviz Korumalı (USD Bazlı) Getiri</h4>",
                unsafe_allow_html=True)
    _usd_data = fetch_stock_data("USDTRY=X")
    _df_dov = pd.DataFrame([x for x in full_data if x['Piyasa'] == 'Türk Borsası' and x['Maliyet'] > 0])
    if _usd_data and not _df_dov.empty:
        try:
            _usd_guncel = float(_usd_data['hist']['Close'].iloc[-1])
            _usd_dun    = float(_usd_data['hist']['Close'].iloc[-30]) if len(_usd_data['hist']) >= 30 else _usd_guncel
            _usd_alim_tahmini = _usd_dun   # alım tarihi bilinmediği için 30 gün önceki kur

            _dov_tbl = (
                "<table class='kral-table'><thead><tr>"
                "<th>HİSSE</th><th>TL K/Z%</th><th>USD K/Z%</th>"
                "<th>KUR ETKİSİ</th><th>GERÇEK KAZANÇ</th>"
                "</tr></thead><tbody>"
            )
            for _, _r in _df_dov.iterrows():
                try:
                    _tl_kz_pct = (_r['Güncel'] - _r['Maliyet']) / _r['Maliyet'] * 100
                    _usd_maliyet = _r['Maliyet'] / _usd_alim_tahmini
                    _usd_guncel_hisse = _r['Güncel'] / _usd_guncel
                    _usd_kz_pct = (_usd_guncel_hisse - _usd_maliyet) / _usd_maliyet * 100
                    _kur_etkisi = _tl_kz_pct - _usd_kz_pct
                    _tl_c  = '#00e676' if _tl_kz_pct  >= 0 else '#ff1744'
                    _usd_c = '#00e676' if _usd_kz_pct >= 0 else '#ff1744'
                    _kur_c = '#ff7043' if _kur_etkisi  > 0 else '#00e676'
                    _dov_tbl += (
                        f"<tr><td><b>{_r['Hisse']}</b></td>"
                        f"<td style='color:{_tl_c};'>%{_tl_kz_pct:+.2f}</td>"
                        f"<td style='color:{_usd_c};font-weight:700;'>%{_usd_kz_pct:+.2f}</td>"
                        f"<td style='color:{_kur_c};font-size:11px;'>"
                        f"{'Kur eritti' if _kur_etkisi>2 else ('Kur katkı' if _kur_etkisi<-2 else 'Nötr')}"
                        f"</td>"
                        f"<td style='color:{'#00e676' if _usd_kz_pct>=0 else '#ff1744'};font-weight:700;'>"
                        f"{'✅ Kazanç' if _usd_kz_pct>=0 else '❌ Kayıp'}</td>"
                        f"</tr>"
                    )
                except Exception:
                    continue
            _dov_tbl += "</tbody></table>"
            st.markdown(_dov_tbl, unsafe_allow_html=True)
            st.caption(f"USD/TRY güncel: {tr_format4(_usd_guncel)} · Alım kuru tahmini: {tr_format4(_usd_alim_tahmini)} (30 gün öncesi)")
        except Exception as _de:
            st.warning(f"Döviz hesabı hatası: {_de}")
    else:
        st.info("Döviz getirisi için USD/TRY verisi ve portföyde hisse gerekli.")

    st.divider()

    # ---------- H) BACKTEST ----------
    st.markdown(f"<h4 style='color:{acc};'>🔁 Sinyal Backtest (RSI + MACD)</h4>",
                unsafe_allow_html=True)
    st.markdown(
        f"<small style='color:{acc}88;'>Mevcut sinyal motoru 60 günlük geçmişte kaç kez doğru çalıştı?</small>",
        unsafe_allow_html=True
    )
    _bt_hisseler = sorted(set(x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası'))
    if _bt_hisseler:
        _bt1, _bt2, _bt3 = st.columns([2, 1, 1])
        _bt_hisse   = _bt1.selectbox("Hisse", _bt_hisseler, key="bt_hisse")
        _bt_al_esik = _bt2.slider("AL ≤ RSI", 20, 50, 40, key="bt_al")
        _bt_sat_esik= _bt3.slider("SAT ≥ RSI", 55, 80, 65, key="bt_sat")

        @st.cache_data(ttl=600)
        def _backtest(symbol, al_esik, sat_esik):
            _d = fetch_stock_data(symbol)
            if not _d or _d['hist'].empty or len(_d['hist']) < 26:
                return []
            _c = _d['hist']['Close'].copy()
            _delta = _c.diff()
            _gain  = _delta.where(_delta > 0, 0).rolling(14).mean()
            _loss  = (-_delta.where(_delta < 0, 0)).rolling(14).mean()
            _rsi   = 100 - (100 / (1 + _gain / _loss.replace(0, 1e-9)))
            _poz, _islemler = 0.0, []
            for i in range(1, len(_c)):
                _r  = float(_rsi.iloc[i])
                _fz = float(_c.iloc[i])
                _t  = str(_c.index[i])[:10]
                if _r <= al_esik and _poz == 0:
                    _poz = _fz
                    _islemler.append({'tarih':_t,'tip':'AL','fiyat':_fz,'kz':None})
                elif _r >= sat_esik and _poz > 0:
                    _kz = (_fz - _poz) / _poz * 100
                    _islemler.append({'tarih':_t,'tip':'SAT','fiyat':_fz,'kz':round(_kz,2)})
                    _poz = 0.0
            return _islemler

        with st.spinner("Backtest hesaplanıyor..."):
            _bt_islemler = _backtest(_bt_hisse, _bt_al_esik, _bt_sat_esik)

        if _bt_islemler:
            _satislar = [x for x in _bt_islemler if x['tip'] == 'SAT']
            _karlilar = [x for x in _satislar if (x['kz'] or 0) > 0]
            _ort_kz   = sum(x['kz'] for x in _satislar) / len(_satislar) if _satislar else 0
            _basari   = len(_karlilar) / len(_satislar) * 100 if _satislar else 0

            _bm1, _bm2, _bm3, _bm4 = st.columns(4)
            _bm1.metric("İşlem Sayısı",   len(_satislar))
            _bm2.metric("Başarı Oranı",   f"%{_basari:.0f}")
            _bm3.metric("Ort. K/Z",       f"%{_ort_kz:+.2f}")
            _bm4.metric("Kümülatif K/Z",  f"%{sum(x['kz'] for x in _satislar):+.2f}")

            _bt_tbl = (
                "<table class='kral-table'><thead><tr>"
                "<th>TARİH</th><th>İŞLEM</th><th>FİYAT</th><th>K/Z %</th>"
                "</tr></thead><tbody>"
            )
            for _ix in _bt_islemler:
                _tc  = '#00e676' if _ix['tip'] == 'AL' else '#ff1744'
                _kzs = f"%{_ix['kz']:+.2f}" if _ix['kz'] is not None else '—'
                _kzc = '#00e676' if (_ix['kz'] or 0) > 0 else ('#ff1744' if _ix['kz'] is not None else txt)
                _bt_tbl += (
                    f"<tr><td style='font-size:11px;'>{_ix['tarih']}</td>"
                    f"<td style='color:{_tc};font-weight:700;'>{_ix['tip']}</td>"
                    f"<td>{tr_format4(_ix['fiyat'])} ₺</td>"
                    f"<td style='color:{_kzc};font-weight:bold;'>{_kzs}</td></tr>"
                )
            _bt_tbl += "</tbody></table>"
            st.markdown(_bt_tbl, unsafe_allow_html=True)
            st.caption("⚠️ Geçmiş performans geleceği garantilemez. Sadece bilgi amaçlıdır.")
        else:
            st.info("Seçilen parametrelerle sinyal oluşmadı veya yeterli veri yok.")

    st.divider()

    # ---------- I) YATIRIM SİMÜLATÖRÜ ----------
    st.markdown(f"<h4 style='color:{acc};'>💰 Yatırım Simülatörü</h4>", unsafe_allow_html=True)
    st.markdown(
        f"<small style='color:{acc}88;'>Düzenli yatırım + bileşik getiri hesabı</small>",
        unsafe_allow_html=True
    )
    _ys1, _ys2, _ys3 = st.columns(3)
    _ys_baslangic  = _ys1.number_input("Başlangıç (₺)", value=10000.0, min_value=0.0,
                                         step=1000.0, format="%.0f", key="ys_baslangic")
    _ys_aylik      = _ys2.number_input("Aylık Katkı (₺)", value=2000.0, min_value=0.0,
                                         step=500.0, format="%.0f", key="ys_aylik")
    _ys4, _ys5     = st.columns(2)
    _ys_yil        = _ys4.slider("Yıl", 1, 30, 10, key="ys_yil")
    _ys_getiri     = _ys5.slider("Yıllık Getiri (%)", 5, 50, 20, key="ys_getiri")

    # Hesap
    _ys_aylik_faiz = (_ys_getiri / 100) / 12
    _ys_ay_sayisi  = _ys_yil * 12
    _ys_portfoy_seri = []
    _ys_toplam_yatirim_seri = []
    _ys_deger = float(_ys_baslangic)
    _ys_toplam_yatirim = float(_ys_baslangic)
    for _ay in range(_ys_ay_sayisi):
        _ys_deger = _ys_deger * (1 + _ys_aylik_faiz) + _ys_aylik
        _ys_toplam_yatirim += _ys_aylik
        if _ay % 12 == 11:
            _ys_portfoy_seri.append(round(_ys_deger))
            _ys_toplam_yatirim_seri.append(round(_ys_toplam_yatirim))

    _ys_net_kazanc = _ys_deger - _ys_toplam_yatirim
    _ysm1, _ysm2, _ysm3 = st.columns(3)
    _ysm1.metric("Toplam Yatırım",  f"{tr_format(_ys_toplam_yatirim)} ₺")
    _ysm2.metric(f"{_ys_yil} Yıl Sonra", f"{tr_format(_ys_deger)} ₺")
    _ysm3.metric("Net Kazanç",      f"{tr_format(_ys_net_kazanc)} ₺",
                  delta=f"%{(_ys_net_kazanc/_ys_toplam_yatirim*100):.0f} getiri")

    _ys_fig = go.Figure()
    _yillar = list(range(1, _ys_yil + 1))
    _ys_fig.add_trace(go.Bar(
        x=_yillar, y=_ys_toplam_yatirim_seri, name="Yatırılan",
        marker_color=hex_rgba(acc, 0.35),
        hovertemplate='Yıl %{x}<br>Yatırılan: %{y:,.0f} ₺<extra></extra>'
    ))
    _ys_fig.add_trace(go.Scatter(
        x=_yillar, y=_ys_portfoy_seri, name="Portföy Değeri",
        line=dict(color=acc, width=2.5),
        hovertemplate='Yıl %{x}<br>Değer: %{y:,.0f} ₺<extra></extra>'
    ))
    _ys_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=txt, size=11, family=secili_font),
        height=300, margin=dict(t=30, b=40, l=50, r=20),
        xaxis=dict(color=txt, showgrid=True, gridcolor=hex_rgba(acc,0.08),
                   title=dict(text='Yıl', font=dict(size=10))),
        yaxis=dict(color=txt, showgrid=True, gridcolor=hex_rgba(acc,0.08),
                   title=dict(text='₺', font=dict(size=10))),
        legend=dict(orientation='h', x=0, y=1.08, font=dict(size=10, color=txt),
                    bgcolor='rgba(0,0,0,0)'),
        barmode='overlay',
    )
    st.plotly_chart(_ys_fig, use_container_width=True)
    st.caption(f"Aylık bileşik faiz formülü · Enflasyon dahil değil · Yıllık %{_ys_getiri} varsayılan getiri")

    st.divider()

    # ---------- J) SEKTÖR ANALİZİ ----------
    st.markdown(f"<h4 style='color:{acc};'>🏭 Sektör Analizi</h4>", unsafe_allow_html=True)

    # BIST sektör eşlemesi (kısmi — yaygın hisseler)
    _SEKTOR_MAP = {
        "Bankacılık":    ["GARAN.IS","AKBNK.IS","ISCTR.IS","YKBNK.IS","HALKB.IS","VAKBN.IS","TSKB.IS"],
        "Havacılık":     ["THYAO.IS","PGSUS.IS"],
        "Enerji":        ["TUPRS.IS","AKENR.IS","AKSEN.IS","ZOREN.IS","ODAS.IS","GWIND.IS"],
        "Demir-Çelik":   ["EREGL.IS","KRDMD.IS","ISGYO.IS"],
        "Perakende":     ["BIMAS.IS","MGROS.IS","SOKM.IS","CRFSA.IS"],
        "Teknoloji":     ["LOGO.IS","INDES.IS","NETAS.IS","ARENA.IS","LINK.IS"],
        "İnşaat/GYO":    ["TOASO.IS","EKGYO.IS","ISGYO.IS","OZGYO.IS"],
        "Kimya/İlaç":    ["SASA.IS","DEVA.IS","ECILC.IS","SELVA.IS"],
        "Otomotiv":      ["TOASO.IS","FROTO.IS","OTKAR.IS","DOAS.IS"],
        "Cam/Seramik":   ["TRKCM.IS","SODA.IS","CIMSA.IS","ADANA.IS"],
    }

    @st.cache_data(ttl=1800)
    def sektor_performans():
        sonuclar = {}
        for sektor, hisseler in _SEKTOR_MAP.items():
            getiriler = []
            for h in hisseler:
                d = fetch_stock_data(h)
                if d and not d['hist'].empty and len(d['hist']) >= 2:
                    try:
                        bas = float(d['hist']['Close'].iloc[0])
                        son = float(d['hist']['Close'].iloc[-1])
                        if bas > 0:
                            getiriler.append((son - bas) / bas * 100)
                    except Exception:
                        pass
            if getiriler:
                sonuclar[sektor] = round(sum(getiriler) / len(getiriler), 2)
        return dict(sorted(sonuclar.items(), key=lambda x: x[1], reverse=True))

    with st.spinner("Sektör verileri hesaplanıyor..."):
        _sek_perf = sektor_performans()

    if _sek_perf:
        _sek_renkler = ['#00e676' if v >= 0 else '#ff1744' for v in _sek_perf.values()]
        _sek_fig = go.Figure(go.Bar(
            x=list(_sek_perf.values()),
            y=list(_sek_perf.keys()),
            orientation='h',
            marker_color=_sek_renkler,
            text=[f"%{v:+.1f}" for v in _sek_perf.values()],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>60G Ortalama: %{x:.1f}%<extra></extra>',
        ))
        _sek_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=txt, size=11, family=secili_font),
            height=max(280, len(_sek_perf) * 28 + 60),
            margin=dict(t=30, b=30, l=120, r=70),
            xaxis=dict(color=txt, showgrid=True, gridcolor=hex_rgba(acc,0.08),
                       zeroline=True, zerolinecolor=txt, zerolinewidth=0.5),
            yaxis=dict(color=txt, showgrid=False),
            title=dict(text="Sektör 60G Ortalama Getirisi",
                       font=dict(size=13, color=acc), x=0.5, xanchor='center'),
        )
        st.plotly_chart(_sek_fig, use_container_width=True)

        # Portföydeki hisselerin sektör dağılımı
        _port_sektor = {}
        for _ph in [x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası']:
            for _sk, _sl in _SEKTOR_MAP.items():
                if _ph in _sl:
                    _port_sektor[_ph] = _sk
                    break
        if _port_sektor:
            st.markdown(
                f"<div style='font-size:11px;opacity:0.6;margin-top:4px;'>"
                f"<b>Portföyünüzdeki hisselerin sektörleri:</b> "
                + " · ".join(f"{h} → {s}" for h, s in _port_sektor.items()) +
                f"</div>",
                unsafe_allow_html=True
            )
        st.caption("Veri: yfinance 60 günlük kapanış fiyatları · 30dk önbellekte")
    else:
        st.info("Sektör verisi alınamadı.")

# ==========================================
# HABERLER TABU
# ==========================================
with tab_haberler:
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>📰 Portföy Haber Akışı</h4>", unsafe_allow_html=True)
    st.markdown(
        f"<small style='color:{acc}88;'>Google News · Bloomberg HT · Dünya Gazetesi · Reuters TR — 15dk önbellekte</small>",
        unsafe_allow_html=True
    )

    portfoy_hisseleri_haber = sorted(set(
        x['Hisse'] for x in full_data if x['Piyasa'] == 'Türk Borsası'
    ))

    if portfoy_hisseleri_haber:
        with st.spinner("Haberler yükleniyor..."):
            haberler = fetch_haberler(tuple(portfoy_hisseleri_haber))

        if haberler:
            # --- Duyarlılık skoru ---
            _POZITIF = ['artış','yüksel','rekor','kar','büyüme','güçlü','hedef','al ',
                        'pozitif','başarı','ivme','fırsat','aşıldı','rally','yeni yüksek']
            _NEGATIF = ['düşüş','geriledi','kayıp','zarar','risk','uyarı','kriz','endişe',
                        'baskı','satış','negatif','darbesi','zayıf','kötüleş','tehdit']
            _duyarlilik = {}
            for _h in portfoy_hisseleri_haber:
                _code = _h.replace('.IS','')
                _ilgili = [n for n in haberler if n['hisse'] == _code]
                if not _ilgili:
                    continue
                _poz = sum(1 for n in _ilgili
                           if any(k in n['baslik'].lower() for k in _POZITIF))
                _neg = sum(1 for n in _ilgili
                           if any(k in n['baslik'].lower() for k in _NEGATIF))
                _duyarlilik[_code] = {'poz': _poz, 'neg': _neg, 'toplam': len(_ilgili)}

            if _duyarlilik:
                st.markdown(f"<h5 style='color:{acc};margin-top:4px;'>📊 Haber Duyarlılığı</h5>",
                            unsafe_allow_html=True)
                _duy_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;'>"
                for _hk, _sv in sorted(_duyarlilik.items()):
                    _net = _sv['poz'] - _sv['neg']
                    _dc  = '#00e676' if _net > 0 else ('#ff1744' if _net < 0 else '#888')
                    _etiket = '😊 Olumlu' if _net > 0 else ('😟 Olumsuz' if _net < 0 else '😐 Nötr')
                    _duy_html += (
                        f"<div style='background:{box};border:1px solid {_dc}44;"
                        f"border-left:3px solid {_dc};border-radius:8px;padding:8px 12px;"
                        f"min-width:100px;'>"
                        f"<div style='font-size:11px;font-weight:700;color:{_dc};'>{_hk}</div>"
                        f"<div style='font-size:10px;margin-top:2px;'>{_etiket}</div>"
                        f"<div style='font-size:9px;opacity:0.5;margin-top:2px;'>"
                        f"✅{_sv['poz']} ❌{_sv['neg']} / {_sv['toplam']} haber</div>"
                        f"</div>"
                    )
                _duy_html += "</div>"
                st.markdown(_duy_html, unsafe_allow_html=True)
                st.caption("Duyarlılık: başlık anahtar kelime analizi ile hesaplanır, yaklaşıktır.")

            # Hisse filtresi — PİYASA ve GENEL de dahil
            _filtre_secenekler = ["Tümü"] + sorted(set(
                h['hisse'] for h in haberler if h['hisse'] not in ('', None)
            ))
            haber_filtre = st.multiselect(
                "Filtrele",
                _filtre_secenekler,
                default=["Tümü"],
                key="haber_filtre"
            )
            gosterilecek = haberler
            if "Tümü" not in haber_filtre and haber_filtre:
                gosterilecek = [h for h in haberler if h['hisse'] in haber_filtre]

            for haber in gosterilecek[:30]:
                zaman_str = ""
                if haber['zaman']:
                    try:
                        dt = datetime.fromtimestamp(haber['zaman'], tz=pytz.timezone('Europe/Istanbul'))
                        zaman_str = dt.strftime('%d.%m.%Y %H:%M')
                    except Exception:
                        pass

                _hisse_badge = haber['hisse'] or 'GENEL'
                _badge_renk  = acc if _hisse_badge not in ('PİYASA', 'GENEL') else '#888'
                st.markdown(
                    f"<div style='background:{box};border:1px solid {acc}22;border-radius:8px;"
                    f"padding:12px 16px;margin-bottom:8px;'>"
                    f"<div style='display:flex;align-items:flex-start;gap:10px;'>"
                    f"  <div style='flex:1;'>"
                    f"    <span style='background:{_badge_renk}22;color:{_badge_renk};font-size:10px;"
                    f"          font-weight:700;padding:2px 7px;border-radius:4px;margin-right:8px;"
                    f"          white-space:nowrap;'>{_hisse_badge}</span>"
                    f"    <a href='{haber['url']}' target='_blank' style='color:{txt};"
                    f"       text-decoration:none;font-size:13px;font-weight:600;"
                    f"       line-height:1.4;'>{haber['baslik']}</a>"
                    f"  </div>"
                    f"</div>"
                    f"<div style='margin-top:6px;display:flex;gap:16px;'>"
                    f"  <span style='font-size:10px;opacity:0.45;'>📰 {haber['kaynak']}</span>"
                    f"  <span style='font-size:10px;opacity:0.45;'>🕒 {zaman_str}</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Haber yüklenemedi. İnternet bağlantısını ve RSS kaynaklarını kontrol et.")
    else:
        st.info("Haber akışı için portföyde Türk Borsası hissesi bulunmalıdır.")


# ==========================================
# TEMEL VERİLER TABU
# ==========================================
with tab_temel:
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>🏦 Temel Analiz Verileri</h4>", unsafe_allow_html=True)
    st.markdown(
        f"<small style='color:{acc}88;'>F/K, PD/DD, Borç/Özsermaye — yfinance üzerinden · Veriler yaklaşık değerdir</small>",
        unsafe_allow_html=True
    )

    portfoy_bist_temel = [x for x in full_data if x['Piyasa'] == 'Türk Borsası']

    if portfoy_bist_temel:
        with st.spinner("Temel veriler çekiliyor..."):
            temel_rows = []
            for item in portfoy_bist_temel:
                tv = fetch_temel_veri(item['Hisse'])
                temel_rows.append({**item, 'temel': tv or {}})

        # Tablo
        tbl = (
            "<table class='kral-table'><thead><tr>"
            "<th>HİSSE</th><th>F/K</th><th>PD/DD</th>"
            "<th>BORÇ/ÖZSERM.</th><th>PİYASA DEĞERİ</th>"
            "<th>TEMETTÜ VERİMİ</th><th>GÜNCEL FİYAT</th>"
            "</tr></thead><tbody>"
        )
        for r in temel_rows:
            tv = r['temel']

            def fmt_val(v, suffix=''):
                if v is None: return "<span style='opacity:0.35;'>—</span>"
                return f"{v}{suffix}"

            def fmt_mkt(v):
                if v is None: return "<span style='opacity:0.35;'>—</span>"
                if v >= 1e9:  return f"{v/1e9:.1f} Mr ₺"
                if v >= 1e6:  return f"{v/1e6:.0f} Mn ₺"
                return f"{v:,.0f} ₺"

            # Borç/Özsermaye rengi
            bo = tv.get('Borc_Ozserm')
            bo_color = '#00e676' if bo is not None and bo < 0.5 else ('#ffc107' if bo is not None and bo < 1.5 else '#ff1744')
            bo_str = f"<span style='color:{bo_color};font-weight:600;'>{bo}</span>" if bo is not None else "<span style='opacity:0.35;'>—</span>"

            # F/K rengi
            fk = tv.get('FK')
            fk_color = '#00e676' if fk is not None and fk < 15 else ('#ffc107' if fk is not None and fk < 30 else '#ff1744')
            fk_str = f"<span style='color:{fk_color};font-weight:600;'>{fk}</span>" if fk is not None else "<span style='opacity:0.35;'>—</span>"

            tbl += (
                f"<tr>"
                f"<td><b>{r['Hisse']}</b></td>"
                f"<td>{fk_str}</td>"
                f"<td>{fmt_val(tv.get('PD_DD'))}</td>"
                f"<td>{bo_str}</td>"
                f"<td style='font-size:11px;'>{fmt_mkt(tv.get('Piyasa_Degeri'))}</td>"
                f"<td>{'%'+str(tv.get('Temettu_Verimi')) if tv.get('Temettu_Verimi') else '<span style=\"opacity:0.35;\">—</span>'}</td>"
                f"<td>{tr_format4(r['Güncel'])} ₺</td>"
                f"</tr>"
            )
        tbl += "</tbody></table>"
        st.markdown(tbl, unsafe_allow_html=True)

        # Açıklama kartı
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:{box};border:1px solid {acc}22;border-radius:8px;padding:12px 16px;"
            f"display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:11px;'>"
            f"<div><b style='color:{acc};'>F/K (Fiyat/Kazanç)</b><br>"
            f"<span style='opacity:0.6;'>&lt;15 ucuz · 15–30 makul · &gt;30 pahalı</span></div>"
            f"<div><b style='color:{acc};'>PD/DD (Piyasa/Defter)</b><br>"
            f"<span style='opacity:0.6;'>&lt;1 defter altı · 1–3 makul · &gt;3 prim</span></div>"
            f"<div><b style='color:#00e676;'>Borç/Özserm. &lt;0.5</b> düşük · "
            f"<b style='color:#ffc107;'>0.5–1.5</b> orta · "
            f"<b style='color:#ff1744;'>&gt;1.5</b> yüksek</div>"
            f"<div style='opacity:0.5;'>Veriler yfinance üzerinden çekilmekte olup kesin değildir.</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        # BIST100 Karşılaştırma grafiği
        st.divider()
        st.markdown(f"<h4 style='color:{acc};'>📊 Portföy vs BIST100 (60 Gün Normalize)</h4>", unsafe_allow_html=True)
        bist_hisseler = tuple(x['Hisse'] for x in portfoy_bist_temel)
        with st.spinner("Karşılaştırma grafiği hazırlanıyor..."):
            bist_norm, portfoy_norm = fetch_bist100_karsilastirma(bist_hisseler)

        if bist_norm is not None:
            kars_fig = go.Figure()
            kars_fig.add_trace(go.Scatter(
                x=bist_norm.index, y=bist_norm.values,
                mode='lines', name='BIST 100',
                line=dict(color='#ffc107', width=2, dash='dot'),
                hovertemplate='<b>BIST100</b><br>%{x|%d.%m.%Y}<br>%{y:.1f}<extra></extra>',
            ))
            if portfoy_norm is not None:
                kars_fig.add_trace(go.Scatter(
                    x=portfoy_norm.index, y=portfoy_norm.values,
                    mode='lines', name='Portföy Ort.',
                    line=dict(color=acc, width=2.5),
                    fill='tonexty', fillcolor=hex_rgba(acc, 0.06),
                    hovertemplate='<b>Portföy</b><br>%{x|%d.%m.%Y}<br>%{y:.1f}<extra></extra>',
                ))
            kars_fig.add_hline(y=100, line_dash='dash', line_color=txt, opacity=0.2)
            kars_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=txt, size=11, family=secili_font),
                height=360,
                margin=dict(t=40, b=40, l=50, r=20),
                xaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt),
                yaxis=dict(showgrid=True, gridcolor=hex_rgba(acc, 0.08), color=txt,
                           title=dict(text='Normalize (Başlangıç=100)', font=dict(size=10))),
                legend=dict(orientation='h', x=0, y=1.08,
                            font=dict(size=10, color=txt), bgcolor='rgba(0,0,0,0)'),
                title=dict(text="Portföy Ortalama vs BIST100",
                           font=dict(size=13, color=acc), x=0.5, xanchor='center'),
            )
            st.plotly_chart(kars_fig, use_container_width=True)

            # Beta hesapla
            if portfoy_norm is not None and len(bist_norm) > 10:
                try:
                    bist_ret = bist_norm.pct_change().dropna()
                    port_ret = portfoy_norm.pct_change().dropna()
                    min_l = min(len(bist_ret), len(port_ret))
                    cov    = np.cov(port_ret.values[-min_l:], bist_ret.values[-min_l:])
                    beta   = round(cov[0, 1] / cov[1, 1], 2) if cov[1, 1] != 0 else None
                    if beta is not None:
                        beta_color = '#00e676' if beta < 1 else ('#ffc107' if beta < 1.5 else '#ff1744')
                        st.markdown(
                            f"<div style='text-align:center;margin-top:4px;'>"
                            f"<span style='font-size:12px;opacity:0.6;'>Portföy Betası: </span>"
                            f"<span style='color:{beta_color};font-weight:700;font-size:16px;'>β = {beta}</span>"
                            f"<span style='font-size:11px;opacity:0.45;'> "
                            f"({'düşük risk' if beta < 1 else ('orta risk' if beta < 1.5 else 'yüksek risk')})</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                except Exception:
                    pass
        else:
            st.info("Karşılaştırma verisi alınamadı.")
    else:
        st.info("Türk Borsası'nda hisse bulunamadı.")


# ==========================================
# EKONOMİK TAKVİM TABU
# ==========================================
with tab_takvim:
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>📅 Ekonomik Takvim</h4>", unsafe_allow_html=True)
    st.markdown(
        f"<small style='color:{acc}88;'>TCMB · Enflasyon · BIST önemli tarihler · 2025–2026</small>",
        unsafe_allow_html=True
    )

    # Sabit ekonomik takvim verisi
    _TAKVIM = [
        # 2025
        {"tarih":"2025-01-23","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-02-03","kategori":"Enflasyon","olay":"Ocak 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-02-27","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-03-03","kategori":"Enflasyon","olay":"Şubat 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-03-06","kategori":"BIST","olay":"Şubat Sanayi Üretimi Endeksi","etki":"Orta"},
        {"tarih":"2025-04-03","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-04-03","kategori":"Enflasyon","olay":"Mart 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-05-05","kategori":"Enflasyon","olay":"Nisan 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-05-22","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-06-03","kategori":"Enflasyon","olay":"Mayıs 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-07-03","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-07-03","kategori":"Enflasyon","olay":"Haziran 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-08-04","kategori":"Enflasyon","olay":"Temmuz 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-08-21","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-09-03","kategori":"Enflasyon","olay":"Ağustos 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-10-02","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-10-03","kategori":"Enflasyon","olay":"Eylül 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-11-04","kategori":"Enflasyon","olay":"Ekim 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-11-20","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2025-12-03","kategori":"Enflasyon","olay":"Kasım 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2025-12-25","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        # 2026
        {"tarih":"2026-01-05","kategori":"Enflasyon","olay":"Aralık 2025 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-01-22","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-02-03","kategori":"Enflasyon","olay":"Ocak 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-02-26","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-03-03","kategori":"Enflasyon","olay":"Şubat 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-04-02","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-04-03","kategori":"Enflasyon","olay":"Mart 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-05-04","kategori":"Enflasyon","olay":"Nisan 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-05-21","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-06-03","kategori":"Enflasyon","olay":"Mayıs 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-07-02","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-07-03","kategori":"Enflasyon","olay":"Haziran 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-08-03","kategori":"Enflasyon","olay":"Temmuz 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-08-20","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-09-03","kategori":"Enflasyon","olay":"Ağustos 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-10-01","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-10-05","kategori":"Enflasyon","olay":"Eylül 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-11-04","kategori":"Enflasyon","olay":"Ekim 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-11-19","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
        {"tarih":"2026-12-03","kategori":"Enflasyon","olay":"Kasım 2026 TÜFE Açıklaması","etki":"Yüksek"},
        {"tarih":"2026-12-24","kategori":"TCMB","olay":"TCMB Para Politikası Kurulu Toplantısı","etki":"Yüksek"},
    ]

    _bugün  = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y-%m-%d')
    _kat_renk = {"TCMB": "#00D4FF", "Enflasyon": "#FF6B6B", "BIST": "#6BCB77", "Diğer": "#888"}

    # Filtre
    _tk_f1, _tk_f2 = st.columns([2, 2])
    _tk_kat  = _tk_f1.multiselect("Kategori", ["Tümü","TCMB","Enflasyon","BIST"],
                                   default=["Tümü"], key="tk_kat")
    _tk_donem = _tk_f2.radio("Dönem", ["Yaklaşan","Geçmiş","Tümü"], horizontal=True, key="tk_donem")

    _takvim_f = _TAKVIM
    if "Tümü" not in _tk_kat and _tk_kat:
        _takvim_f = [x for x in _takvim_f if x['kategori'] in _tk_kat]
    if _tk_donem == "Yaklaşan":
        _takvim_f = [x for x in _takvim_f if x['tarih'] >= _bugün]
    elif _tk_donem == "Geçmiş":
        _takvim_f = [x for x in _takvim_f if x['tarih'] < _bugün]

    _takvim_f = sorted(_takvim_f, key=lambda x: x['tarih'],
                       reverse=(_tk_donem == "Geçmiş"))

    # Yaklaşan event varsa kaç gün kaldığını hesapla
    for _ev in _takvim_f[:20]:
        try:
            _ev_dt  = datetime.strptime(_ev['tarih'], '%Y-%m-%d')
            _bug_dt = datetime.strptime(_bugün, '%Y-%m-%d')
            _delta  = (_ev_dt - _bug_dt).days
            _renk   = _kat_renk.get(_ev['kategori'], '#888')
            _gecti  = _ev['tarih'] < _bugün
            _bg     = f"{box}" if not _gecti else f"{t_sec['bg']}"
            _opc    = "1" if not _gecti else "0.45"
            _gun_str = (f"<b style='color:{_renk};'>{_delta} gün kaldı</b>"
                        if not _gecti and _delta >= 0
                        else ("<b style='color:#00e676;'>BUGÜN ⚡</b>" if _delta == 0
                              else f"<span style='opacity:0.4;'>{abs(_delta)} gün önce</span>"))
            st.markdown(
                f"<div style='background:{_bg};border:1px solid {_renk}33;"
                f"border-left:3px solid {_renk};border-radius:8px;"
                f"padding:10px 14px;margin-bottom:6px;opacity:{_opc};'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"  <div>"
                f"    <span style='background:{_renk}22;color:{_renk};font-size:9px;"
                f"          font-weight:700;padding:2px 6px;border-radius:4px;margin-right:8px;'>"
                f"    {_ev['kategori']}</span>"
                f"    <span style='font-size:13px;font-weight:600;'>{_ev['olay']}</span>"
                f"  </div>"
                f"  <div style='text-align:right;white-space:nowrap;'>"
                f"    <div style='font-size:11px;opacity:0.6;'>{_ev['tarih']}</div>"
                f"    <div style='font-size:11px;margin-top:2px;'>{_gun_str}</div>"
                f"  </div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        except Exception:
            continue

    if not _takvim_f:
        st.info("Seçilen filtreler için etkinlik bulunamadı.")

    st.divider()
    st.markdown(
        f"<small style='color:{acc}66;'>Tarihler tahmini olup değişebilir. "
        f"Kesin tarihler için TCMB ve TÜİK resmi sitelerini takip edin.</small>",
        unsafe_allow_html=True
    )

# ==========================================
# EKRAN AYARLARI TABU
# ==========================================
with tab_olcek:
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>📐 Ekran & Görünüm Ayarları</h4>",
                unsafe_allow_html=True)

    # --- A) EKRAN BOYUTU CİVE ---
    # JavaScript ile anlık ekran genişliğini ve viewport'u ölç
    olcek_js = f"""
    <div id="ekran-bilgi" style="background:{box};border:1px solid {acc}33;
         border-radius:10px;padding:14px 18px;margin-bottom:12px;">
      <div style="color:{acc};font-weight:700;font-size:11px;letter-spacing:1px;margin-bottom:10px;">
        📱 ANLLIK EKRAN BİLGİSİ
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
        <div>
          <div style="font-size:10px;opacity:0.5;">EKRAN GENİŞLİĞİ</div>
          <div id="ekran-gen" style="font-size:18px;font-weight:700;color:{acc};">—</div>
          <div style="font-size:9px;opacity:0.4;">px (fiziksel)</div>
        </div>
        <div>
          <div style="font-size:10px;opacity:0.5;">VIEWPORT GENİŞLİĞİ</div>
          <div id="viewport-gen" style="font-size:18px;font-weight:700;color:{acc};">—</div>
          <div style="font-size:9px;opacity:0.4;">px (tarayıcı)</div>
        </div>
        <div>
          <div style="font-size:10px;opacity:0.5;">CİHAZ TÜRÜ</div>
          <div id="cihaz-turu" style="font-size:14px;font-weight:700;color:{acc};">—</div>
          <div style="font-size:9px;opacity:0.4;">tahmini</div>
        </div>
      </div>
      <div style="margin-top:10px;padding-top:10px;border-top:1px solid {acc}18;">
        <div style="font-size:10px;opacity:0.5;">PIXEL RATIO</div>
        <div id="pixel-ratio" style="font-size:12px;color:{txt};opacity:0.7;">—</div>
      </div>
      <div style="margin-top:6px;">
        <div style="font-size:10px;opacity:0.5;">USER AGENT (Cihaz Bilgisi)</div>
        <div id="user-agent" style="font-size:10px;color:{txt};opacity:0.55;word-break:break-all;line-height:1.4;">—</div>
      </div>
    </div>
    <script>
    function guncelle() {{
        var w = screen.width, vw = window.innerWidth;
        document.getElementById('ekran-gen').innerText = w + ' px';
        document.getElementById('viewport-gen').innerText = vw + ' px';
        document.getElementById('pixel-ratio').innerText = 'x' + window.devicePixelRatio.toFixed(1);
        document.getElementById('user-agent').innerText = navigator.userAgent;
        var tur = vw < 480 ? '📱 Telefon' : vw < 768 ? '📱 Geniş Telefon' : vw < 1024 ? '💻 Tablet' : '🖥️ Masaüstü';
        document.getElementById('cihaz-turu').innerText = tur;
    }}
    guncelle();
    window.addEventListener('resize', guncelle);
    setInterval(guncelle, 2000);
    </script>
    """
    st.components.v1.html(olcek_js, height=240)

    st.divider()

    # --- B) TABLO AYARLARI ---
    st.markdown(f"<div style='color:{acc};font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:10px;'>🗂️ TABLO GÖRÜNÜM AYARLARI</div>",
                unsafe_allow_html=True)

    oa1, oa2 = st.columns(2)
    _yeni_font = oa1.slider(
        "Tablo yazı boyutu (px)", 9, 18,
        value=st.session_state.tablo_font, key="oa_font"
    )
    _yeni_pad = oa2.slider(
        "Tablo hücre boşluğu (px)", 4, 20,
        value=st.session_state.tablo_padding, key="oa_pad"
    )
    if _yeni_font != st.session_state.tablo_font or _yeni_pad != st.session_state.tablo_padding:
        st.session_state.tablo_font    = _yeni_font
        st.session_state.tablo_padding = _yeni_pad
        st.rerun()

    # Önizleme satırı
    st.markdown(
        f"<div style='font-size:10px;opacity:0.5;margin-bottom:4px;'>Önizleme:</div>"
        f"<table class='kral-table' style='width:auto;'><thead>"
        f"<tr><th>HİSSE</th><th>GÜNCEL</th><th>K/Z</th><th>TOPLAM</th></tr>"
        f"</thead><tbody>"
        f"<tr><td><b>GARAN.IS</b></td><td>42,5000 ₺</td>"
        f"<td style='color:#00e676;font-weight:bold;'>+1.250,00 ₺</td>"
        f"<td><b>42.500,00 ₺</b></td></tr>"
        f"<tr><td><b>THYAO.IS</b></td><td>198,3000 ₺</td>"
        f"<td style='color:#ff1744;font-weight:bold;'>-800,00 ₺</td>"
        f"<td><b>198.300,00 ₺</b></td></tr>"
        f"</tbody></table>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- C) MOBİL UYUMLULUK MODU ---
    st.markdown(f"<div style='color:{acc};font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:10px;'>📱 MOBİL UYUMLULUK MODU</div>",
                unsafe_allow_html=True)

    _mobil_toggle = st.toggle(
        "Mobil Modu Etkinleştir",
        value=st.session_state.mobil_mod,
        key="mobil_toggle",
        help="Tablolarda daha küçük font ve padding kullanır, ticker aralığını sıkıştırır"
    )
    if _mobil_toggle != st.session_state.mobil_mod:
        st.session_state.mobil_mod = _mobil_toggle
        st.rerun()

    if st.session_state.mobil_mod:
        st.success("✅ Mobil mod aktif — tablolar telefon ekranına optimize edildi")
    else:
        st.info("📺 Masaüstü modu aktif")

    # Mobil mod kısaca ne yapar
    st.markdown(
        f"<div style='background:{box};border:1px solid {acc}22;border-radius:8px;"
        f"padding:10px 14px;margin-top:8px;font-size:11px;line-height:1.7;opacity:0.75;'>"
        f"<b style='color:{acc};'>Mobil mod değişiklikleri:</b><br>"
        f"• Tablo padding: 12px → 6px<br>"
        f"• Tablo font: seçili boyut → 11px<br>"
        f"• Ticker aralığı: 60px → 30px<br>"
        f"• Metrik kartı padding sıkıştırılır"
        f"</div>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- D) HIZLI RESET ---
    if st.button("🔄 Varsayılana Sıfırla", key="olcek_reset", use_container_width=True):
        st.session_state.tablo_font    = 13
        st.session_state.tablo_padding = 12
        st.session_state.mobil_mod     = False
        st.rerun()

    st.divider()

    # --- KULLANICI YÖNETİMİ ---
    acc = t_sec['accent']; txt = t_sec['text']; box = t_sec['box']
    st.markdown(f"<h4 style='color:{acc};'>👤 Kullanıcı Yönetimi</h4>", unsafe_allow_html=True)

    _KULLANICI_DOSYASI2 = _veri_yolu("kullanicilar.json")

    def _kullanicilar_oku2():
        if not os.path.exists(_KULLANICI_DOSYASI2):
            return []
        try:
            with open(_KULLANICI_DOSYASI2, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    _kl_listesi = _kullanicilar_oku2()

    # Mevcut kullanıcıları listele
    if _kl_listesi:
        st.markdown("**Kayıtlı kullanıcılar:**")
        for _klu in _kl_listesi:
            _klu_c1, _klu_c2 = st.columns([4, 1])
            _klu_c1.markdown(
                f"<div style='font-size:12px;'>👤 <b>{_klu['kullanici']}</b> "
                f"<span style='opacity:0.5;font-size:10px;'>({_klu.get('rol','kullanici')})</span></div>",
                unsafe_allow_html=True
            )
            if _klu['kullanici'] != 'admin' and _klu_c2.button("❌", key=f"klu_sil_{_klu['kullanici']}"):
                _kl_listesi = [k for k in _kl_listesi if k['kullanici'] != _klu['kullanici']]
                save_json(_KULLANICI_DOSYASI2, _kl_listesi)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # PIN Değiştir
    with st.expander("🔑 PIN Değiştir"):
        with st.form("pin_degistir_form", clear_on_submit=True):
            _pd_kul  = st.text_input("Kullanıcı Adı", key="pd_kul")
            _pd_eski = st.text_input("Mevcut PIN", type="password", key="pd_eski")
            _pd_yeni = st.text_input("Yeni PIN (min 4 karakter)", type="password", key="pd_yeni")
            _pd_yeni2= st.text_input("Yeni PIN (tekrar)", type="password", key="pd_yeni2")
            if st.form_submit_button("🔑 PIN Güncelle", use_container_width=True):
                import hashlib as _hl
                _kll = _kullanicilar_oku2()
                _eski_hash = _hl.sha256(_pd_eski.encode()).hexdigest()
                _kullanici_bul = next((k for k in _kll if k['kullanici'] == _pd_kul and k['pin_hash'] == _eski_hash), None)
                if not _kullanici_bul:
                    st.error("Kullanıcı adı veya mevcut PIN hatalı.")
                elif len(_pd_yeni) < 4:
                    st.error("Yeni PIN en az 4 karakter olmalı.")
                elif _pd_yeni != _pd_yeni2:
                    st.error("Yeni PIN'ler eşleşmiyor.")
                else:
                    _kullanici_bul['pin_hash'] = _hl.sha256(_pd_yeni.encode()).hexdigest()
                    save_json(_KULLANICI_DOSYASI2, _kll)
                    st.success("✅ PIN güncellendi!")

    # Ayarlar sekmesine ekle
st.markdown("### ⭐ Pro'ya Geç")
st.markdown("Tüm özelliklere eriş — ₺59/ay")
if st.button("💳 Şimdi Abone Ol"):
    st.markdown("[Ödeme Sayfası](https://buy.stripe.com/https://buy.stripe.com/test_4gM14ncFraxpeJZ7tK0sU00)", unsafe_allow_html=True)

    # Yeni kullanıcı ekle
    with st.expander("➕ Yeni Kullanıcı Ekle"):
        with st.form("yeni_kullanici_form", clear_on_submit=True):
            _nk_adi = st.text_input("Kullanıcı Adı", key="nk_adi")
            _nk_pin = st.text_input("PIN", type="password", key="nk_pin")
            _nk_rol = st.selectbox("Rol", ["kullanici", "admin"], key="nk_rol")
            if st.form_submit_button("➕ Ekle", use_container_width=True):
                import hashlib as _hl2
                _kll2 = _kullanicilar_oku2()
                if any(k['kullanici'] == _nk_adi for k in _kll2):
                    st.error("Bu kullanıcı adı zaten alınmış.")
                elif len(_nk_pin) < 4:
                    st.error("PIN en az 4 karakter olmalı.")
                else:
                    _kll2.append({
                        "kullanici": _nk_adi.strip(),
                        "pin_hash": _hl2.sha256(_nk_pin.encode()).hexdigest(),
                        "rol": _nk_rol
                    })
                    save_json(_KULLANICI_DOSYASI2, _kll2)
                    st.success(f"✅ {_nk_adi} kullanıcısı eklendi!")
                    st.rerun()


# ==========================================
st.markdown("---")
st.caption(
    f"🕒 Son Güncelleme: {datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')}  |  "
    f"Sinyal: RSI + MA20 + MACD + Bollinger Bands  |  * Son 1 yılda temettü dağıtımı yapılmamış hisseler"
)
