import streamlit as st
import swisseph as swe
from datetime import datetime, time

# App එකේ මූලික පෙනුම සැකසීම
st.set_page_config(page_title="AstroPro Sri Lanka", page_icon="☀️", layout="centered")

# CSS මගින් පෙනුම තවත් ලස්සන කිරීම
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("☀️ AstroPro ශ්‍රී ලංකා")
st.subheader("Swiss Ephemeris තාක්ෂණයෙන් ක්‍රියාත්මක වන නිවැරදිම ජ්‍යොතිෂ්‍ය පද්ධතිය")

# දත්ත ඇතුළත් කිරීමේ කොටස
with st.expander("උපන් විස්තර ඇතුළත් කරන්න", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("උපන් දිනය", datetime(1995, 5, 20))
    with col2:
        birth_time = st.time_input("උපන් වේලාව", time(10, 30))

    # ලංකාවේ ප්‍රධාන නගරවල දත්ත (Latitude, Longitude)
    locations = {
        "කොළඹ": (6.9271, 79.8612),
        "මහනුවර": (7.2906, 80.6337),
        "ගාල්ල": (6.0535, 80.2210),
        "අනුරාධපුරය": (8.3114, 80.4037),
        "යාපනය": (9.6615, 80.0255),
        "කුරුණෑගල": (7.4863, 80.3647)
    }
    city = st.selectbox("උපන් නගරය (සන්නිකර්ෂණ පිහිටීම සඳහා)", list(locations.keys()))

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    try:
        lat, lon = locations[city]
        
        # ලංකාවේ වේලාව (GMT+5.5) UTC බවට පත් කිරීම
        decimal_hour = birth_time.hour + birth_time.minute/60.0 - 5.5
        
        # Julian Day ගණනය කිරීම
        jd = swe.julday(date.year, date.month, date.day, decimal_hour)
        
        # නිරයන ක්‍රමය සහ ලාහිරි අයනාංශය (Lahiri Ayanamsa) සැකසීම
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # ලග්නය ගණනය කිරීම (Ascendant)
        # b'P' යනු Placidus house system එකයි
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        rashi_names = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
        lagna_idx = int(ascmc[0] / 30)
        lagna = rashi_names[lagna_idx]

        # සඳුගේ පිහිටීම සහ නැකත ගණනය කිරීම
        moon, ret = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        moon_lon = moon[0]
        
        nak_names = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", 
                     "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", 
                     "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
        
        nak_index = int(moon_lon / (360/27))
        nak_name = nak_names[nak_index]

        # ප්‍රතිඵල පෙන්වීම
        st.divider()
        st.success(f"ගණනය කිරීම සාර්ථකයි!")
        
        res1, res2 = st.columns(2)
        res1.metric("ලග්නය", lagna)
        res2.metric("නැකත", nak_name)
        
        # ග්‍රහ ස්ඵුට වගුව
        st.write("### ග්‍රහ ස්ඵුටයන් (Planetary Degrees):")
        planets = {
            "රවි (Sun)": swe.SUN,
            "චන්ද්‍ර (Moon)": swe.MOON,
            "කුජ (Mars)": swe.MARS,
            "බුධ (Mercury)": swe.MERCURY,
            "ගුරු (Jupiter)": swe.JUPITER,
            "සිකුරු (Venus)": swe.VENUS,
            "ශනි (Saturn)": swe.SATURN,
            "රාහු (Rahu)": swe.MEAN_NODE
        }
        
        planet_data = []
        for name, id in planets.items():
            res, ret = swe.calc_ut(jd, id, swe.FLG_SIDEREAL)
            deg = res[0]
            r_idx = int(deg / 30)
            planet_data.append({"ග්‍රහයා": name, "රාශිය": rashi_names[r_idx], "ස්ඵුටය": round(deg % 30, 4)})
        
        st.table(planet_data)

    except Exception as e:
        st.error(f"දෝෂයක් සිදු විය: {e}")

st.caption("AstroPro SL v1.0 | Powered by Swiss Ephemeris")
