import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Pro Terminal v30", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    div[data-testid="metric-container"] { padding: 8px; border-radius: 12px; background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 2. MEGA VERİ KÜTÜPHANESİ ---
market_data = {
    "🏢 BIST": {"THY": "THYAO.IS", "Tüpraş": "TUPRS.IS", "Aselsan": "ASELS.IS", "Koç": "KCHOL.IS", "SASA": "SASA.IS", "Ereğli": "EREGL.IS", "Şişecam": "SISE.IS"},
    "🗽 ABD": {"Apple": "AAPL", "Tesla": "TSLA", "Nvidia": "NVDA", "Amazon": "AMZN", "Microsoft": "MSFT", "Google": "GOOGL"},
    "🪙 Kripto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Avax": "AVAX-USD", "Ripple": "XRP-USD", "Link": "LINK-USD"},
    "💱 Döviz & Emtia": {"Dolar/TL": "USDTRY=X", "Euro/TL": "EURTRY=X", "Ons Altın": "GC=F", "Gümüş": "SI=F", "Gram Altın": "GC=F", "Euro/Dolar": "EURUSD=X"}
}
all_symbols = {k: v for kat in market_data.values() for k, v in kat.items()}

# --- 3. HAFIZA ---
if "kisisel_liste" not in st.session_state: 
    st.session_state.kisisel_liste = {"Bitcoin": "BTC-USD", "THY": "THYAO.IS", "Dolar/TL": "USDTRY=X", "Gram Altın": "GC=F"}
if "c_df" not in st.session_state: 
    st.session_state.c_df = pd.DataFrame(columns=["Varlık","Maliyet","Adet"])
if "incelenecek" not in st.session_state: st.session_state.incelenecek = "Bitcoin"
if "arac_db" not in st.session_state: st.session_state.arac_db = pd.DataFrame(columns=["Tarih","Araç","Fiyat","Link"])

# --- 4. VERİ MOTORU ---
@st.cache_data(ttl=60)
def veri_motoru(sembol, isim="", p="1y", i="1d"):
    try:
        if isim == "Gram Altın":
            o = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
            k = yf.Ticker("USDTRY=X").history(period="1d")['Close'].iloc[-1]
            return (o / 31.1035) * k, 0.5, yf.Ticker("GC=F").history(period=p)
        
        v = yf.Ticker(sembol)
        g = v.history(period=p, interval=i)
        if g.empty: return 0.0, 0.0, None
        son = g['Close'].iloc[-1]
        yuzde = ((son - g['Close'].iloc[-2]) / g['Close'].iloc[-2]) * 100 if len(g) > 1 else 0.0
        return son, yuzde, g
    except: return 0.0, 0.0, None

# --- 5. KENAR ÇUBUĞU ---
with st.sidebar:
    st.title("🛡️ Terminal v30")
    sayfa = st.radio("Bölüm Seçin:", ["📌 Ana Sayfam", "💰 Toplam Servetim", "📈 Teknik Analiz", "⚖️ Yatırım Kıyaslama", "💱 Çapraz Kur", "🚗 Araç & İlan Radarı", "📥 Varlık Pazarı", "💼 Cüzdanım", "📰 Haberler"])
    st.divider()
    st.subheader("🤖 Finans Asistanı")
    if "chat" not in st.session_state: st.session_state.chat = [{"r":"assistant", "i":"Analize hazırım."}]
    with st.container(height=150):
        for m in st.session_state.chat: st.chat_message(m["r"]).write(m["i"])
    if p := st.chat_input("Sor..."):
        st.session_state.chat.append({"r":"user", "i":p}); st.rerun()

# --- 6. SAYFALAR ---

if sayfa == "📌 Ana Sayfam":
    st.header("📌 Portföy İzleme")
    secili = st.multiselect("Listeyi Düzenle:", list(all_symbols.keys()), default=list(st.session_state.kisisel_liste.keys()))
    st.session_state.kisisel_liste = {k: all_symbols[k] for k in secili}
    cols = st.columns(5)
    for index, (isim, sem) in enumerate(st.session_state.kisisel_liste.items()):
        f, y, _ = veri_motoru(sem, isim)
        with cols[index % 5]:
            with st.container(border=True):
                st.metric(isim, f"{f:,.2f}", f"%{y:.2f}")
                if st.button("🔍", key=f"main_go_{isim}_{index}"): st.session_state.incelenecek = isim; st.toast(f"{isim} seçildi!")

elif sayfa == "📈 Teknik Analiz":
    st.header(f"📈 {st.session_state.incelenecek} - Profesyonel Analiz")
    a1, a2, a3 = st.columns(3)
    v_sec = a1.selectbox("Varlık:", list(all_symbols.keys()), index=list(all_symbols.keys()).index(st.session_state.incelenecek))
    st.session_state.incelenecek = v_sec
    per = a2.selectbox("Periyot:", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=5)
    intv = a3.selectbox("Aralık:", ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"], index=8)
    
    f, y, g = veri_motoru(all_symbols[v_sec], v_sec, p=per, i=intv)
    if g is not None and not g.empty:
        fig = go.Figure(data=[go.Candlestick(x=g.index, open=g['Open'], high=g['High'], low=g['Low'], close=g['Close'])])
        fig.update_layout(title=f"{v_sec} Mum Grafiği", xaxis_rangeslider_visible=False, height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Bu zaman diliminde veri bulunamadı. Lütfen Aralığı (örneğin 1d) artırmayı deneyin.")

elif sayfa == "📥 Varlık Pazarı":
    st.header("📥 Varlık Pazarı")
    for kat_index, (kat, vlar) in enumerate(market_data.items()):
        with st.expander(kat):
            for v_index, (vi, vs) in enumerate(vlar.items()):
                # HATA ÇÖZÜMÜ: Key'e hem kategori hem de varlık indexini ekledik, çakışma imkansız.
                if st.button(f"Ekle: {vi}", key=f"btn_pazar_{kat_index}_{v_index}_{vs}"):
                    st.session_state.kisisel_liste[vi] = vs
                    st.success(f"{vi} başarıyla eklendi!")

elif sayfa == "💰 Toplam Servetim":
    st.header("💰 Servet Özeti")
    tv, tk = 0.0, 0.0
    u_t, _, _ = veri_motoru("USDTRY=X")
    for _, r in st.session_state.c_df.iterrows():
        sem = all_symbols.get(r["Varlık"])
        if sem:
            f, _, _ = veri_motoru(sem, r["Varlık"])
            val = f * r["Adet"]
            if ".IS" not in str(sem) and "TRY" not in str(sem): val *= u_t
            tv += val
            tk += (f - r["Maliyet"]) * r["Adet"] * (u_t if (".IS" not in str(sem) and "TRY" not in str(sem)) else 1)
    st.metric("Toplam Servet (TL)", f"{tv:,.2f} ₺", f"Kâr/Zarar: {tk:,.2f} ₺")

elif sayfa == "💱 Çapraz Kur":
    st.header("💱 Çapraz Kur")
    ca1, ca2, ca3 = st.columns(3)
    k_v = ca1.selectbox("Eldeki:", ["Gram Altın", "Bitcoin", "Dolar", "Euro"])
    mik = ca2.number_input("Miktar:", value=1.0)
    h_b = ca3.selectbox("Hedef:", ["TL (₺)", "Dolar ($)", "Euro (€)"])
    if st.button("Hesapla"):
        u_t, _, _ = veri_motoru("USDTRY=X"); e_u, _, _ = veri_motoru("EURUSD=X")
        if k_v == "Gram Altın": f, _, _ = veri_motoru("GC=F"); f = f/31.10
        elif k_v == "Bitcoin": f, _, _ = veri_motoru("BTC-USD")
        elif k_v == "Euro": f = e_u
        else: f = 1.0
        t_usd = f * mik
        res = t_usd * u_t if h_b == "TL (₺)" else (t_usd if h_b == "Dolar ($)" else t_usd / e_u)
        st.success(f"Sonuç: {res:,.2f} {h_b}")

elif sayfa == "⚖️ Yatırım Kıyaslama":
    st.header("⚖️ Kıyaslama")
    k1, k2 = st.columns(2)
    v1 = k1.selectbox("1. Varlık", list(all_symbols.keys()))
    v2 = k2.selectbox("2. Varlık", list(all_symbols.keys()))
    if st.button("Kıyasla"):
        _, _, g1 = veri_motoru(all_symbols[v1]); _, _, g2 = veri_motoru(all_symbols[v2])
        r1 = g1['Close'].iloc[-1]/g1['Close'].iloc[0]; r2 = g2['Close'].iloc[-1]/g2['Close'].iloc[0]
        st.write(f"**{v1}**: {r1:.2f} Kat | **{v2}**: {r2:.2f} Kat")

elif sayfa == "🚗 Araç & İlan Radarı":
    st.header("🚗 Araç Takibi")
    with st.container(border=True):
        co1, co2, co3 = st.columns(3)
        m = co1.text_input("Model"); f = co2.number_input("Fiyat (₺)", value=0); l = co3.text_input("Link")
        if st.button("Kaydet"):
            st.session_state.arac_db = pd.concat([st.session_state.arac_db, pd.DataFrame([{"Tarih":datetime.now().strftime("%d/%m/%Y"),"Araç":m,"Fiyat":f,"Link":l}])])
    for _, r in st.session_state.arac_db.iterrows():
        st.write(f"🚗 {r['Araç']} - {r['Fiyat']:,.0f} ₺ | [İlan]({r['Link']})")

elif sayfa == "💼 Cüzdanım":
    st.header("💼 Cüzdan")
    c_sec1, c_sec2 = st.columns([2,1])
    yeni_v = c_sec1.selectbox("Eklenecek Varlık:", ["---"] + list(all_symbols.keys()))
    if c_sec2.button("➕ Ekle") and yeni_v != "---":
        st.session_state.c_df = pd.concat([st.session_state.c_df, pd.DataFrame([{"Varlık": yeni_v, "Maliyet": 0.0, "Adet": 0.0}])], ignore_index=True)
    st.session_state.c_df = st.data_editor(st.session_state.c_df, num_rows="dynamic", use_container_width=True)

elif sayfa == "📰 Haberler":
    st.header("📰 Haberler")
    h_v = st.selectbox("Kaynak:", list(all_symbols.keys()))
    for n in yf.Ticker(all_symbols[h_v]).news[:5]:
        st.write(f"**{n.get('title')}** - [Oku]({n.get('link')})")