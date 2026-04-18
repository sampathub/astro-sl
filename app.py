import streamlit as st
import swisseph as swe
from datetime import datetime
from fpdf import FPDF
import io

# --- Mobile Optimized Configuration ---
st.set_page_config(page_title="AstroPro SL", page_icon="☸️", layout="centered")

st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { max-width: 800px; margin: auto; }
        .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 25 Districts Data ---
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

# --- PDF Generation Function ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Astrological Report - AstroPro SL", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    return pdf.output(dest='S')

# --- Existing Calculation Logic (Unchanged) ---
def get_planet_bhava(planet_lon, cusps):
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            if start <= planet_lon < end: return i + 1
        else:
            if planet_lon >= start or planet_lon < end: return i + 1
    return 1

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    u_name = st.text_input("නම")
    u_dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20))
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

# --- Main Logic ---
if st.button("කේන්දරය බලන්න"):
    if not u_name: st.warning("නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, (u_h + u_m/60) - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            
            planets_def = {"Ravi":0, "Sanda":1, "Kuja":4, "Budha":2, "Guru":5, "Sikuru":3, "Shani":6, "Rahu":10}
            bhava_map = {i: [] for i in range(1, 13)}
            
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                p_bhava = get_planet_bhava(res[0], houses)
                bhava_map[p_bhava].append(p_name)
            
            st.success(f"{u_name} - ජන්ම පත්‍ර දත්ත")
            
            # Display
            report_data = {"Name": u_name, "Lagna": "Computed", "Planets": str(bhava_map)}
            st.session_state['report'] = report_data
            
            for b in range(1, 13):
                if bhava_map[b]:
                    st.write(f"**{b} වන භාවය:** {', '.join(bhava_map[b])}")

        except Exception as e:
            st.error(f"Error: {e}")

# --- PDF Download Section ---
if 'report' in st.session_state:
    pdf_bytes = create_pdf(st.session_state['report'])
    st.download_button(
        label="📥 PDF වාර්තාව බාගත කරන්න",
        data=pdf_bytes,
        file_name="Astrology_Report.pdf",
        mime="application/pdf"
    )
