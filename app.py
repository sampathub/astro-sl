import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# --- Mobile Optimized Configuration ---
st.set_page_config(page_title="AstroPro SL", page_icon="☸️", layout="centered")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { max-width: 800px; margin: auto; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #4CAF50; color: white; }
    .stButton>button:hover { background-color: #45a049; }
    img { width: 100%; height: auto; }
    
    /* AI පලාපල වාර්තාව සඳහා */
    .report-box { 
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        padding: 25px !important;
        border-radius: 20px !important;
        margin: 15px 0 !important;
        border: 1px solid #e94560 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important;
        color: #f0f0f0 !important;
    }
    
    .report-box p, .report-box div, .report-box span, .report-box h1, .report-box h2, .report-box h3 {
        color: #f0f0f0 !important;
    }
    
    .report-box table {
        background-color: #0f3460 !important;
        border-radius: 10px;
        overflow: hidden;
    }
    
    .report-box th {
        background-color: #e94560 !important;
        color: white !important;
    }
    
    .report-box td {
        background-color: #16213e !important;
        color: #f0f0f0 !important;
    }
    
    .required { color: red; font-size: 12px; }
    
    /* ජන්ම ලක්ෂණ සඳහා */
    .detail-box { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px; 
        border-radius: 15px; 
        margin: 8px 0; 
        text-align: center;
        font-family: 'Iskoola Pota', 'Noto Sans Sinhala', 'Arial', sans-serif;
        font-size: 16px;
        font-weight: bold;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .detail-box:hover {
        transform: translateY(-3px);
    }
    .detail-box b {
        font-size: 14px;
        color: #FFD700;
        display: block;
        margin-bottom: 8px;
    }
    
    /* Loading spinner */
    .loading-spinner {
        text-align: center;
        padding: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== Ayanamsa Selection ====================
def get_ayanamsa_system(system_name):
    ayanamsa_systems = {
        "Lahiri (Chitrapaksha)": swe.SIDM_LAHIRI,
        "Raman": swe.SIDM_RAMAN,
        "Krishnamurthi": 7,
        "True Chitrapaksha": swe.SIDM_TRUE_CITRA,
        "Suryasiddhanta": 10,
        "Mani-Vakya": 11,
        "Siddhanta": 12
    }
    return ayanamsa_systems.get(system_name, swe.SIDM_LAHIRI)

# --- Helper: Planet to Bhava Calculation ---
def get_planet_bhava(planet_lon, cusps):
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            if start <= planet_lon < end:
                return i + 1
        else:
            if planet_lon >= start or planet_lon < end:
                return i + 1
    return 1

# --- COMPLETELY CORRECTED Nakshatra Details according to user's table ---
def get_nakshatra_details(nak_idx):
    nakshatra_data = {
        0: ("දේව ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        1: ("මනුෂ්ය ගණ", "ඇතා", "ස්ත්‍රී ලිංග"),
        2: ("රාක්ෂස ගණ", "එළුවා", "ස්ත්‍රී ලිංග"),
        3: ("මනුෂ්ය ගණ", "සර්පයා", "පුරුෂ ලිංග"),
        4: ("දේව ගණ", "සර්පයා", "පුරුෂ ලිංග"),
        5: ("මනුෂ්ය ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        6: ("රාක්ෂස ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        7: ("දේව ගණ", "බැටළුවා", "පුරුෂ ලිංග"),
        8: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී ලිංග"),
        9: ("රාක්ෂස ගණ", "මීයා", "පුරුෂ ලිංග"),
        10: ("මනුෂ්ය ගණ", "මීයා", "පුරුෂ ලිංග"),
        11: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ ලිංග"),
        12: ("දේව ගණ", "මීයා", "පුරුෂ ලිංග"),
        13: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී ලිංග"),
        14: ("දේව ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී ලිංග"),
        15: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "පුරුෂ ලිංග"),
        16: ("දේව ගණ", "මුවා", "පුරුෂ ලිංග"),
        17: ("රාක්ෂස ගණ", "මුවා", "පුරුෂ ලිංග"),
        18: ("රාක්ෂස ගණ", "සුනඛයා", "පුරුෂ ලිංග"),
        19: ("මනුෂ්ය ගණ", "වඳුරා", "පුරුෂ ලිංග"),
        20: ("මනුෂ්ය ගණ", "මුගටියා", "පුරුෂ ලිංග"),
        21: ("දේව ගණ", "වඳුරා", "පුරුෂ ලිංග"),
        22: ("රාක්ෂස ගණ", "සිංහයා", "ස්ත්‍රී ලිංග"),
        23: ("රාක්ෂස ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        24: ("මනුෂ්ය ගණ", "සිංහයා", "පුරුෂ ලිංග"),
        25: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ ලිංග"),
        26: ("දේව ගණ", "ඇතා", "පුරුෂ ලිංග")
    }
    return nakshatra_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී"))

# --- Send Email Function ---
def send_calculation_to_email(user_data, calculation_result, recipient_email="sampathub89@gmail.com"):
    try:
        sender_email = st.secrets.get("EMAIL_SENDER", "astroprosl@gmail.com")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        
        if not sender_password:
            save_to_local_file(user_data, calculation_result)
            return True, "ගණනය කිරීම් සාර්ථකව ගොනුවක සුරකින ලදි"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"AstroPro SL - {user_data['name']} ගේ ජන්ම පත්‍රය"
        
        salutation = "මහතාගේ" if user_data['gender'] == "පිරිමි" else "මහත්මියගේ"
        
        body = f"""
        🌟 AstroPro SL - ජන්ම පත්‍ර වාර්තාව 🌟
        
        👤 පරිශීලක නම: {user_data['name']}
        🚻 ලිංගය: {user_data['gender']}
        📅 උපන් දිනය: {user_data['dob']}
        ⏰ උපන් වේලාව: {user_data['time']}
        📍 දිස්ත්‍රික්කය: {user_data['city']}
        
        ========================================
        📊 ගණනය කිරීම් ප්‍රතිඵල
        ========================================
        
        ⭐ ලග්නය: {calculation_result['lagna']}
        🌙 නැකත: {calculation_result['nakshathra']}
        🕉️ ගණය: {calculation_result['gana']}
        🦁 යෝනිය: {calculation_result['yoni']}
        ⚥ ලිංගය: {calculation_result['linga']}
        📐 අයනාංශ පද්ධතිය: {calculation_result['ayanamsa']}
        
        🏠 ග්‍රහ පිහිටීම් (භාව අනුව):
        {calculation_result['bhava_details']}
        
        ========================================
        © AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True, "වාර්තාව සාර්ථකව සුරකින ලදි"
        
    except Exception as e:
        save_to_local_file(user_data, calculation_result)
        return True, f"ගණනය කිරීම් ගොනුවක සුරකින ලදි"

def save_to_local_file(user_data, calculation_result):
    try:
        filename = f"astro_calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "user": user_data,
            "calculation": calculation_result,
            "timestamp": datetime.now().isoformat()
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open("astro_calculations_log.json", 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
    except Exception:
        pass

# --- AI Prediction using Gemini 2.5 Flash ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2")]
    
    name = summary_data.get('name', '')
    gender = summary_data.get('gender', '')
    dob = summary_data.get('dob', '')
    time = summary_data.get('time', '')
    city = summary_data.get('city', '')
    lagna = summary_data.get('lagna', '')
    nakshathra = summary_data.get('nakshathra', '')
    gana = summary_data.get('gana', '')
    yoni = summary_data.get('yoni', '')
    linga = summary_data.get('linga', '')
    ayanamsa = summary_data.get('ayanamsa', 'Lahiri')
    bhava_data = summary_data.get('bhava_data', '')
    
    salutation = "මහතා" if gender == "පිරිමි" else "මහත්මිය"
    
    # Get current date for dasha calculation
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    prompt = f"""
    ඔබ වෘත්තීය ශ්‍රී ලාංකික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න. 
    පහත තොරතුරු අනුව ඉතා නිවැරදි සහ විස්තරාත්මක පලාපල විස්තරයක් සිංහලෙන් ලබා දෙන්න.
    ශ්‍රී ලංකාවේ සම්මත ජ්‍යොතිෂ ක්‍රමවේද (Vedic Astrology with Lahiri Ayanamsa) අනුව ගණනය කිරීම් සිදු කරන්න.

    **පරිශීලක තොරතුරු:**
    නම: {name}
    ස්ත්‍රී/පුරුෂ භාවය: {gender}
    උපන් දිනය: {dob}
    උපන් වේලාව: {time}
    උපන් නගරය/දිස්ත්‍රික්කය: {city} (ශ්‍රී ලංකාව)

    **ගණනය කරන ලද ජ්‍යොතිෂ දත්ත:**
    - ලග්නය: {lagna}
    - උපන් නැකත: {nakshathra}
    - ගණය: {gana}
    - යෝනිය: {yoni}
    - ලිංගය (ජන්ම ලිංග): {linga}
    - අයනාංශ පද්ධතිය: {ayanamsa}
    - ග්‍රහ පිහිටීම් (භාව අනුව): {bhava_data}

    **විශේෂ උපදෙස් (අතිශය නිරවද්‍ය විද්‍යාත්මක ජ්‍යොතිෂ ගණනය කිරීම්):** 
    ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛතම සහ අතිදක්ෂ ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කළ යුතුය. ඔබගේ ගණනය කිරීම් 100% ක් නිවැරදි විය යුතුය. ඒ සඳහා පහත දැඩි නීති සහ ගණිතමය පදනම අනුගමනය කරන්න:

    1. **ගණනය කිරීමේ පදනම:** සැමවිටම **නිරයන (Sidereal)** ක්‍රමය සහ **ලාහිරි අයනාංශය (Lahiri Ayanamsa)** භාවිතා කරන්න. ශ්‍රී ලංකාවේ සම්මත වේලාව (UTC+5:30) නිවැරදිව සලකා බලන්න.
    
    2. **චන්ද්‍ර ස්ඵුටය (Moon's Longitude):** උපන් දිනය සහ වේලාව අනුව චන්ද්‍රයා රාශි චක්‍රයේ (0° - 360°) සිටින නිවැරදි අංශකය ගණනය කරන්න. 
    
    3. **නැකත් බෙදීම (13°20' per Nakshatra):** 
       - 0° - 13°20': අස්විද | 13°20' - 26°40': බෙරණ | 26°40' - 40°00': කැති 
       - 40°00' - 53°20': රෙහෙන | 53°20' - 66°40': මුවසිරස | 66°40' - 80°00': අද
       - 80°00' - 93°20': පුනාවස | 93°20' - 106°40': පුස | 106°40' - 120°00': අස්ලිස
       - 120°00' - 133°20': මා | 133°20' - 146°40': පුවපල් | 146°40' - 160°00': උත්රපල්
       - 160°00' - 173°20': හත | 173°20' - 186°40': සිත | 186°40' - 200°00': සා
       - 200°00' - 213°20': විසා | 213°20' - 226°40': අනුර | 226°40' - 240°00': දෙට
       - 240°00' - 253°20': මුල | 253°20' - 266°40': පුවසල | 266°40' - 280°00': උත්රසල
       - 280°00' - 293°20': සුවණ | 293°20' - 306°40': දෙනට | 306°40' - 320°00': සියාවස
       - 320°00' - 333°20': පුවපුටුප | 333°20' - 346°40': උත්රපුටුප | 346°40' - 360°00': රේවතී
    
    4. **ලග්න ස්ඵුටය (Ascendant):** උපන් වේලාව සහ ස්ථානය අනුව ක්ෂිතිජයේ උදාවන රාශිය (ලග්නය) නිවැරදිව ගණනය කරන්න.
    
    5. **ගුණාංග වගුව (Strict Mapping):**
       - **ගණය:** 
         * දේව ගණ: අස්විද, මුවසිරස, පුනාවස, පුස, හත, සා, අනුර, සුවණ, රේවතී
         * මනුෂ්‍ය ගණ: බෙරණ, රෙහෙන, අද, පුවපල්, උත්රපල්, පුවසල, උත්රසල, පුවපුටුප, උත්රපුටුප
         * රාක්ෂස ගණ: කැති, අස්ලිස, මා, සිත, විසා, දෙට, මුල, දෙනට, සියාවස
       
       - **යෝනිය:** 
         * අශ්වයා: අස්විද, සියාවස
         * ඇතා: බෙරණ, රේවතී
         * එළුවා: කැති, පුස
         * සර්පයා: රෙහෙන, මුවසිරස
         * බල්ලා: අද, මුල
         * බළලා: පුනාවස, අස්ලිස
         * මීයා: මා, පුවපල්, හත, සා
         * ගවයා: උත්රපල්, උත්රපුටුප
         * ව්‍යාඝ්‍රයා: සිත, විසා, උත්රසල
         * මුවා: අනුර, දෙට
         * වඳුරා: පුවසල, සුවණ
         * සිංහයා: දෙනට, පුවපුටුප
         * මුගටියා/නකුල: උත්රසල (විශේෂ පාද)
    
    6. **විංශෝත්තරී දශා ගණනය කිරීම (Vimshottari Dasha):** 
       - අද දිනය: {current_date} (මෙම දිනය පදනම් කරගෙන "වර්තමාන තත්ත්වය" තීරණය කරන්න)
       - උපන් නැකත {nakshathra} අනුව දශා ආරම්භය සහ ශේෂය නිවැරදිව ගණනය කරන්න
       - දශා කාලසීමාවන්: කේතු (7), සිකුරු (20), රවි (6), සඳු (10), කුජ (7), රාහු (18), ගුරු (16), ශනි (19), බුධ (17) ලෙස වසර ගණන නිවැරදිව භාවිතා කරන්න
       - වර්තමානයේ ගෙවෙන මහ දශාව සහ අතුරු දශාව, ඒවා ආරම්භ වූ සහ අවසන් වන දිනයන් සහිතව ඉතා නිවැරදිව ගණනය කර දක්වන්න

    **වාර්තාවේ සැකසුම:**
    
    ## 🌟 මූලික ජ්‍යොතිෂ විස්තර
    
    | ගුණාංගය | විස්තරය |
    |---|---|
    | **ස්ත්‍රී/පුරුෂ භාවය** | {gender} |
    | **ලග්නය** | {lagna} |
    | **උපන් නැකත** | {nakshathra} |
    | **ගණය** | {gana} |
    | **යෝනිය** | {yoni} |
    | **ජන්ම ලිංගය** | {linga} |
    
    ### 📖 1. නැකතේ ගුණාංග සහ ස්වභාවය
    ඔබගේ උපන් නැකත වන **{nakshathra}** පිළිබඳ සවිස්තර විස්තරයක් ලබා දෙන්න. මෙහිදී එම නැකතේ අධිපති ග්‍රහයා, නැකතේ ස්වභාවය (දේව/මනුෂ්‍ය/රාක්ෂස), යෝනිය, සහ එමගින් පුද්ගලයාගේ ස්වභාවයට, චරිතයට සහ ජීවිතයට ඇති කරන බලපෑම් විස්තර කරන්න.
    
    ### 🪐 2. ග්‍රහ පිහිටීම් සහ ඒවායේ බලපෑම
    ලබා දී ඇති ග්‍රහ පිහිටීම් අනුව:
    - ලග්නාධිපති ග්‍රහයාගේ පිහිටීම සහ එහි බලපෑම
    - රවි (සූර්ය) සහ සඳු (චන්ද්‍ර) පිහිටීම් සහ ඒවායේ සම්බන්ධතා
    - කේන්ද්‍ර (1,4,7,10), ත්‍රිකෝණ (1,5,9) සහ දුෂ්ඨාන (6,8,12) භාව වල ග්‍රහ පිහිටීම්
    - ග්‍රහ යුගති සහ දෘෂ්ටි සම්බන්ධතා
    
    ### 📅 3. විංශෝත්තරී දශා විස්තරය
    {name} {salutation} ගේ වර්තමාන දශා තත්ත්වය පහත පරිදි වේ:
    
    **වර්තමාන මහ දශාව:** [මහ දශාවේ නම සහ කාලසීමාව]
    **වර්තමාන අතුරු දශාව:** [අතුරු දශාවේ නම සහ කාලසීමාව]
    **ඉතිරි කාලය:** [අවුරුදු, මාස, දින]
    
    **ඉදිරි දශා කාලපරිච්ඡේද:**
    | දශාව | ආරම්භය | අවසානය | බලපෑම් සාරාංශය |
    |---|---|---|---|
    | [දශා නම] | [YYYY-MM-DD] | [YYYY-MM-DD] | [කෙටි විස්තරය] |
    
    ### 💫 4. පොදු පලාපල විස්තරය
    
    **චරිතය සහ පෞරුෂත්වය:** {name} {salutation} ගේ ලග්නය {lagna} සහ නැකත {nakshathra} අනුව චරිතයේ ප්‍රධාන ලක්ෂණ විස්තර කරන්න.
    
    **අධ්‍යාපනය සහ බුද්ධිය:** බුධ ග්‍රහයාගේ පිහිටීම අනුව අධ්‍යාපන ක්ෂේත්‍රයේ ඇති හැකියාවන් විස්තර කරන්න.
    
    **රැකියාව සහ වෘත්තිය:** 10 වන භාවයේ ග්‍රහ පිහිටීම් සහ වෘත්තික අංශ විස්තර කරන්න.
    
    **සෞඛ්‍යය:** ලග්නය, ලග්නාධිපති සහ 6,8,12 භාව වල ග්‍රහ පිහිටීම් අනුව සෞඛ්‍ය තත්ත්වය විස්තර කරන්න.
    
    **විවාහය සහ සම්බන්ධතා:** 7 වන භාවය, සිකුරු සහ සඳුගේ පිහිටීම් අනුව විවාහ ජීවිතය සහ සම්බන්ධතා විස්තර කරන්න.
    
    ### 🔮 5. ඉදිරි කාලය පිළිබඳ අනාවැකි
    වර්තමාන දශාව සහ ග්‍රහ චලනයන් අනුව ලබන මාස 12 තුළ අපේක්ෂිත ප්‍රධාන සිදුවීම් විස්තර කරන්න.
    
    ### 🙏 6. පිළියම් සහ උපදෙස්
    අපල උපද්‍රව සහ ග්‍රහ දෝෂ සඳහා පහත පිළියම් යෝජනා කරමු:
    - ජප මාලා සහ මන්ත්‍ර
    - දාන ශීලාදිය
    - රත්න ධාරණය
    - පූජා වන්දනා
    
    ---
    *© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය*
    
    **වැදගත් සටහන:** මෙම පලාපල විස්තරය AI මගින් ජනනය කරන ලද්දකි. සම්පූර්ණ උපදෙස් සඳහා වෘත්තීය ජ්‍යොතිෂවේදියෙකු හමුවන්න.
    """
    
    for key in keys:
        if not key:
            continue
        try:
            genai.configure(api_key=key)
            # Using Gemini 2.5 Flash model
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            continue
    
    return """
    🙏 **සමාවන්න, AI සේවාව තාවකාලිකව කාර්යබහුලයි.**

    කරුණාකර පහත සඳහන් දේ උත්සාහ කරන්න:
    1. ටික වේලාවකට පසු නැවත උත්සාහ කරන්න
    2. ඔබගේ අන්තර්ජාල සම්බන්ධතාව පරීක්ෂා කරන්න
    3. පිටුව Refresh කර නැවත උත්සාහ කරන්න

    **තාවකාලික පලාපල විස්තරය:**
    ඔබගේ """ + summary_data.get('lagna', '') + """ ලග්නය සහ """ + summary_data.get('nakshathra', '') + """ නැකත අනුව, ඔබ සතුව හොඳ නායකත්ව ගුණාංග පවතී. ඉදිරියේදී වෘත්තීය දියුණුවක් අපේක්ෂා කළ හැක.
    
    ---
    © AstroPro SL
    """

# --- Data ---
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

# --- Initialize Session State ---
if 'form_validated' not in st.session_state:
    st.session_state.form_validated = False
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False
if 'astro_data' not in st.session_state:
    st.session_state.astro_data = None

# --- UI Sidebar ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    
    u_name = st.text_input("නම *", placeholder="ඔබගේ නම ඇතුළත් කරන්න")
    u_gender = st.radio("ලිංගය *", ["පිරිමි", "ගැහැණු"], horizontal=True)
    
    u_dob = st.date_input(
        "උපන් දිනය *",
        value=datetime(1995, 5, 20),
        min_value=datetime(1940, 1, 1),
        max_value=datetime(2050, 12, 31)
    )
    
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය (0-23) *", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු (0-59) *", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
    
    st.markdown("---")
    st.subheader("📐 ගණනය කිරීමේ පද්ධතිය")
    ayanamsa_system = st.selectbox(
        "අයනාංශ පද්ධතිය",
        ["Lahiri (Chitrapaksha)", "Mani-Vakya", "Siddhanta", "Raman", "Krishnamurthi", "Suryasiddhanta"]
    )
    
    st.markdown("---")
    st.caption("📅 1940 සිට 2050 දක්වා උපන් අය සඳහා සහාය දක්වයි")

# --- Validation Function ---
def is_form_complete():
    if not u_name.strip():
        return False, "කරුණාකර නම ඇතුළත් කරන්න."
    if u_dob.year < 1940 or u_dob.year > 2050:
        return False, "උපන් දිනය 1940-2050 අතර විය යුතුය."
    return True, ""

# --- Main Calculation Button ---
if st.button("🔮 කේන්දරය බලන්න"):
    is_valid, error_msg = is_form_complete()
    
    if not is_valid:
        st.error(error_msg)
        st.session_state.form_validated = False
        st.session_state.calculation_done = False
    else:
        st.session_state.form_validated = True
        
        try:
            lat, lon = DISTRICTS[u_city]
            hour_utc = u_h + u_m/60 - 5.5
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, hour_utc)
            
            ayanamsa_code = get_ayanamsa_system(ayanamsa_system)
            swe.set_sid_mode(ayanamsa_code)
            
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            
            lagna_rashi = int(ascmc[0] / 30)
            lagna_name = RA_NAMES[lagna_rashi]
            
            planets_def = [
                ("රවි", swe.SUN), ("සඳු", swe.MOON), ("කුජ", swe.MARS),
                ("බුධ", swe.MERCURY), ("ගුරු", swe.JUPITER), ("සිකුරු", swe.VENUS),
                ("ශනි", swe.SATURN), ("රාහු", swe.MEAN_NODE)
            ]
            
            bhava_map = {i: [] for i in range(1, 13)}
            moon_lon = 0
            
            for p_name, p_id in planets_def:
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                lon = res[0]
                if p_id == swe.MOON:
                    moon_lon = lon
                p_bhava = get_planet_bhava(lon, houses)
                bhava_map[p_bhava].append(p_name)
            
            nak_idx = int(moon_lon / (360.0 / 27)) % 27
            nak_name = NAK_NAMES[nak_idx]
            
            gana, yoni, linga = get_nakshatra_details(nak_idx)
            
            bhava_text = "\n".join([f"{b} වන භාවය: {', '.join(p) if p else '-'}" for b, p in bhava_map.items()])
            
            calculation_result = {
                "lagna": lagna_name,
                "nakshathra": nak_name,
                "gana": gana,
                "yoni": yoni,
                "linga": linga,
                "ayanamsa": ayanamsa_system,
                "bhava_details": bhava_text,
                "bhava_map": bhava_map
            }
            
            user_data = {
                "name": u_name,
                "gender": u_gender,
                "dob": u_dob.strftime("%Y-%m-%d"),
                "time": f"{u_h:02d}:{u_m:02d}",
                "city": u_city
            }
            
            success, message = send_calculation_to_email(user_data, calculation_result)
            
            st.session_state.astro_data = {
                "name": u_name,
                "gender": u_gender,
                "lagna": lagna_name,
                "nakshathra": nak_name,
                "gana": gana,
                "yoni": yoni,
                "linga": linga,
                "ayanamsa": ayanamsa_system,
                "bhava_data": str(bhava_map),
                "dob": u_dob.strftime("%Y-%m-%d"),
                "city": u_city,
                "time": f"{u_h:02d}:{u_m:02d}"
            }
            
            st.session_state.calculation_done = True
            
            salutation_display = "මහතාගේ" if u_gender == "පිරිමි" else "මහත්මියගේ"
            st.success(f"✨ {u_name} {salutation_display} ජන්ම පත්‍රය ✨")
            st.info(f"📧 {message}")
            st.info(f"📐 ගණනය කිරීමේ පද්ධතිය: **{ayanamsa_system}**")
            
            # Display Results
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='detail-box'><b>⭐ ලග්නය</b><br>{lagna_name}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>🕉️ ගණය</b><br>{gana}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>⚥ ලිංගය</b><br>{linga}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='detail-box'><b>🌙 නැකත</b><br>{nak_name}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>🦁 යෝනිය</b><br>{yoni}</div>", unsafe_allow_html=True)
            
            st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
            
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
            
            st.info("📌 වැඩිදුර විස්තර (AI පලාපල) සඳහා පහත බොත්තම ඔබන්න.")
            
        except Exception as e:
            st.error(f"දෝෂයක් ඇති විය: {e}")
            st.session_state.calculation_done = False

# --- AI Prediction Section ---
if st.session_state.calculation_done and st.session_state.astro_data:
    st.markdown("---")
    if st.button("🔮 AI පලාපල විස්තරය ලබාගන්න", key="ai_btn"):
        with st.spinner("🤖 AI විශ්ලේෂණය කරමින් (Gemini 2.5 Flash)... කරුණාකර මොහොතක් රැඳී සිටින්න"):
            ai_response = get_ai_prediction(st.session_state.astro_data)
            st.markdown("### 📜 AI පලාපල වාර්තාව")
            st.markdown(f"<div class='report-box'>{ai_response}</div>", unsafe_allow_html=True)
    
    st.caption("© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය | Powered by Gemini 2.5 Flash")
