import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta

# App Settings
st.set_page_config(page_title="Heladiwa Astro Pro v2", page_icon="☸️", layout="wide")

st.title("☸️ Heladiwa Astro Pro - Advanced Edition")
st.markdown("### මහා දශා සහ අතුරු දශා නිරවද්‍ය ගණනය කිරීම්")

# --- දත්ත සැකසුම් ---
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

RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", 
             "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", 
             "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- Inputs ---
with st.sidebar:
    st.header("⚙️ උපන් තොරතුරු")
    dob = st.date_input("උපන් දිනය", datetime(1995, 5, 20))
    t_col1, t_col2, t_col3 = st.columns(3)
    h = t_col1.number_input("පැය", 0, 23, 10)
    m = t_col2.number_input("විනාඩි", 0, 59, 30)
    s = t_col3.number_input("තත්", 0, 59, 0)
    city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

def get_dasha_details(birth_dt, moon_lon):
    # 1 නැකතක දිග අංශක 13.3333
    nak_length = 360 / 27
    nak_idx = int(moon_lon / nak_length)
    
    # දශා ආරම්භක ග්‍රහයා (කේතුගෙන් පටන් ගෙන)
    lord_idx = nak_idx % 9
    
    # නැකත තුල ගෙවුනු ප්‍රමාණය
    elapsed_in_nak = moon_lon % nak_length
    remaining_ratio = 1 - (elapsed_in_nak / nak_length)
    
    # උපතේදී ඉතිරි දශා කාලය
    first_dasha_years = DASHA_YEARS[lord_idx] * remaining_ratio
    
    dasha_timeline = []
    current_start_date = birth_dt
    
    # පළමු දශාව (Balance)
    end_date = current_start_date + timedelta(days=first_dasha_years * 365.2425)
    dasha_timeline.append({
        "මහා දශාව": DASHA_LORDS[lord_idx],
        "ආරම්භය": current_start_date.strftime('%Y-%m-%d'),
        "අවසානය": end_date.strftime('%Y-%m-%d'),
        "කාලය": f"වසර {first_dasha_years:.2f}"
    })
    
    # ඉදිරි දශා 9 ම ගණනය කිරීම
    current_start_date = end_date
    for i in range(1, 10):
        idx = (lord_idx + i) % 9
        years = DASHA_YEARS[idx]
        end_date = current_start_date + timedelta(days=years * 365.2425)
        dasha_timeline.append({
            "මහා දශාව": DASHA_LORDS[idx],
            "ආරම්භය": current_start_date.strftime('%Y-%m-%d'),
            "අවසානය": end_date.strftime('%Y-%m-%d'),
            "කාලය": f"වසර {years}"
        })
        current_start_date = end_date
        
    return dasha_timeline, lord_idx

if st.button("කේන්ද්‍රය සහ සම්පූර්ණ දශා විස්තර පෙන්වන්න"):
    try:
        lat, lon = DISTRICTS[city]
        birth_dt = datetime.combine(dob, datetime.min.time().replace(hour=h, minute=m, second=s))
        
        # Julian Day (UTC+5.5 -> UTC conversion)
        decimal_hour = h + m/60.0 + s/3600.0 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # ගණනය කිරීම්
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        moon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        m_lon = moon[0]
        
        # Results Display
        st.success("ගණනය කිරීම් සාර්ථකයි!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("ලග්නය", RA_NAMES[int(ascmc[0] / 30)])
        c2.metric("නැකත", NAK_NAMES[int(m_lon / (360/27))])
        c3.metric("චන්ද්‍ර ස්ඵුටය", f"{m_lon:.2f}°")

        # දශා වගුව
        timeline, current_idx = get_dasha_details(birth_dt, m_lon)
        
        st.subheader("🗓️ සම්පූර්ණ මහා දශා කාලසටහන")
        st.table(timeline)

        # අතුරු දශා ගණනය (දැනට පවතින මහා දශාව සඳහා)
        st.subheader(f"🔍 {timeline[0]['මහා දශාව']} මහා දශාව තුල අතුරු දශා (Bhukti)")
        
        main_lord_years = DASHA_YEARS[current_idx]
        bhukti_list = []
        # අතුරු දශා පටන් ගන්නේ මහා දශා අධිපතිගෙන්මයි
        for j in range(9):
            b_idx = (current_idx + j) % 9
            b_years = DASHA_YEARS[b_idx]
            # අතුරු දශා කාලය = (මහා දශා වසර * අතුරු දශා හිමි ග්‍රහයාගේ වසර) / 120
            bhukti_months = (main_lord_years * b_years) / 120 * 12
            bhukti_list.append({"අතුරු දශා අධිපති": DASHA_LORDS[b_idx], "කාලය (මාස)": round(bhukti_months, 2)})
            
        st.dataframe(bhukti_list, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
