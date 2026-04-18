import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai

# --- Mobile Optimized Configuration ---
st.set_page_config(page_title="AstroPro SL", page_icon="☸️", layout="centered")

st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { max-width: 800px; margin: auto; }
        .stButton>button { width: 100%; border-radius: 5px; background-color: #4CAF50; color: white; }
        .stButton>button:hover { background-color: #45a049; }
        img { width: 100%; height: auto; }
        .report-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- Helper: Planet to Bhava Calculation ---
def get_planet_bhava(planet_lon, cusps):
    """Determine bhava (1-12) based on planet's longitude"""
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            if start <= planet_lon < end:
                return i + 1
        else:  # Wraparound 360
            if planet_lon >= start or planet_lon < end:
                return i + 1
    return 1

# --- AI Prediction using Gemini ---
def get_ai_prediction(summary_data):
    # Try both possible secret keys (add your keys in Streamlit secrets)
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2")]
    prompt = f"""
    ඔබ ප්‍රවීණ ශ්‍රී ලාංකීය ජ්‍යොතිෂවේදියෙකි. පහත දත්ත මත පදනම්ව චරිතය, අධ්‍යාපනය, රැකියාව, සෞඛ්‍යය සහ විවාහය ගැන සවිස්තරාත්මක පලාපල විස්තරයක් සිංහලෙන් ලියන්න.
    දත්ත: {summary_data}
    """
    for key in keys:
        if not key:
            continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    return "කණගාටුයි, AI සේවාව තාවකාලිකව කාර්යබහුලයි. කරුණාකර පසුව නැවත උත්සාහ කරන්න."

# --- Data ---
# Districts with coordinates (latitude, longitude)
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කිලිනොච්චිය": (9.3854, 80.3921), "මන්නාරම": (8.9810, 79.9044),
    "වවුනියාව": (8.7542, 80.4982), "මුලතිව්": (9.2671, 80.8143), "මඩකලපුව": (7.7102, 81.6924),
    "අම්පාර": (7.2843, 81.6747), "ත්‍රිකුණාමලය": (8.5711, 81.2335), "කුරුණෑගල": (7.4863, 80.3647),
    "පුත්තලම": (8.0330, 79.8257), "අනුරාධපුරය": (8.3114, 80.4037), "පොළොන්නරුව": (7.9403, 81.0188),
    "බදුල්ල": (6.9934, 81.0550), "මොණරාගල": (6.8719, 81.3512), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

# --- UI Sidebar ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    u_name = st.text_input("නම", placeholder="ඔබගේ නම ඇතුළත් කරන්න")
    
    # Date input with year validation (1940 to 2050)
    u_dob = st.date_input(
        "උපන් දිනය",
        value=datetime(1995, 5, 20),
        min_value=datetime(1940, 1, 1),
        max_value=datetime(2050, 12, 31)
    )
    
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය (0-23)", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු (0-59)", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    
    st.markdown("---")
    st.caption("📅 1940 සිට 2050 දක්වා උපන් අය සඳහා සහාය දක්වයි")

# --- Main Calculation Button ---
if st.button("🔮 කේන්දරය බලන්න"):
    if not u_name.strip():
        st.warning("කරුණාකර නම ඇතුළත් කරන්න.")
    elif u_dob.year < 1940 or u_dob.year > 2050:
        st.error("සමාවන්න, මෙම වැඩසටහන 1940 සිට 2050 දක්වා උපන් අය සඳහා පමණයි.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            # Convert local time (Sri Lanka +5:30) to UTC Julian Day
            hour_utc = u_h + u_m/60 - 5.5
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, hour_utc)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Calculate houses and ascendant
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            
            # Lagna Rashi
            lagna_rashi = int(ascmc[0] / 30)
            lagna_name = RA_NAMES[lagna_rashi]
            
            # Planet positions: (name, swisseph ID)
            planets_def = [
                ("රවි", swe.SUN), ("සඳු", swe.MOON), ("කුජ", swe.MARS),
                ("බුධ", swe.MERCURY), ("ගුරු", swe.JUPITER), ("සිකුරු", swe.VENUS),
                ("ශනි", swe.SATURN), ("රාහු", swe.MEAN_NODE)
            ]
            
            # Dictionary to store planets per bhava
            bhava_map = {i: [] for i in range(1, 13)}
            moon_lon = 0
            
            for p_name, p_id in planets_def:
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                lon = res[0]
                if p_id == swe.MOON:
                    moon_lon = lon
                p_bhava = get_planet_bhava(lon, houses)
                bhava_map[p_bhava].append(p_name)
            
            # Nakshatra calculation
            nak_idx = int(moon_lon / (360.0 / 27)) % 27
            nak_name = NAK_NAMES[nak_idx]
            
            # Store data for AI prediction
            st.session_state['astro_data'] = {
                "name": u_name,
                "lagna": lagna_name,
                "nakshathra": nak_name,
                "bhava_data": str(bhava_map),
                "dob": u_dob.strftime("%Y-%m-%d"),
                "city": u_city
            }
            
            # --- Display Results ---
            st.success(f"✨ {u_name} මහතාගේ/මියගේ ජන්ම පත්‍රය ✨")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='report-box'><b>⭐ ලග්නය:</b> {lagna_name}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='report-box'><b>🌙 නැකත:</b> {nak_name}</div>", unsafe_allow_html=True)
            
            st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
            
            # Display bhava table in columns for better mobile view
            col_a, col_b = st.columns(2)
            bhava_items = list(bhava_map.items())
            mid = len(bhava_items) // 2
            
            with col_a:
                for bhava, planets in bhava_items[:mid]:
                    if planets:
                        st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                    else:
                        st.markdown(f"**{bhava} වන භාවය:** -")
            
            with col_b:
                for bhava, planets in bhava_items[mid:]:
                    if planets:
                        st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                    else:
                        st.markdown(f"**{bhava} වන භාවය:** -")
            
            st.info("📌 වැඩිදුර විස්තර සඳහා පහත බොත්තම ඔබන්න.")
            
        except Exception as e:
            st.error(f"දෝෂයක් ඇති විය: {e}")
            st.info("කරුණාකර නැවත උත්සාහ කරන්න හෝ අනෙක් දිනයක්/වේලාවක් ඇතුළත් කරන්න.")

# --- AI Prediction Section ---
if 'astro_data' in st.session_state:
    st.markdown("---")
    if st.button("🔮 පලාපල විස්තරය ලබාගන්න", key="ai_btn"):
        with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
            ai_response = get_ai_prediction(st.session_state['astro_data'])
            st.markdown("### 📜 පලාපල වාර්තාව")
            st.markdown(f"<div class='report-box'>{ai_response}</div>", unsafe_allow_html=True)
    
    # Optional: Add a footer note
    st.caption("© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය")
