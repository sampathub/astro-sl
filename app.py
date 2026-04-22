import swisseph as swe
from datetime import datetime

def calculate_accurate_astrology(name, gender, dob, hour, minute, city):
    """
    නිවැරදි ලග්නය, නැකත, ග්‍රහ පිහිටීම් ගණනය කිරීම
    """
    try:
        # 1. නිවැරදි time zone එක ලබා ගැනීම (ඉතිහාසය සැලකිල්ලට)
        tz_offset = get_sri_lanka_timezone(dob.year)
        
        # 2. UTC පරිවර්තනය
        jd = convert_to_utc_with_history(dob, hour, minute, tz_offset)
        
        # 3. Swiss Ephemeris සැකසීම
        swe.set_ephe_path('ephe')  # හැකි නම් path එක සකසන්න
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # 4. Ayanamsa පරීක්ෂාව
        ayanamsa = swe.get_ayanamsa(jd)
        print(f"Debug: Ayanamsa = {ayanamsa:.6f}°")
        
        # 5. Houses ගණනය - Placidus system, Sidereal
        lat, lon = DISTRICTS[city]
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        # 6. ලග්නය
        lagna_lon = ascmc[0]
        lagna_rashi = int(lagna_lon / 30) % 12
        
        # 7. ග්‍රහ පිහිටීම්
        planet_positions = {}
        for name, pid in PLANETS:
            result, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            planet_positions[name] = result[0]
        
        # 8. නැකත
        moon_lon = planet_positions["සඳු (චන්ද්‍ර)"]
        nak_angle = 360.0 / 27.0
        nak_index = int(moon_lon / nak_angle) % 27
        
        return {
            "lagna": RA_NAMES[lagna_rashi],
            "lagna_lon": lagna_lon,
            "nakshatra": NAK_NAMES[nak_index],
            "planets": planet_positions,
            "jd": jd,
            "ayanamsa": ayanamsa
        }, None
        
    except Exception as e:
        return None, str(e)

def get_sri_lanka_timezone(year):
    """ශ්‍රී ලංකාවේ historical time zone එක ලබා ගැනීම"""
    if 1996 <= year <= 1998:
        return 6.0  # GMT+6:00 (1996 මැයි - 1998 ඔක්තෝබර්)
    else:
        return 5.5  # GMT+5:30

def convert_to_utc_with_history(dob, hour, minute, tz_offset):
    """ඉතිහාසය සැලකිල්ලට ගනිමින් UTC පරිවර්තනය"""
    # Local to UTC conversion
    total_local_minutes = hour * 60 + minute
    total_utc_minutes = total_local_minutes - int(tz_offset * 60)
    
    # Handle day rollover
    utc_day = dob.day
    utc_month = dob.month
    utc_year = dob.year
    utc_hour = total_utc_minutes // 60
    utc_minute = total_utc_minutes % 60
    
    if total_utc_minutes < 0:
        total_utc_minutes += 24 * 60
        utc_day -= 1
        utc_hour = total_utc_minutes // 60
        utc_minute = total_utc_minutes % 60
        
        if utc_day < 1:
            # Previous month logic
            if utc_month == 1:
                utc_month = 12
                utc_year -= 1
                utc_day = 31
            else:
                utc_month -= 1
                # Days in previous month
                if utc_month in [1, 3, 5, 7, 8, 10, 12]:
                    utc_day = 31
                elif utc_month in [4, 6, 9, 11]:
                    utc_day = 30
                else:  # February
                    is_leap = (utc_year % 4 == 0 and utc_year % 100 != 0) or (utc_year % 400 == 0)
                    utc_day = 29 if is_leap else 28
    
    # Gregorian calendar භාවිතයෙන් Julian Day ගණනය
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0, swe.GREG_CAL)
    return jd
