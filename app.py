import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image, ImageDraw

# --- 1. මූලික සැකසුම් (Configuration) ---
st.set_page_config(page_title="AstroPro Ultimate v21", page_icon="☸️", layout="wide")

# --- 2. AI පලාපල සේවාව ---
def get_ai_prediction(data):
    for i in range(1, 4):
        key = st.secrets.get(f"GEMINI_API_KEY_{i}")
        if key:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(f"ඔබ ප්‍රවීණ සිංහල ජ්‍යොතිෂවේදියෙකි. මෙම දත්ත මත පදනම්ව දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් කරන්න: {data}").text
            except: continue
    return "AI සේවාව දැනට කාර්යබහුලයි."

# --- 3. සියලුම දත්ත වගු (Fixed & Full) ---
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
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
GANA = ["දේව","මනුෂ්‍ය","රාක්ෂ","මනුෂ්‍ය","දේව","මනුෂ්‍ය","දේව","දේව","රාක්ෂ","රාක්ෂ","මනුෂ්‍ය","මනුෂ්‍ය","දේව","රාක්ෂ","දේව","රාක්ෂ","දේව","රාක්ෂ","රාක්ෂ","මනුෂ්‍ය","මනුෂ්‍ය","දේව","රාක්ෂ","රාක්ෂ","මනුෂ්‍ය","මනුෂ්‍ය","දේව"]
YONI = ["අශ්ව","ඇත්","එළු","සර්ප","සර්ප","බැල්ලි","බළල්","එළු","බළල්","මී මින්","මී මින්","ගව","මී හරක්","ව්‍යාඝ්‍ර","මී හරක්","ව්‍යාඝ්‍ර","මුව","මුව","මුගටි","වඳුරු","වඳුරු","සිංහ","සිංහ","අශ්ව","සිංහ","ගව","ඇත්"]
LINGA = ["පුරුෂ","පුරුෂ","ස්ත්‍රී","ස්ත්‍රී","ස්ත්‍රී","ස්ත්‍රී","පුරුෂ","පුරුෂ","ස්ත්‍රී","පුරුෂ","ස්ත්‍රී","පුරුෂ","ස්ත්‍රී","ස්ත්‍රී","පුරුෂ","පුරුෂ","ස්ත්‍රී","පුරුෂ","පුරුෂ","පුරුෂ","ස්ත්‍රී","පුරුෂ","පුරුෂ","ස්ත්‍රී","පුරුෂ","පුරුෂ","ස්ත්‍රී"]
VRUKSHA = ["කදම්බ","නෙල්ලි","දිවුල්","කරඹ","කීරිය","තිඹිරි","උණ","බෝගහ","නුග","පලු","කෑල","නුග","වල් දෙල්","බෙලි","කුඹුක්","මීඹ","දම්","වැටකේ","සල්","පුවක්","පිහිඹියා","වෙලං","ලූණුමකරල","කලවැල්","කොහොඹ","මී","වැටකේ"]
PAKSHI = ["කිරලා","කපුටා","කපුටා","කිරලා","කිරලා","කිරලා","මොණරා","මොණරා","කුකුළා","කුකුළා","කුකුළා","කුකුළා","කුකුළා","කුකුළා","මොණරා","මොණරා","මොණරා","මොණරා","බකමූණා","බකමූණා","බකමූණා","බකමූණා","බකමූණා","මොණරා","මොණරා","මොණරා","මොණරා"]
D_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
D_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- 4. කේන්ද්‍ර සටහන ඇඳීමේ ශ්‍රිතය ---
def draw_horoscope(pos_map, lagna_idx, title):
    img = Image.new('RGB', (600, 600), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        draw.line([(i*150, 0), (i*150, 600)], "black", 2)
        draw.line([(0, i*150), (600, i*150)], "black", 2)
    grid = {11:(0,0), 0:(150,0), 1:(300,0), 2:(450,0), 10:(0,150), 3:(450,150), 9:(0,300), 4:(450,300), 8:(0,450), 7:(150,450), 6:(300,450), 5:(450,450)}
    for r, (x, y) in grid.items():
        if r == lagna_idx: draw.text((x+65, y+10), "L", (255, 0, 0))
        planets = pos_map.get(r, [])
        for i, p in enumerate(planets):
            p_short = {"රවි":"Sun","සඳු":"Moon","කුජ":"Mars","බුධ":"Merc","ගුරු":"Jup","සිකුරු":"Ven","ශනි":"Sat","රාහු":"Rahu"}.get(p,p)
            draw.text((x+25, y+40+(i*22)), p_short, "black")
    return img

# --- 5. ප්‍රධාන යෙදුම (Main UI) ---
with st.sidebar:
    st.header("👤 උපන් තොරතුරු")
    u_name = st.text_input("නම")
    u_dob = st.date_input("උපන් දිනය", value=date(2019, 8, 18))
    c = st.columns(3)
    u_h = c[0].number_input("පැය", 0, 23, 6)
    u_m = c[1].number_input("විනා", 0, 59, 41)
    u_s = c[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

st.title("☸️ AstroPro Sri Lanka Ultimate v21")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if u_name:
        lat, lon = DISTRICTS[u_city]
        decimal_hour = u_h + u_m/60.0 + u_s/3600.0 - 5.5
        jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # --- භාව සහ ලග්න ගණනය ---
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        lag_idx = int(ascmc[0]/30)
        
        # --- ග්‍රහ පිහිටීම් (රාශි සහ භාව) ---
        planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
        rashi_map = {i: [] for i in range(12)}
        bhava_map = {i: [] for i in range(12)}
        moon_lon = 0
        
        for name, pid in planets_def.items():
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            p_lon = res[0]
            if pid == 1: moon_lon = p_lon
            
            # රාශි සිතියම සඳහා
            rashi_map[int(p_lon/30)].append(name)
            
            # භාව සිතියම සඳහා (Placidus Houses)
            for i in range(12):
                h_start = houses[i]
                h_end = houses[(i+1)%12]
                if (h_start < h_end and h_start <= p_lon < h_end) or (h_start > h_end and (p_lon >= h_start or p_lon < h_end)):
                    bhava_map[i].append(name)
                    break
        
        # --- පංචාංගය ---
        n_idx = min(int(moon_lon / (360/27)), 26)
        d_idx = n_idx % 9
        bal = (1 - ((moon_lon - (n_idx*(360/27))) / (360/27))) * D_YEARS[d_idx]
        
        # --- ප්‍රතිඵල පෙන්වීම ---
        st.header(f"📊 {u_name} මහතාගේ ජන්ම පත්‍රය")
        tab1, tab2 = st.tabs(["☸️ කේන්ද්‍ර සටහන්", "📝 පංචාංගය සහ දශාව"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("රාශි කේන්ද්‍රය")
                st.image(draw_horoscope(rashi_map, lag_idx, "Rashi Chart"))
            with col2:
                st.subheader("භාව කේන්ද්‍රය (Bhava Chalit)")
                st.image(draw_horoscope(bhava_map, lag_idx, "Bhava Chart"))
        
        with tab2:
            c1, c2, c3 = st.columns(3)
            c1.metric("නැකත", NAK_NAMES[n_idx])
            c1.metric("ගණය", GANA[n_idx])
            c2.metric("යෝනිය", YONI[n_idx])
            c2.metric("ලිංගය", LINGA[n_idx])
            c3.metric("වෘක්ෂය", VRUKSHA[n_idx])
            c3.metric("පක්ෂියා", PAKSHI[n_idx])
            
            st.info(f"උපතේදී හිමි දශාව: {D_LORDS[d_idx]} (ඉතිරි කාලය: වසර {int(bal)} මාස {int((bal%1)*12)})")
            
            st.subheader("මහා දශා කාලසටහන")
            cy = u_dob.year + bal
            for i in range(1, 5):
                idx = (d_idx + i) % 9
                st.write(f"• **{D_LORDS[idx]} දශාව:** {int(cy)} සිට {int(cy+D_YEARS[idx])} දක්වා")
                cy += D_YEARS[idx]

        st.session_state['data'] = {"name": u_name, "lagna": RA_NAMES[lag_idx], "nak": NAK_NAMES[n_idx]}

if 'data' in st.session_state:
    st.divider()
    if st.button("🔮 AI පලාපල වාර්තාව ලබාගන්න"):
        with st.spinner("AI පලාපල සකසමින්..."):
            st.write(get_ai_prediction(str(st.session_state['data'])))
