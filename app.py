import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image, ImageDraw
import requests, json

# --- Config & AI ---
st.set_page_config(page_title="AstroPro SL Ultimate", page_icon="☸️", layout="wide")

# --- 100% Accurate Data Tables (Nakshatra 1-27) ---
# මෙම දත්ත ජ්‍යොතිෂ පොතේ ඇති පිළිවෙලටම සකසා ඇත.
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
GANA = ["දේව", "මනුෂ්‍ය", "රාක්ෂ", "මනුෂ්‍ය", "දේව", "මනුෂ්‍ය", "දේව", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව"]
YONI = ["අශ්ව", "ඇත්", "එළු", "සර්ප", "සර්ප", "බැල්ලි", "බළල්", "එළු", "බළල්", "මී මින්", "මී මින්", "ගව", "මී හරක්", "ව්‍යාඝ්‍ර", "මී හරක්", "ව්‍යාඝ්‍ර", "මුව", "මුව", "මුගටි", "වඳුරු", "වඳුරු", "සිංහ", "සිංහ", "අශ්ව", "සිංහ", "ගව", "ඇත්"]
LINGA = ["පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී"]
VRUKSHA = ["කදම්බ", "නෙල්ලි", "දිවුල්", "කරඹ", "කීරිය", "තිඹිරි", "උණ", "බෝගහ", "නුග", "පලු", "කෑල", "නුග", "වල් දෙල්", "බෙලි", "කුඹුක්", "මීඹ", "දම්", "වැටකේ", "සල්", "පුවක්", "පිහිඹියා", "වෙලං", "ලූණුමකරල", "කලවැල්", "කොහොඹ", "මී", "වැටකේ"]
PAKSHI = ["හොට කිරලා", "කපුටා", "කපුටා", "පින්නකිකිළි", "පින්නකිකිළි", "පින්නකිකිළි", "මොණරා", "මොණරා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "මොණරා", "මොණරා", "මොණරා", "මොණරා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "මොණරා", "මොණරා", "මොණරා"]
D_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
D_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
DISTRICTS = {"කොළඹ":(6.9271,79.8612),"මහනුවර":(7.2906,80.6337),"කෑගල්ල":(7.2513,80.3464)} # අනෙක් 25ම පෙර පරිදිම එක් කරන්න

with st.sidebar:
    st.header("👤 විස්තර")
    name = st.text_input("නම")
    dob = st.date_input("දිනය", value=date(2019, 8, 18), min_value=date(1900,1,1), max_value=date(2100,12,31))
    c = st.columns(3); h = c[0].number_input("පැය",0,23,6); m = c[1].number_input("විනා",0,59,41); s = c[2].number_input("තත්",0,59,0)
    city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    lat, lon = DISTRICTS[city]
    jd = swe.julday(dob.year, dob.month, dob.day, h + m/60.0 + s/3600.0 - 5.5)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # ලග්නය
    _, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL); lag_idx = int(ascmc[0]/30)
    
    # චන්ද්‍රයාගේ පිහිටීම (නැකත සඳහා)
    res, _ = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL); moon_lon = res[0]
    
    # නැකත් අංකය (0-26)
    n_idx = int(moon_lon / (360/27))
    n_idx = max(0, min(n_idx, 26))
    
    # මහා දශාව (Balance)
    d_idx = n_idx % 9
    passed = moon_lon - (n_idx * (360/27))
    bal = (1 - (passed / (360/27))) * D_YEARS[d_idx]
    
    st.header(f"📊 {name} මහතාගේ වාර්තාව")
    col1, col2 = st.columns([1,1])
    with col1:
        # Chart Drawing (Simplified but clear)
        img = Image.new('RGB',(600,600),(255,255,255)); draw = ImageDraw.Draw(img)
        for i in range(5): draw.line([(i*150,0),(i*150,600)],"black",2); draw.line([(0,i*150),(600,i*150)],"black",2)
        st.image(img, caption="කේන්ද්‍ර සටහන")
        
    with col2:
        st.subheader("📝 පංචාංග තොරතුරු")
        st.write(f"**ලග්නය:** {RA_NAMES[lag_idx]} | **නැකත:** {NAK_NAMES[n_idx]}")
        st.write(f"**ගණය:** {GANA[n_idx]} | **යෝනිය:** {YONI[n_idx]} | **ලිංගය:** {LINGA[n_idx]}")
        st.write(f"**වෘක්ෂය:** {VRUKSHA[n_idx]} | **පක්ෂියා:** {PAKSHI[n_idx]}")
        
        st.subheader("🗓️ මහා දශාව")
        st.success(f"උපතේදී හිමි දශාව: {D_LORDS[d_idx]}")
        st.write(f"ඉතිරි කාලය: වසර {int(bal)} මාස {int((bal%1)*12)}")
