# sticky_header.py — Sticky Header with Live Clock (21 Languages + Animation + Correct BS)
import streamlit.components.v1 as components
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import nepali_datetime


def to_nepali_digits(value):
    """Convert English digits to Nepali digits"""
    return str(value).translate(str.maketrans("0123456789", "०१२३४५६७८९"))


# ============================================================
# 🌐 21 भाषाको Language Data
# ============================================================
LANG_DATA = {
    "ne": {
        "greeting": "नमस्ते",
        "speak": "🎤 बोल्नुहोस् वा लेख्नुहोस्",
        "days": ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"],
        "months": ["वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
                   "कात्तिक", "मंसिर", "पुस", "माघ", "फागुन", "चैत"],
        "am": "AM", "pm": "PM", "date_format": "bs", "rtl": False,
    },
    "en": {
        "greeting": "Hello",
        "speak": "🎤 Speak or type",
        "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "months": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "hi": {
        "greeting": "नमस्ते",
        "speak": "🎤 बोलें या लिखें",
        "days": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
        "months": ["जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून",
                   "जुलाई", "अगस्त", "सितम्बर", "अक्टूबर", "नवम्बर", "दिसम्बर"],
        "am": "पूर्वाह्न", "pm": "अपराह्न", "date_format": "ad", "rtl": False,
    },
    "zh": {
        "greeting": "你好",
        "speak": "🎤 说话或输入",
        "days": ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
        "months": ["一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"],
        "am": "上午", "pm": "下午", "date_format": "ad", "rtl": False,
    },
    "es": {
        "greeting": "Hola",
        "speak": "🎤 Habla o escribe",
        "days": ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
        "months": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "fr": {
        "greeting": "Bonjour",
        "speak": "🎤 Parlez ou tapez",
        "days": ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
        "months": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "ar": {
        "greeting": "مرحبا",
        "speak": "🎤 تحدث أو اكتب",
        "days": ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"],
        "months": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                   "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
        "am": "ص", "pm": "م", "date_format": "ad", "rtl": True,
    },
    "ja": {
        "greeting": "こんにちは",
        "speak": "🎤 話すか入力してください",
        "days": ["日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日"],
        "months": ["1月", "2月", "3月", "4月", "5月", "6月",
                   "7月", "8月", "9月", "10月", "11月", "12月"],
        "am": "午前", "pm": "午後", "date_format": "ad", "rtl": False,
    },
    "ko": {
        "greeting": "안녕하세요",
        "speak": "🎤 말하거나 입력하세요",
        "days": ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"],
        "months": ["1월", "2월", "3월", "4월", "5월", "6월",
                   "7월", "8월", "9월", "10월", "11월", "12월"],
        "am": "오전", "pm": "오후", "date_format": "ad", "rtl": False,
    },
    "de": {
        "greeting": "Hallo",
        "speak": "🎤 Sprich oder tippe",
        "days": ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
        "months": ["Januar", "Februar", "März", "April", "Mai", "Juni",
                   "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "pt": {
        "greeting": "Olá",
        "speak": "🎤 Fale ou digite",
        "days": ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"],
        "months": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "ru": {
        "greeting": "Привет",
        "speak": "🎤 Говорите или печатайте",
        "days": ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"],
        "months": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "it": {
        "greeting": "Ciao",
        "speak": "🎤 Parla o scrivi",
        "days": ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"],
        "months": ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                   "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "tr": {
        "greeting": "Merhaba",
        "speak": "🎤 Konuş veya yaz",
        "days": ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"],
        "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
        "am": "ÖÖ", "pm": "ÖS", "date_format": "ad", "rtl": False,
    },
    "id": {
        "greeting": "Halo",
        "speak": "🎤 Bicara atau ketik",
        "days": ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"],
        "months": ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "vi": {
        "greeting": "Xin chào",
        "speak": "🎤 Nói hoặc gõ",
        "days": ["Chủ nhật", "Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Thứ bảy"],
        "months": ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
                   "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"],
        "am": "SA", "pm": "CH", "date_format": "ad", "rtl": False,
    },
    "th": {
        "greeting": "สวัสดี",
        "speak": "🎤 พูดหรือพิมพ์",
        "days": ["วันอาทิตย์", "วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์"],
        "months": ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                   "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "nl": {
        "greeting": "Hallo",
        "speak": "🎤 Spreek of typ",
        "days": ["Zondag", "Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag"],
        "months": ["Januari", "Februari", "Maart", "April", "Mei", "Juni",
                   "Juli", "Augustus", "September", "Oktober", "November", "December"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "pl": {
        "greeting": "Cześć",
        "speak": "🎤 Mów lub pisz",
        "days": ["Niedziela", "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"],
        "months": ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
                   "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "sv": {
        "greeting": "Hej",
        "speak": "🎤 Tala eller skriv",
        "days": ["Söndag", "Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag"],
        "months": ["Januari", "Februari", "Mars", "April", "Maj", "Juni",
                   "Juli", "Augusti", "September", "Oktober", "November", "December"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
    "tl": {
        "greeting": "Kumusta",
        "speak": "🎤 Magsalita o mag-type",
        "days": ["Linggo", "Lunes", "Martes", "Miyerkules", "Huwebes", "Biyernes", "Sabado"],
        "months": ["Enero", "Pebrero", "Marso", "Abril", "Mayo", "Hunyo",
                   "Hulyo", "Agosto", "Setyembre", "Oktubre", "Nobyembre", "Disyembre"],
        "am": "AM", "pm": "PM", "date_format": "ad", "rtl": False,
    },
}


def render_sticky_header(username, lang="ne"):
    """
    Sticky header with live clock (JavaScript-powered)
    21 भाषा support + Animation + सही BS format
    """
    data = LANG_DATA.get(lang, LANG_DATA["ne"])
    is_rtl = data.get("rtl", False)
    direction = "rtl" if is_rtl else "ltr"

    # ✅ Nepal time
    now_np = datetime.now(ZoneInfo("Asia/Kathmandu"))

    # ✅ नेपाली BS मिति — "वि.सं. २०८३ मंसिर ११, शुक्रबार" format
    nepali_date_text = ""
    if data["date_format"] == "bs":
        try:
            bs_date = nepali_datetime.date.from_datetime_date(now_np.date())
            nepali_days = ["आइतबार", "सोमबार", "मंगलबार", "बुधबार",
                           "बिहीबार", "शुक्रबार", "शनिबार"]
            # ✅ AD date को weekday() प्रयोग (सोमबार=0, आइतबार=6)
            # AD र BS को दिन नाम सधैं मिल्छ
            ad_weekday = now_np.weekday()          # 0=Mon ... 6=Sun
            nepali_idx = (ad_weekday + 1) % 7      # 0=Sun ... 6=Sat
            day_name = nepali_days[nepali_idx]

            nepali_date_text = (
                f"वि.सं. {to_nepali_digits(bs_date.year)} "
                f"{data['months'][bs_date.month - 1]} "
                f"{to_nepali_digits(bs_date.day)}, "
                f"{day_name}"
            )
        except Exception as e:
            print(f"[BS DATE ERROR] {e}")
            nepali_date_text = "मिति उपलब्ध छैन"

    # ⚠️ JavaScript — Live clock + Animation
    html = f"""
    <!DOCTYPE html>
    <html dir="{direction}">
    <head>
        <meta charset="utf-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}

            body {{
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                overflow: hidden;
                background: transparent;
            }}

            /* ============================================================ */
            /* 🎬 ANIMATIONS                                                 */
            /* ============================================================ */
            @keyframes headerSlideIn {{
                from {{ opacity: 0; transform: translateY(-10px); }}
                to   {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes borderGlow {{
                0%, 100% {{ box-shadow: 0 4px 20px rgba(102,126,234,0.15), inset 0 0 0 1px rgba(102,126,234,0.1); }}
                50%      {{ box-shadow: 0 6px 28px rgba(102,126,234,0.3), inset 0 0 0 1px rgba(102,126,234,0.25); }}
            }}
            @keyframes gradientShift {{
                0%   {{ background-position: 0% 50%; }}
                100% {{ background-position: 200% 50%; }}
            }}
            @keyframes pulseDot {{
                0%, 100% {{ box-shadow: 0 0 0 0 rgba(49,162,76,0.7); }}
                70%      {{ box-shadow: 0 0 0 8px rgba(49,162,76,0); }}
            }}
            @keyframes floatClock {{
                0%, 100% {{ transform: translateY(0); }}
                50%      {{ transform: translateY(-3px); }}
            }}
            @keyframes shimmer {{
                0%   {{ left: -100%; }}
                100% {{ left: 200%; }}
            }}
            @keyframes titleShine {{
                0%   {{ background-position: 0% 50%; }}
                100% {{ background-position: 200% 50%; }}
            }}

            /* ============================================================ */
            /* 🎨 HEADER CONTAINER                                           */
            /* ============================================================ */
            .sticky-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 12px 20px;
                border-radius: 14px;
                border-left: 4px solid #667eea;
                position: relative;
                overflow: hidden;
                animation: headerSlideIn 0.5s cubic-bezier(0.2, 0.8, 0.2, 1), borderGlow 4s ease-in-out infinite;
                transition: transform 0.25s ease;
            }}
            .sticky-header:hover {{
                transform: translateY(-2px);
            }}

            /* Shimmer overlay */
            .sticky-header::before {{
                content: '';
                position: absolute;
                top: 0; left: -100%;
                width: 60%; height: 100%;
                background: linear-gradient(120deg, transparent, rgba(102,126,234,0.08), transparent);
                transform: skewX(-20deg);
                animation: shimmer 5s infinite;
                pointer-events: none;
            }}

            /* Floating particles (decorative) */
            .sticky-header::after {{
                content: '';
                position: absolute;
                top: -50%; right: -10%;
                width: 200px; height: 200px;
                background: radial-gradient(circle, rgba(102,126,234,0.08), transparent 70%);
                border-radius: 50%;
                pointer-events: none;
            }}

            /* ============================================================ */
            /* 📝 LEFT SECTION                                               */
            /* ============================================================ */
            .left-section {{
                display: flex;
                flex-direction: column;
                gap: 2px;
                position: relative;
                z-index: 1;
            }}
            .app-title {{
                font-size: 1.4rem;
                font-weight: 800;
                background: linear-gradient(90deg, #667eea 0%, #a78bfa 50%, #764ba2 100%);
                background-size: 200% auto;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: titleShine 4s linear infinite;
            }}
            .greeting {{
                font-size: 0.85rem;
                color: #666;
                display: flex;
                align-items: center;
                gap: 6px;
                animation: headerSlideIn 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.1s both;
            }}
            .greeting b {{
                color: #667eea;
                font-weight: 700;
            }}
            .greeting .pulse-dot {{
                display: inline-block;
                width: 8px; height: 8px;
                border-radius: 50%;
                background: #31a24c;
                animation: pulseDot 1.8s infinite;
                flex-shrink: 0;
            }}

            /* ============================================================ */
            /* ⏰ DATETIME BOX                                               */
            /* ============================================================ */
            .datetime-box {{
                display: flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                background-size: 200% auto;
                animation: gradientShift 6s linear infinite;
                color: white;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 4px 16px rgba(102,126,234,0.4);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                position: relative;
                z-index: 1;
                overflow: hidden;
            }}
            .datetime-box:hover {{
                transform: translateY(-1px) scale(1.02);
                box-shadow: 0 8px 24px rgba(102,126,234,0.55);
            }}
            .clock-icon {{
                font-size: 1.2rem;
                animation: floatClock 3s ease-in-out infinite;
                flex-shrink: 0;
            }}
            .time-text {{
                font-family: 'Courier New', monospace;
                letter-spacing: 0.5px;
                font-weight: 700;
                font-size: 0.9rem;
            }}
            .date-text {{
                font-size: 0.75rem;
                opacity: 0.92;
                margin-top: 2px;
            }}
            .datetime-content {{
                display: flex;
                flex-direction: column;
                line-height: 1.2;
            }}

            /* ============================================================ */
            /* 📱 RESPONSIVE                                                 */
            /* ============================================================ */
            @media (max-width: 600px) {{
                .app-title {{ font-size: 1.1rem; }}
                .datetime-box {{ padding: 6px 10px; font-size: 0.75rem; }}
                .time-text {{ font-size: 0.8rem; }}
                .date-text {{ font-size: 0.65rem; }}
                .sticky-header {{ padding: 10px 14px; }}
            }}
        </style>
    </head>
    <body>
        <div class="sticky-header">
            <div class="left-section">
                <div class="app-title">🧠 PDF Brain</div>
                <div class="greeting">
                    <span class="pulse-dot"></span>
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
            const dateFormat = "{data['date_format']}";

            // ✅ Python बाट पठाइएको नेपाली BS मिति (पूरा format सहित)
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

                const hour12 = hour % 12 || 12;
                const ampm = hour < 12 ? amLabel : pmLabel;

                let timeStr, dateStr;

                if (lang === "ne") {{
                    // ✅ नेपालीमा — पूरा BS मिति (दिन नाम सहित)
                    timeStr = toNepali(hour12) + ":" + toNepali(minute) + ":" + toNepali(second) + " " + ampm;
                    dateStr = nepaliDateText;
                }} else if (lang === "hi") {{
                    timeStr = String(hour12).padStart(2, '0') + ":" + String(minute).padStart(2, '0') + ":" + String(second).padStart(2, '0') + " " + ampm;
                    dateStr = dayName + ", " + day + " " + monthName + " " + year;
                }} else {{
                    timeStr = String(hour12).padStart(2, '0') + ":" + String(minute).padStart(2, '0') + ":" + String(second).padStart(2, '0') + " " + ampm;
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
    """Tabs + Chat Input sticky CSS"""
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