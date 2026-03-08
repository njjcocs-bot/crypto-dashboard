import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime
import time

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  ESTILOS CSS PERSONALIZADOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0e1a;
        color: #e0e6f0;
    }

    .main { background-color: #0a0e1a; }
    .block-container { padding: 1.5rem 2rem; }

    .dash-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #1e2d4a;
        padding-bottom: 1rem;
    }
    .dash-title {
        font-family: 'Space Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #00d4ff;
        letter-spacing: -0.5px;
    }
    .dash-subtitle {
        font-size: 0.8rem;
        color: #4a6080;
        font-family: 'Space Mono', monospace;
    }

    .metric-card {
        background: linear-gradient(135deg, #0f1729 0%, #111d35 100%);
        border: 1px solid #1e2d4a;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #4a6080;
        font-family: 'Space Mono', monospace;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #e0e6f0;
    }
    .metric-change-pos {
        font-size: 0.85rem;
        color: #00e676;
        font-family: 'Space Mono', monospace;
    }
    .metric-change-neg {
        font-size: 0.85rem;
        color: #ff4444;
        font-family: 'Space Mono', monospace;
    }

    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 230, 118, 0.07);
        border: 1px solid rgba(0, 230, 118, 0.2);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.7rem;
        color: #00e676;
        font-family: 'Space Mono', monospace;
    }
    .live-dot {
        width: 6px;
        height: 6px;
        background: #00e676;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        display: inline-block;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    [data-testid="stSidebar"] {
        background-color: #080c18;
        border-right: 1px solid #1e2d4a;
    }
    [data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Noticias */
    .noticia-card {
        background: linear-gradient(135deg, #0f1729 0%, #111d35 100%);
        border: 1px solid #1e2d4a;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        transition: border-color 0.2s;
    }
    .noticia-card:hover { border-color: rgba(0,212,255,0.2); }
    .noticia-badge {
        font-size: 0.65rem;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        white-space: nowrap;
        margin-top: 2px;
    }
    .badge-bullish {
        background: rgba(0,230,118,0.12);
        border: 1px solid rgba(0,230,118,0.3);
        color: #00e676;
    }
    .badge-bearish {
        background: rgba(255,68,68,0.12);
        border: 1px solid rgba(255,68,68,0.3);
        color: #ff4444;
    }
    .badge-neutral {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #4a6080;
    }
    .noticia-titulo {
        font-size: 0.82rem;
        color: #c8d4e8;
        line-height: 1.4;
        flex: 1;
    }
    .noticia-titulo a {
        color: #c8d4e8;
        text-decoration: none;
    }
    .noticia-titulo a:hover { color: #00d4ff; }
    .noticia-meta {
        font-size: 0.65rem;
        color: #2a3a55;
        font-family: 'Space Mono', monospace;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  BASE DE DATOS SQLITE LOCAL
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("crypto_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simbolo TEXT,
            precio REAL,
            variacion_24h REAL,
            volumen REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_precio(simbolo, precio, variacion_24h, volumen):
    conn = sqlite3.connect("crypto_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO precios (simbolo, precio, variacion_24h, volumen, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (simbolo, precio, variacion_24h, volumen, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def obtener_historial(simbolo, limite=100):
    conn = sqlite3.connect("crypto_history.db")
    df = pd.read_sql_query(
        "SELECT * FROM precios WHERE simbolo=? ORDER BY timestamp DESC LIMIT ?",
        conn, params=(simbolo, limite)
    )
    conn.close()
    return df

# ─────────────────────────────────────────────
#  CRIPTOMONEDAS DISPONIBLES
# ─────────────────────────────────────────────
CRIPTOS = {
    "Bitcoin (BTC)": "BTCUSDT",
    "Ethereum (ETH)": "ETHUSDT",
    "BNB": "BNBUSDT",
    "Solana (SOL)": "SOLUSDT",
    "XRP": "XRPUSDT",
    "Cardano (ADA)": "ADAUSDT",
    "Dogecoin (DOGE)": "DOGEUSDT",
    "Polkadot (DOT)": "DOTUSDT",
}

# Símbolo corto para la API de noticias
SIMBOLO_CORTO = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH",
    "BNBUSDT": "BNB",
    "SOLUSDT": "SOL",
    "XRPUSDT": "XRP",
    "ADAUSDT": "ADA",
    "DOGEUSDT": "DOGE",
    "DOTUSDT": "DOT",
}

# ─────────────────────────────────────────────
#  FUNCIONES DE API (BINANCE - GRATUITA)
# ─────────────────────────────────────────────
@st.cache_data(ttl=5)
def obtener_precio_actual(simbolo):
    # Intento 1: Binance
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={simbolo}"
        r = requests.get(url, timeout=6)
        data = r.json()
        if "lastPrice" in data:
            return {
                "precio": float(data["lastPrice"]),
                "variacion_24h": float(data["priceChangePercent"]),
                "volumen": float(data["quoteVolume"]),
                "precio_max": float(data["highPrice"]),
                "precio_min": float(data["lowPrice"]),
                "precio_apertura": float(data["openPrice"]),
                "fuente": "Binance",
            }
    except Exception:
        pass

    # Intento 2: CoinGecko (fallback)
    try:
        symbol_map = {
            "BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "BNBUSDT": "binancecoin",
            "SOLUSDT": "solana",  "XRPUSDT": "ripple",   "ADAUSDT": "cardano",
            "DOGEUSDT": "dogecoin", "DOTUSDT": "polkadot",
        }
        cg_id = symbol_map.get(simbolo, "bitcoin")
        url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={cg_id}&vs_currencies=usd"
            f"&include_24hr_change=true&include_24hr_vol=true"
            f"&include_high_24h=true&include_low_24h=true"
        )
        r = requests.get(url, timeout=8)
        cg = r.json().get(cg_id, {})
        if cg:
            precio = cg.get("usd", 0)
            return {
                "precio":         precio,
                "variacion_24h":  cg.get("usd_24h_change", 0),
                "volumen":        cg.get("usd_24h_vol", 0),
                "precio_max":     cg.get("usd_24h_high", precio),
                "precio_min":     cg.get("usd_24h_low",  precio),
                "precio_apertura": precio,
                "fuente": "CoinGecko",
            }
    except Exception:
        pass

    return None

@st.cache_data(ttl=60)
def obtener_velas(simbolo, intervalo="1h", limite=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval={intervalo}&limit={limite}"
        r = requests.get(url, timeout=5)
        data = r.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except Exception:
        return None

# ─────────────────────────────────────────────
#  NOTICIAS — RSS FEEDS PÚBLICOS (sin API key)
# ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def obtener_noticias(simbolo_corto):
    import xml.etree.ElementTree as ET

    feeds = [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
    ]

    noticias = []
    for feed_url in feeds:
        try:
            r = requests.get(feed_url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item")[:5]:
                titulo = item.findtext("title", "").strip()
                url = item.findtext("link", "#").strip()
                pub_date = item.findtext("pubDate", "")

                # Filtrar por símbolo si aparece en el título
                keywords = {
                    "BTC": ["bitcoin", "btc"],
                    "ETH": ["ethereum", "eth", "ether"],
                    "BNB": ["bnb", "binance"],
                    "SOL": ["solana", "sol"],
                    "XRP": ["xrp", "ripple"],
                    "ADA": ["cardano", "ada"],
                    "DOGE": ["dogecoin", "doge"],
                    "DOT": ["polkadot", "dot"],
                }
                palabras = keywords.get(simbolo_corto, [])
                titulo_lower = titulo.lower()
                es_relevante = any(p in titulo_lower for p in palabras)

                # Tiempo relativo
                tiempo = ""
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_date)
                    diff = datetime.utcnow() - dt.replace(tzinfo=None)
                    mins = int(diff.total_seconds() / 60)
                    if mins < 60:
                        tiempo = f"hace {mins} min"
                    elif mins < 1440:
                        tiempo = f"hace {mins // 60}h"
                    else:
                        tiempo = f"hace {mins // 1440}d"
                except Exception:
                    tiempo = ""

                # Sentimiento simple por palabras clave
                positivas = ["surge", "rally", "gain", "rise", "bull", "high", "up", "record", "growth", "sube", "alcanza", "supera"]
                negativas = ["crash", "drop", "fall", "bear", "low", "down", "hack", "ban", "fear", "cae", "baja", "pierde"]
                pos = sum(1 for p in positivas if p in titulo_lower)
                neg = sum(1 for p in negativas if p in titulo_lower)
                if pos > neg:
                    sentimiento = "bullish"
                elif neg > pos:
                    sentimiento = "bearish"
                else:
                    sentimiento = "neutral"

                # Fuente
                fuente = feed_url.split("/")[2].replace("www.", "")

                noticias.append({
                    "titulo": titulo,
                    "url": url,
                    "sentimiento": sentimiento,
                    "tiempo": tiempo,
                    "fuente": fuente,
                    "relevante": es_relevante,
                })
        except Exception:
            continue

    # Ordenar todo por tiempo (más reciente primero)
    def mins_noticia(n):
        try:
            import re
            t = n.get("tiempo", "")
            if not t: return 9999
            num = int(re.search(r"\d+", t).group())
            if "min" in t: return num
            if "h"   in t: return num * 60
            if "d"   in t: return num * 1440
        except: pass
        return 9999
    noticias.sort(key=mins_noticia)
    return noticias[:10]


# ─────────────────────────────────────────────
#  TWEETS / MENCIONES DE PERSONAS INFLUYENTES
# ─────────────────────────────────────────────
@st.cache_data(ttl=180)
def obtener_menciones_influyentes():
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    PERSONAS = {
        "Elon Musk":     "elon+musk",
        "Donald Trump":  "trump",
        "Michael Saylor":"michael+saylor",
        "Cathie Wood":   "cathie+wood",
        "Jerome Powell": "jerome+powell",
    }

    KEYWORDS_CRYPTO = [
        "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
        "blockchain", "doge", "dogecoin", "xrp", "ripple", "altcoin",
        "solana", "sol", "binance", "coinbase", "stablecoin", "usdt",
        "inflation", "inflación", "fed", "interest rate", "tasa", "economy",
        "economía", "market", "mercado", "stock", "wall street", "dollar",
        "dólar", "tariff", "arancel", "recession", "recesión", "treasury",
    ]

    resultados = []

    for nombre, query in PERSONAS.items():
        query_full = f"{query}+crypto+OR+bitcoin+OR+economy+OR+market"
        url = f"https://news.google.com/rss/search?q={query_full}&hl=en&gl=US&ceid=US:en"
        try:
            r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item")[:4]:
                titulo = item.findtext("title", "").strip()
                link   = item.findtext("link", "#").strip()
                fecha  = item.findtext("pubDate", "")
                fuente_tag = item.find("{http://purl.org/dc/elements/1.1/}creator")
                fuente = fuente_tag.text if fuente_tag is not None else link.split("/")[2] if link != "#" else "Google News"

                titulo_lower = titulo.lower()

                # Filtrar que realmente mencione a la persona Y tenga keyword relevante
                nombre_lower = nombre.lower().split()[0]  # "elon", "donald", etc
                apellido_lower = nombre.lower().split()[-1]  # "musk", "trump", etc
                menciona_persona = nombre_lower in titulo_lower or apellido_lower in titulo_lower
                menciona_tema    = any(k in titulo_lower for k in KEYWORDS_CRYPTO)

                if not (menciona_persona and menciona_tema):
                    continue

                # Tiempo relativo
                tiempo = ""
                try:
                    dt = parsedate_to_datetime(fecha)
                    diff = datetime.utcnow() - dt.replace(tzinfo=None)
                    mins = int(diff.total_seconds() / 60)
                    if mins < 60:
                        tiempo = f"hace {mins} min"
                    elif mins < 1440:
                        tiempo = f"hace {mins // 60}h"
                    else:
                        tiempo = f"hace {mins // 1440}d"
                except Exception:
                    tiempo = ""

                # Sentimiento
                positivas = ["surge", "rally", "gain", "rise", "bull", "high", "record", "growth", "boost", "support", "buy"]
                negativas = ["crash", "drop", "fall", "bear", "low", "hack", "ban", "fear", "sell", "warning", "concern", "loss"]
                pos = sum(1 for p in positivas if p in titulo_lower)
                neg = sum(1 for p in negativas if p in titulo_lower)
                sentimiento = "bullish" if pos > neg else ("bearish" if neg > pos else "neutral")

                resultados.append({
                    "persona":     nombre,
                    "titulo":      titulo,
                    "url":         link,
                    "fuente":      fuente,
                    "tiempo":      tiempo,
                    "sentimiento": sentimiento,
                })

        except Exception:
            continue

    # Ordenar por más reciente (tiempo más corto primero)
    def sort_key(x):
        try:
            t = x["tiempo"]
            if not t:
                return 9999
            import re
            n = int(re.search(r"\d+", t).group())
            if "min" in t:  return n
            if "h"   in t:  return n * 60
            if "d"   in t:  return n * 1440
        except Exception:
            pass
        return 9999

    resultados.sort(key=sort_key)
    return resultados[:12]

# ─────────────────────────────────────────────
#  GRÁFICOS
# ─────────────────────────────────────────────
def crear_grafico_velas(df, nombre):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25]
    )

    # Velas — sin fillcolor para evitar errores de formato
    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name=nombre,
        increasing_line_color="#00e676",
        decreasing_line_color="#ff4444",
    ), row=1, col=1)

    # Media móvil 20
    df["ma20"] = df["close"].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["ma20"],
        name="MA 20",
        line=dict(color="#00d4ff", width=1.5, dash="dot"),
        opacity=0.8
    ), row=1, col=1)

    # Volumen con colores rgba correctos
    colores_vol = [
        "rgba(0, 230, 118, 0.33)" if c >= o else "rgba(255, 68, 68, 0.33)"
        for c, o in zip(df["close"], df["open"])
    ]
    fig.add_trace(go.Bar(
        x=df["timestamp"], y=df["volume"],
        name="Volumen",
        marker_color=colores_vol,
        showlegend=False
    ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font=dict(family="Space Mono, monospace", color="#4a6080", size=11),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="#0f1729", bordercolor="#1e2d4a", borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=480,
    )
    fig.update_xaxes(
        gridcolor="#1e2d4a", zeroline=False,
        showspikes=True, spikecolor="rgba(0, 212, 255, 0.27)", spikethickness=1
    )
    fig.update_yaxes(
        gridcolor="#1e2d4a", zeroline=False,
        showspikes=True, spikecolor="rgba(0, 212, 255, 0.27)", spikethickness=1
    )
    return fig

def crear_grafico_linea_historial(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"][::-1],
        y=df["precio"][::-1],
        mode="lines+markers",
        line=dict(color="#00d4ff", width=2),
        marker=dict(size=4, color="#00d4ff"),
        fill="tozeroy",
        fillcolor="rgba(0, 212, 255, 0.07)",
        name="Precio registrado"
    ))
    fig.update_layout(
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font=dict(family="Space Mono, monospace", color="#4a6080", size=10),
        margin=dict(l=0, r=0, t=10, b=0),
        height=200,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#1e2d4a", zeroline=False)
    fig.update_yaxes(gridcolor="#1e2d4a", zeroline=False)
    return fig

# ─────────────────────────────────────────────
#  FUNCIONES NUEVAS — Fear & Greed + Dólar + Economía AR
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def obtener_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        d = r.json()["data"][0]
        return {
            "valor": int(d["value"]),
            "label": d["value_classification"],
            "ok": True
        }
    except Exception:
        return {"ok": False}

@st.cache_data(ttl=120)
def obtener_dolares():
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", timeout=5)
        data = r.json()
        result = {}
        for d in data:
            nombre = d.get("nombre", "").lower()
            if "blue" in nombre:
                result["blue"] = {"compra": d["compra"], "venta": d["venta"]}
            elif "oficial" in nombre:
                result["oficial"] = {"compra": d["compra"], "venta": d["venta"]}
            elif "cripto" in nombre or "usdt" in nombre:
                result["cripto"] = {"compra": d["compra"], "venta": d["venta"]}
        result["ok"] = True
        return result
    except Exception:
        return {"ok": False}

@st.cache_data(ttl=3600)
def obtener_inflacion():
    result = {"ok": True, "mensual": "—", "fecha_m": "", "interanual": "—", "fecha_ia": "", "riesgo": "—", "fecha_r": ""}
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacion", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                ultimo = data[-1]
                result["mensual"] = ultimo.get("valor", "—")
                result["fecha_m"] = ultimo.get("fecha", "")
    except Exception:
        pass
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacionInteranual", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                ultimo = data[-1]
                result["interanual"] = ultimo.get("valor", "—")
                result["fecha_ia"]   = ultimo.get("fecha", "")
    except Exception:
        pass
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                result["riesgo"]  = data.get("valor", "—")
                result["fecha_r"] = data.get("fecha", "")
    except Exception:
        pass
    return result


# BASE DE DATOS DESACTIVADA — para reactivarla descomentá la línea de abajo
# init_db()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family: Space Mono, monospace; color: #00d4ff; font-size: 1rem;
                font-weight: 700; margin-bottom: 1.5rem;'>
        ⚙ CONFIGURACIÓN
    </div>
    """, unsafe_allow_html=True)

    cripto_nombre = st.selectbox("Criptomoneda", list(CRIPTOS.keys()), index=0)
    cripto_simbolo = CRIPTOS[cripto_nombre]

    intervalos_map = {
        "1 minuto": "1m",
        "5 minutos": "5m",
        "15 minutos": "15m",
        "1 hora": "1h",
        "4 horas": "4h",
        "1 día": "1d"
    }
    intervalo = st.selectbox("Intervalo de velas", list(intervalos_map.keys()), index=3)
    intervalo_val = intervalos_map[intervalo]

    auto_refresh = st.toggle("Auto-actualizar (10s)", value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-family: Space Mono, monospace; font-size: 0.65rem; color: #2a3a55; line-height: 1.8;'>
        PRECIOS<br>
        <span style='color: #4a6080;'>Binance API (gratuita)</span><br><br>
        NOTICIAS<br>
        <span style='color: #4a6080;'>RSS &amp; Google News</span><br><br>
        DÓLAR &amp; ECONOMÍA<br>
        <span style='color: #4a6080;'>DolarApi · ArgentinaDatos</span><br><br>
        ALOJAMIENTO<br>
        <span style='color: #00e676;'>✓ Streamlit Cloud</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONTENIDO PRINCIPAL
# ─────────────────────────────────────────────
col_title, col_badge, col_time = st.columns([3, 1, 1])
with col_title:
    st.markdown("""
    <div class="dash-header">
        <div>
            <div class="dash-title">📈 CRYPTO DASHBOARD</div>
            <div class="dash-subtitle">datos en tiempo real · sin registro · 100% gratuito</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_badge:
    st.markdown("""
    <div style='margin-top: 1rem;'>
        <span class="live-badge"><span class="live-dot"></span> EN VIVO</span>
    </div>
    """, unsafe_allow_html=True)
with col_time:
    st.markdown(f"""
    <div style='margin-top: 1.1rem; font-family: Space Mono, monospace; font-size: 0.7rem;
                color: #2a3a55; text-align: right;'>
        {datetime.now().strftime("%H:%M:%S")}
    </div>
    """, unsafe_allow_html=True)

# ── Obtener datos de la API ──
datos = obtener_precio_actual(cripto_simbolo)

if datos:
    # guardar_precio(cripto_simbolo, datos["precio"], datos["variacion_24h"], datos["volumen"])

    # ── Métricas ──
    col1, col2, col3, col4 = st.columns(4)

    precio_fmt = f"${datos['precio']:,.2f}" if datos['precio'] > 1 else f"${datos['precio']:.6f}"
    variacion = datos['variacion_24h']
    signo = "+" if variacion >= 0 else ""
    color_var = "metric-change-pos" if variacion >= 0 else "metric-change-neg"
    emoji_var = "▲" if variacion >= 0 else "▼"

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">PRECIO ACTUAL</div>
            <div class="metric-value">{precio_fmt}</div>
            <div class="{color_var}">{emoji_var} {signo}{variacion:.2f}% (24h)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">MÁXIMO 24H</div>
            <div class="metric-value" style="font-size:1.2rem; color:#00e676;">
                ${datos['precio_max']:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">MÍNIMO 24H</div>
            <div class="metric-value" style="font-size:1.2rem; color:#ff4444;">
                ${datos['precio_min']:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        vol_fmt = f"${datos['volumen']/1_000_000:.1f}M"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">VOLUMEN 24H</div>
            <div class="metric-value" style="font-size:1.2rem; color:#00d4ff;">
                {vol_fmt}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Gráfico de velas ──
    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #4a6080;
                letter-spacing: 1px; text-transform: uppercase; margin: 0.5rem 0 0.3rem;'>
        {cripto_nombre} / USDT — {intervalo}
    </div>
    """, unsafe_allow_html=True)

    df_velas = obtener_velas(cripto_simbolo, intervalo_val, 100)
    if df_velas is not None:
        st.plotly_chart(crear_grafico_velas(df_velas, cripto_nombre), use_container_width=True)
    else:
        st.markdown('''<div style="background:#0f1729;border:1px solid #1e2d4a;border-radius:10px;
            padding:2rem;text-align:center;font-family:Space Mono,monospace;
            font-size:0.75rem;color:#2a3a55;margin-bottom:1rem;">
            Cargando gráfico de velas...
        </div>''', unsafe_allow_html=True)

    # ── Noticias en tiempo real ──
    st.markdown("""
    <div style='font-family: Space Mono, monospace; font-size: 0.7rem; color: #4a6080;
                letter-spacing: 1px; text-transform: uppercase; margin: 1.2rem 0 0.6rem;'>
        📰 NOTICIAS EN TIEMPO REAL
    </div>
    """, unsafe_allow_html=True)

    simbolo_news = SIMBOLO_CORTO.get(cripto_simbolo, "BTC")
    noticias = obtener_noticias(simbolo_news)

    if noticias:
        for n in noticias:
            if n["sentimiento"] == "bullish":
                badge_class = "badge-bullish"
                badge_texto = "▲ BULLISH"
            elif n["sentimiento"] == "bearish":
                badge_class = "badge-bearish"
                badge_texto = "▼ BEARISH"
            else:
                badge_class = "badge-neutral"
                badge_texto = "● NEUTRAL"

            st.markdown(f"""
            <div class="noticia-card">
                <span class="noticia-badge {badge_class}">{badge_texto}</span>
                <div class="noticia-titulo">
                    <a href="{n['url']}" target="_blank">{n['titulo']}</a>
                    <div class="noticia-meta">{n['fuente']} · {n['tiempo']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-family: Space Mono, monospace; font-size: 0.75rem; color: #2a3a55;
                    padding: 1rem; border: 1px solid #1e2d4a; border-radius: 8px;'>
            No se pudieron cargar las noticias. Verificá tu conexión.
        </div>
        """, unsafe_allow_html=True)

    # ── Personas Influyentes ──
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#4a6080;
                letter-spacing:1px;text-transform:uppercase;margin:1.5rem 0 0.6rem;'>
        🎙 PERSONAS INFLUYENTES — CRYPTO &amp; MERCADOS
    </div>
    """, unsafe_allow_html=True)

    menciones = obtener_menciones_influyentes()

    COLORES_PERSONA = {
        "Elon Musk":      "#00d4ff",
        "Donald Trump":   "#ff4444",
        "Michael Saylor": "#00e676",
        "Cathie Wood":    "#ffb300",
        "Jerome Powell":  "#c8a0ff",
    }

    if menciones:
        for m in menciones:
            color_persona = COLORES_PERSONA.get(m["persona"], "#4a6080")
            if m["sentimiento"] == "bullish":
                badge_class = "badge-bullish"; badge_texto = "▲ BULLISH"
            elif m["sentimiento"] == "bearish":
                badge_class = "badge-bearish"; badge_texto = "▼ BEARISH"
            else:
                badge_class = "badge-neutral"; badge_texto = "● NEUTRAL"

            st.markdown(f"""
            <div class="noticia-card">
                <div style='display:flex;flex-direction:column;align-items:center;gap:4px;min-width:80px;'>
                    <div style='font-family:Space Mono,monospace;font-size:0.58rem;font-weight:700;
                                color:{color_persona};text-align:center;line-height:1.3;'>
                        {m["persona"].replace(" ", "<br>")}
                    </div>
                    <span class="noticia-badge {badge_class}">{badge_texto}</span>
                </div>
                <div class="noticia-titulo">
                    <a href="{m["url"]}" target="_blank">{m["titulo"]}</a>
                    <div class="noticia-meta">{m["fuente"]} · {m["tiempo"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-family:Space Mono,monospace;font-size:0.75rem;color:#2a3a55;
                    padding:1rem;border:1px solid #1e2d4a;border-radius:8px;text-align:center;'>
            Sin menciones recientes de personas influyentes en crypto/mercados.
        </div>
        """, unsafe_allow_html=True)

        # ── Fear & Greed + Dólar + Economía Argentina ──
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#4a6080;
                letter-spacing:1px;text-transform:uppercase;margin:1.5rem 0 0.6rem;'>
        🌡 MERCADO &amp; ECONOMÍA
    </div>
    """, unsafe_allow_html=True)

    fg_data  = obtener_fear_greed()
    dol_data = obtener_dolares()
    eco_data = obtener_inflacion()

    sec1, sec2, sec3 = st.columns([1, 1.4, 1.6])

    # ── Fear & Greed ──
    with sec1:
        if fg_data.get("ok"):
            v = fg_data["valor"]
            if v <= 25:
                fg_color = "#ff4444"; fg_emoji = "😱"
            elif v <= 45:
                fg_color = "#ff8c00"; fg_emoji = "😨"
            elif v <= 55:
                fg_color = "#e0e6f0"; fg_emoji = "😐"
            elif v <= 75:
                fg_color = "#00d4ff"; fg_emoji = "😊"
            else:
                fg_color = "#00e676"; fg_emoji = "🤑"

            # Barra visual
            barra_w = v
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">FEAR &amp; GREED INDEX</div>
                <div style='display:flex;align-items:center;gap:12px;margin:0.3rem 0;'>
                    <div style='font-family:Space Mono,monospace;font-size:2.2rem;font-weight:700;color:{fg_color};'>{v}</div>
                    <div>
                        <div style='font-size:1.2rem;'>{fg_emoji}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:{fg_color};font-weight:700;'>{fg_data["label"].upper()}</div>
                    </div>
                </div>
                <div style='background:#0a0e1a;border-radius:999px;height:6px;width:100%;border:1px solid #1e2d4a;overflow:hidden;'>
                    <div style='height:100%;border-radius:999px;width:{barra_w}%;background:{fg_color};'></div>
                </div>
                <div style='display:flex;justify-content:space-between;font-family:Space Mono,monospace;font-size:0.6rem;color:#2a3a55;margin-top:3px;'>
                    <span>MIEDO</span><span>NEUTRO</span><span>CODICIA</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><div class="metric-label">FEAR &amp; GREED</div><div style="color:#2a3a55;font-size:0.75rem;">No disponible</div></div>', unsafe_allow_html=True)

    # ── Dólar ──
    with sec2:
        if dol_data.get("ok"):
            blue_v    = dol_data.get("blue",    {}).get("venta", "—")
            oficial_v = dol_data.get("oficial", {}).get("venta", "—")
            cripto_v  = dol_data.get("cripto",  {}).get("venta", "—")
            blue_c    = dol_data.get("blue",    {}).get("compra", "—")
            oficial_c = dol_data.get("oficial", {}).get("compra", "—")
            cripto_c  = dol_data.get("cripto",  {}).get("compra", "—")

            # Brecha blue vs oficial
            try:
                brecha = ((float(blue_v) - float(oficial_v)) / float(oficial_v)) * 100
                brecha_txt = f"+{brecha:.1f}% sobre oficial"
                brecha_color = "#ffb300"
            except Exception:
                brecha_txt = ""
                brecha_color = "#2a3a55"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">DÓLAR / PESO ARGENTINO</div>
                <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:0.5rem;'>
                    <div style='text-align:center;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>OFICIAL</div>
                        <div style='font-family:Space Mono,monospace;font-size:1rem;font-weight:700;color:#e0e6f0;'>${oficial_v}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a6080;'>c: ${oficial_c}</div>
                    </div>
                    <div style='text-align:center;border-left:1px solid #1e2d4a;border-right:1px solid #1e2d4a;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>BLUE</div>
                        <div style='font-family:Space Mono,monospace;font-size:1rem;font-weight:700;color:#ffb300;'>${blue_v}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a6080;'>c: ${blue_c}</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>CRIPTO</div>
                        <div style='font-family:Space Mono,monospace;font-size:1rem;font-weight:700;color:#00d4ff;'>${cripto_v}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a6080;'>c: ${cripto_c}</div>
                    </div>
                </div>
                <div style='font-family:Space Mono,monospace;font-size:0.62rem;color:{brecha_color};margin-top:0.5rem;text-align:center;'>
                    Blue {brecha_txt}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><div class="metric-label">DÓLAR / ARS</div><div style="color:#2a3a55;font-size:0.75rem;">No disponible</div></div>', unsafe_allow_html=True)

    # ── Economía Argentina ──
    with sec3:
        if eco_data.get("ok"):
            inf_m  = eco_data["mensual"]
            inf_ia = eco_data["interanual"]
            riesgo = eco_data["riesgo"]
            fecha_m  = eco_data["fecha_m"][:7]  if eco_data["fecha_m"]  else ""
            fecha_ia = eco_data["fecha_ia"][:7] if eco_data["fecha_ia"] else ""

            # Formateo seguro — puede venir "—" si el endpoint falló
            try:    inf_m_color  = "#ff4444" if float(inf_m)  > 5   else ("#ffb300" if float(inf_m)  > 3   else "#00e676")
            except: inf_m_color  = "#2a3a55"
            try:    inf_ia_color = "#ff4444" if float(inf_ia) > 100  else ("#ffb300" if float(inf_ia) > 50  else "#00e676")
            except: inf_ia_color = "#2a3a55"
            try:    riesgo_color = "#ff4444" if float(riesgo) > 1500 else ("#ffb300" if float(riesgo) > 800 else "#00e676")
            except: riesgo_color = "#2a3a55"

            try:    inf_m_txt  = f"{float(inf_m):.1f}%"
            except: inf_m_txt  = str(inf_m)
            try:    inf_ia_txt = f"{float(inf_ia):.1f}%"
            except: inf_ia_txt = str(inf_ia)
            try:    riesgo_txt = f"{int(float(riesgo)):,}"
            except: riesgo_txt = str(riesgo)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">ECONOMÍA ARGENTINA</div>
                <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:0.5rem;'>
                    <div style='text-align:center;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>INFLACIÓN MENSUAL</div>
                        <div style='font-family:Space Mono,monospace;font-size:1.1rem;font-weight:700;color:{inf_m_color};'>{inf_m_txt}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#2a3a55;'>{fecha_m}</div>
                    </div>
                    <div style='text-align:center;border-left:1px solid #1e2d4a;border-right:1px solid #1e2d4a;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>INFLACIÓN ANUAL</div>
                        <div style='font-family:Space Mono,monospace;font-size:1.1rem;font-weight:700;color:{inf_ia_color};'>{inf_ia_txt}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#2a3a55;'>{fecha_ia}</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a3a55;'>RIESGO PAÍS</div>
                        <div style='font-family:Space Mono,monospace;font-size:1.1rem;font-weight:700;color:{riesgo_color};'>{riesgo_txt}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#2a3a55;'>puntos</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><div class="metric-label">ECONOMÍA ARGENTINA</div><div style="color:#2a3a55;font-size:0.75rem;">No disponible</div></div>', unsafe_allow_html=True)


    # Sin datos disponibles — mostrar cards vacías sin mensajes de error
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-label">PRECIO ACTUAL</div><div class="metric-value" style="color:#2a3a55;">—</div><div style="font-family:Space Mono,monospace;font-size:0.75rem;color:#2a3a55;">cargando...</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-label">MÁXIMO 24H</div><div class="metric-value" style="color:#2a3a55;">—</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-label">MÍNIMO 24H</div><div class="metric-value" style="color:#2a3a55;">—</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><div class="metric-label">VOLUMEN 24H</div><div class="metric-value" style="color:#2a3a55;">—</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  AUTO-REFRESH
# ─────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
