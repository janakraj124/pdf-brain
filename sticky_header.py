# sticky_header.py — Sticky Header with Live Clock (Nepali BS Date Fixed)
import streamlit.components.v1 as components
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import nepali_datetime

def to_nepali_digits(value):
    """Convert English digits to Nepali digits"""
    return str(value).translate(str.maketrans("0123456789", "०१२३४५६७८९"))

def render_sticky_header(username, lang="ne"):
    """
    Sticky header with live clock (JavaScript-powered)
    """
    # Language-specific data
    lang_data = {
        "ne": {
            "greeting": "नमस्ते",
            "speak": "🎤 बोल्नुहोस् वा लेख्नुहोस्",
            "days": ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"],
            # ✅ सही नेपाली महिना
            "months": ["वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
                       "कात्तिक", "मंसिर", "पुस", "माघ", "फागुन", "चैत"],
            "am": "AM",
            "pm": "PM"
        },
        "en": {
            "greeting": "Hello",
            "speak": "🎤 Speak or type",
            "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "months": ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"],
            "am": "AM",
            "pm": "PM"
        },
        "hi": {
            "greeting": "नमस्ते",
            "speak": "🎤 बोलें या लिखें",
            "days": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
            "months": ["जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून",
                       "जुलाई", "अगस्त", "सितम्बर", "अक्टूबर", "नवम्बर", "दिसम्बर"],
            "am": "पूर्वाह्न",
            "pm": "अपराह्न"
        }
    }
    
    data = lang_data.get(lang, lang_data["ne"])
    
    # ✅ Python बाट वास्तविक विक्रम संवत् (BS) मिति निकाल्ने
    now_np = datetime.now(ZoneInfo("Asia/Kathmandu"))
    try:
        bs_date = nepali_datetime.date.from_datetime_date(now_np.date())
        nepali_date_text = (
            f"{to_nepali_digits(bs_date.day)} "
            f"{data['months'][bs_date.month - 1]} "
            f"{to_nepali_digits(bs_date.year)}"
        )
    except Exception:
        # Fallback यदि library फेल भयो भने
        nepali_date_text = "मिति उपलब्ध छैन"
        
    # ⚠️ JavaScript — Live clock + Sticky
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                overflow: hidden;
            }}
            .sticky-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 12px 20px;
                border-radius: 12px;
                border-left: 4px solid #667eea;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            .left-section {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}
            .app-title {{
                font-size: 1.4rem;
                font-weight: 700;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .greeting {{
                font-size: 0.85rem;
                color: #666;
            }}
            .greeting b {{
                color: #667eea;
            }}
            .datetime-box {{
                display: flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }}
            .clock-icon {{
                font-size: 1.1rem;
            }}
            .time-text {{
                font-family: 'Courier New', monospace;
                letter-spacing: 0.5px;
            }}
            .date-text {{
                font-size: 0.75rem;
                opacity: 0.9;
                margin-top: 2px;
            }}
            .datetime-content {{
                display: flex;
                flex-direction: column;
                line-height: 1.2;
            }}
            @media (max-width: 600px) {{
                .app-title {{ font-size: 1.1rem; }}
                .datetime-box {{ padding: 6px 10px; font-size: 0.75rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="sticky-header">
            <div class="left-section">
                <div class="app-title">🧠 PDF Brain</div>
                <div class="greeting">
                    {data['greeting']} <b>{username}</b>! {data['speak']}
                </div>
            </div>
            <div class="datetime-box">
                <span class="clock-icon">⏰</span>
                <div class="datetime-content">
                    <div class="time-text" id="live-time">--:--:--</div>
                    <div class="date-text" id="live-date">...</div>
                </div>
            </div>
        </div>
        
        <script>
            // ⚠️ Language data
            const lang = "{lang}";
            const days = {data['days']};
            const months = {data['months']};
            const amLabel = "{data['am']}";
            const pmLabel = "{data['pm']}";
            
            // ✅ Python बाट पठाइएको नेपाली BS मिति
            const nepaliDateText = "{nepali_date_text}";
            
            function toNepali(n, pad=2) {{
                const nep = "०१२३४५६७८९";
                let s = String(n).padStart(pad, '0');
                return s.split('').map(d => nep[parseInt(d)] || d).join('');
            }}
            
            function updateClock() {{
                const now = new Date();
                let hour = now.getHours();
                let minute = now.getMinutes();
                let second = now.getSeconds();
                let day = now.getDate();
                let month = now.getMonth();
                let year = now.getFullYear();
                let dayName = days[now.getDay()];
                let monthName = months[month];
                
                // 12-hour format
                const hour12 = hour % 12 || 12;
                const ampm = hour < 12 ? amLabel : pmLabel;
                
                let timeStr, dateStr;
                
                if (lang === "ne") {{
                    timeStr = toNepali(hour12) + ":" + toNepali(minute) + ":" + toNepali(second) + " " + ampm;
                    // ✅ नेपाली BS मिति प्रयोग
                    dateStr = dayName + ", " + nepaliDateText;
                }} else if (lang === "hi") {{
                    timeStr = String(hour12).padStart(2, '0') + ":" + String(minute).padStart(2, '0') + ":" + String(second).padStart(2, '0') + " " + ampm;
                    dateStr = dayName + ", " + day + " " + monthName + " " + year;
                }} else {{
                    const ampmEn = hour < 12 ? "AM" : "PM";
                    timeStr = String(hour12).padStart(2, '0') + ":" + String(minute).padStart(2, '0') + ":" + String(second).padStart(2, '0') + " " + ampmEn;
                    dateStr = dayName + ", " + monthName + " " + day + ", " + year;
                }}
                
                document.getElementById("live-time").textContent = timeStr;
                document.getElementById("live-date").textContent = dateStr;
            }}
            
            // Initial update
            updateClock();
            
            // Update every second
            setInterval(updateClock, 1000);
        </script>
    </body>
    </html>
    """
    
    # Render with height ~95px
    components.html(html, height=95, scrolling=False)


def inject_sticky_tabs_css():
    """Tabs + Chat Input sticky CSS (पहिले जस्तै)"""
    st.markdown("""
    <style>
        /* === Sticky Tabs === */
        .stTabs [data-baseweb="tab-list"] {
            position: sticky !important;
            top: 100px !important;
            z-index: 998 !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
            padding: 8px 12px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
            border-left: 4px solid #667eea !important;
            margin-bottom: 15px !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            transition: all 0.3s ease !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(102, 126, 234, 0.1) !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        /* === Sticky Chat Input (Bottom) === */
        [data-testid="stChatInput"] {
            position: sticky !important;
            bottom: 0 !important;
            z-index: 997 !important;
            background: white !important;
            padding: 10px 0 !important;
            border-top: 2px solid #f0f0f0 !important;
        }
        
        /* === Main scroll offset === */
        .main .block-container {
            padding-top: 20px !important;
        }
    </style>
    """, unsafe_allow_html=True)