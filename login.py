# login.py — PDF Brain v55.0 (Fixed Language Switch + Animation + OTP)
import re
import streamlit as st

from auth import (
    verify_user,
    create_user,
    update_user_language,
    update_user_password,
    user_exists_by_email,
)

from translations import LANGUAGES, TRANSLATIONS
from otp_manager import generate_otp, verify_otp, clear_otp
from email_helper import send_otp_email as _send_otp_raw


EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"


# ============================================================
# OTP EMAIL WRAPPER
# ============================================================
def send_otp_email(to_email, otp, purpose="signup", lang="ne"):
    try:
        result = _send_otp_raw(
            to_email, otp,
            username="",
            lang=lang,
            purpose=purpose
        )
        if result.get("success"):
            return True, "OTP इमेल पठाइयो।"
        else:
            err = result.get("error", "अज्ञात error")
            print(f"\n{'='*50}")
            print(f"📧 DEV MODE — OTP for {to_email} ({purpose}): {otp}")
            print(f"   Error: {err}")
            print(f"{'='*50}\n")
            return False, f"इमेल पठाउन सकिएन: {err} (OTP terminal मा हेर्नुहोस्)"
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"📧 DEV MODE — OTP for {to_email} ({purpose}): {otp}")
        print(f"   Exception: {e}")
        print(f"{'='*50}\n")
        return False, f"इमेल error: {e} (OTP terminal मा हेर्नुहोस्)"


def login_page():

    # ============================================================
    # LANGUAGE SETUP — ⚠️ FIXED (login_lang युजरको छनोटलाई प्राथमिकता)
    # ============================================================
    available_languages = list(LANGUAGES.keys()) or ["en"]

    # ✅ पहिलो पटक मात्र ui_lang बाट sync
    if "login_lang" not in st.session_state:
        prev = st.session_state.get("ui_lang", "en")
        if prev in available_languages:
            st.session_state.login_lang = prev
        else:
            st.session_state.login_lang = "en" if "en" in available_languages else available_languages[0]

    # ✅ login_lang valid छ कि जाँच्ने (तर ओभरराइड नगर्ने)
    if st.session_state.login_lang not in available_languages:
        st.session_state.login_lang = "en" if "en" in available_languages else available_languages[0]

    # ============================================================
    # MODE STATE
    # ============================================================
    for key, val in {
        "login_mode": "login",
        "otp_email": "",
        "otp_purpose": "signup",
        "otp_sent": False,
        "pending_signup": None,
        "login_success_msg": None,
        "lang_save_warning": None,
        "otp_anim_key": 0,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # ============================================================
    # CSS + ANIMATION
    # ============================================================
    # CSS का लागि lang चाहिन्छ — युजरको छनोट अनुसार
    lang = st.session_state.login_lang
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))

    direction_css = """
        .stApp { direction: rtl; text-align: right; }
        .stTextInput input { direction: rtl !important; text-align: right !important; }
        .stMarkdown { text-align: right; }
    """ if lang == "ar" else """
        .stApp { direction: ltr; text-align: left; }
        .stTextInput input { direction: ltr !important; text-align: left !important; }
    """

    st.markdown(f"""
    <style>
        @keyframes gradientShift {{
            0%   {{ background-position: 0% 50%; }}
            50%  {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .stApp {{
            background: linear-gradient(-45deg, #0E1117, #1a1f2e, #0f1626, #141824);
            background-size: 400% 400%;
            animation: gradientShift 18s ease infinite;
            color: white;
            min-height: 100vh;
        }}
        .particle {{
            position: fixed;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(102,126,234,0.55), transparent 70%);
            pointer-events: none;
            animation: floatUp linear infinite;
            z-index: 0;
        }}
        @keyframes floatUp {{
            0%   {{ transform: translateY(100vh) scale(0.4); opacity: 0; }}
            10%  {{ opacity: 1; }}
            90%  {{ opacity: 1; }}
            100% {{ transform: translateY(-10vh) scale(1.2); opacity: 0; }}
        }}
        .p1 {{ width: 180px; height: 180px; left: 5%;  animation-duration: 22s; animation-delay: 0s; }}
        .p2 {{ width: 120px; height: 120px; left: 25%; animation-duration: 18s; animation-delay: 3s; }}
        .p3 {{ width: 220px; height: 220px; left: 55%; animation-duration: 26s; animation-delay: 1s; }}
        .p4 {{ width: 90px;  height: 90px;  left: 75%; animation-duration: 20s; animation-delay: 5s; }}
        .p5 {{ width: 150px; height: 150px; left: 90%; animation-duration: 24s; animation-delay: 2s; }}

        .glass-card {{
            background: rgba(30, 36, 52, 0.55);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 28px 26px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.06);
            margin-bottom: 18px;
            animation: cardIn 0.7s cubic-bezier(0.2, 0.8, 0.2, 1);
        }}
        @keyframes cardIn {{
            from {{ transform: translateY(18px) scale(0.98); opacity: 0; }}
            to   {{ transform: translateY(0)   scale(1);    opacity: 1; }}
        }}

        .brand-header {{
            display: flex; align-items: center; gap: 12px; margin-bottom: 6px;
            animation: brandFloat 4s ease-in-out infinite;
        }}
        @keyframes brandFloat {{
            0%,100% {{ transform: translateY(0); }}
            50%     {{ transform: translateY(-4px); }}
        }}
        .brand-title {{
            font-size: 26px; font-weight: 800; color: white; margin: 0;
            background: linear-gradient(90deg, #667eea, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shine 5s linear infinite;
            background-size: 200% auto;
        }}
        @keyframes shine {{
            to {{ background-position: 200% center; }}
        }}
        .brand-sub {{ font-size: 12px; color: #a0aabf; margin: 0; letter-spacing: 0.5px; }}

        .fade-slide {{
            animation: fadeSlide 0.6s ease-out both;
        }}
        @keyframes fadeSlide {{
            from {{ opacity: 0; transform: translateX(-14px); }}
            to   {{ opacity: 1; transform: translateX(0); }}
        }}

        /* GLASSMORPHISM INPUT FIELDS */
        .stTextInput > div > div > input {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1.5px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 14px !important;
            color: #ffffff !important;
            font-size: 0.95rem !important;
            padding: 14px 16px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow:
                inset 0 1px 2px rgba(255, 255, 255, 0.05),
                0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }}
        .stTextInput > div > div > input::placeholder {{
            color: rgba(255, 255, 255, 0.4) !important;
            font-style: italic !important;
        }}
        .stTextInput > div > div > input:focus {{
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: #667eea !important;
            box-shadow:
                0 0 0 4px rgba(102, 126, 234, 0.15),
                0 0 24px rgba(102, 126, 234, 0.4),
                inset 0 1px 2px rgba(255, 255, 255, 0.1) !important;
            transform: translateY(-2px) !important;
            outline: none !important;
        }}
        .stTextInput > div > div > input:hover:not(:focus) {{
            border-color: rgba(102, 126, 234, 0.5) !important;
            background: rgba(255, 255, 255, 0.07) !important;
        }}
        .stTextInput > label {{
            color: rgba(255, 255, 255, 0.85) !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.3px !important;
            margin-bottom: 6px !important;
            transition: all 0.2s ease !important;
        }}
        .stTextInput:focus-within > label {{
            color: #a78bfa !important;
            text-shadow: 0 0 12px rgba(167, 139, 250, 0.6) !important;
        }}
        .stTextInput > div > div > input[type="password"] {{
            letter-spacing: 2px !important;
            font-family: 'Courier New', monospace !important;
        }}

        .stCheckbox > label {{
            color: rgba(255, 255, 255, 0.8) !important;
            font-size: 0.9rem !important;
        }}

        .stButton>button {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            padding: 12px !important;
            width: 100% !important;
            border: none !important;
            letter-spacing: 0.3px;
            transition: transform 0.18s ease, box-shadow 0.25s ease, filter 0.2s ease !important;
            box-shadow: 0 4px 14px rgba(102,126,234,0.35) !important;
        }}
        .stButton>button::before {{
            content: "";
            position: absolute; top: 0; left: -120%;
            width: 60%; height: 100%;
            background: linear-gradient(120deg, transparent, rgba(255,255,255,0.35), transparent);
            transform: skewX(-20deg);
            animation: shimmer 3.2s infinite;
        }}
        @keyframes shimmer {{
            0%   {{ left: -120%; }}
            60%  {{ left: 130%; }}
            100% {{ left: 130%; }}
        }}
        .stButton>button:hover {{
            transform: translateY(-2px) scale(1.01);
            box-shadow: 0 10px 26px rgba(102,126,234,0.55), 0 0 0 3px rgba(102,126,234,0.18) !important;
            filter: brightness(1.08);
        }}
        .stButton>button:active {{
            transform: translateY(0) scale(0.99);
        }}

        @keyframes shake {{
            0%,100% {{ transform: translateX(0); }}
            20%     {{ transform: translateX(-8px); }}
            40%     {{ transform: translateX(8px); }}
            60%     {{ transform: translateX(-5px); }}
            80%     {{ transform: translateX(5px); }}
        }}
        .otp-error-shake {{
            animation: shake 0.5s ease-in-out;
            border-color: #ff4b4b !important;
            box-shadow: 0 0 0 4px rgba(255,75,75,0.18) !important;
        }}

        .confetti-wrap {{
            position: fixed; inset: 0; pointer-events: none; z-index: 9999; overflow: hidden;
        }}
        .confetti {{
            position: absolute; width: 10px; height: 10px; top: -20px;
            opacity: 0.9; border-radius: 2px;
            animation: confettiFall linear forwards;
        }}
        @keyframes confettiFall {{
            0%   {{ transform: translateY(-20px) rotate(0deg); opacity: 1; }}
            100% {{ transform: translateY(105vh) rotate(720deg); opacity: 0; }}
        }}

        .pulse-dot {{
            display: inline-block; width: 9px; height: 9px; border-radius: 50%;
            background: #31a24c; margin-right: 6px;
            animation: pulseDot 1.6s infinite;
        }}
        @keyframes pulseDot {{
            0%   {{ box-shadow: 0 0 0 0 rgba(49,162,76,0.7); }}
            70%  {{ box-shadow: 0 0 0 9px rgba(49,162,76,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(49,162,76,0); }}
        }}

        @media (max-width: 768px) {{
            .glass-card {{ padding: 20px 16px; border-radius: 18px; }}
            .brand-title {{ font-size: 22px; }}
        }}

        {direction_css}
    </style>
    """, unsafe_allow_html=True)

    # Floating particles
    st.markdown("""
    <div class="particle p1"></div>
    <div class="particle p2"></div>
    <div class="particle p3"></div>
    <div class="particle p4"></div>
    <div class="particle p5"></div>
    """, unsafe_allow_html=True)

    # ============================================================
    # HEADER + LANGUAGE SELECTOR
    # ============================================================
    col_logo, col_lang = st.columns([3, 1])

    with col_logo:
        st.markdown("""
        <div class="brand-header">
            <div style="font-size: 32px;">🧠</div>
            <div>
                <p class="brand-title">PDF Brain</p>
                <p class="brand-sub"><span class="pulse-dot"></span>AI Knowledge Platform</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_lang:
        # ✅ index हटाइयो — key बाट मात्र state नियन्त्रण
        selected_lang = st.selectbox(
            "Language",
            available_languages,
            format_func=lambda x: LANGUAGES.get(x, x),
            key="login_language_selector",
            label_visibility="collapsed"
        )
        # ✅ युजरले बदल्यो भने login_lang update + rerun
        if selected_lang != st.session_state.login_lang:
            st.session_state.login_lang = selected_lang
            st.rerun()

    # ✅ T refresh — selectbox PACHI (यही महत्त्वपूर्ण!)
    lang = st.session_state.login_lang
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))

    # ============================================================
    # HEADER TEXT
    # ============================================================
    st.markdown(
        f"<h2 class='fade-slide' style='text-align:center;color:white;"
        f"margin-top:14px;font-weight:800;'>{T.get('welcome', 'Welcome')}</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p class='fade-slide' style='text-align:center;color:#a0aabf;"
        f"margin-bottom:24px;'>{T.get('subtitle', 'AI Knowledge Platform')}</p>",
        unsafe_allow_html=True
    )

    # Success / warning messages
    if st.session_state.get("login_success_msg"):
        st.success(st.session_state.login_success_msg)
        st.session_state.login_success_msg = None
        st.markdown("""
        <div class="confetti-wrap">
            <div class="confetti" style="left:10%; background:#667eea; animation-duration:2.4s; animation-delay:0s;"></div>
            <div class="confetti" style="left:25%; background:#f472b6; animation-duration:2.8s; animation-delay:0.2s;"></div>
            <div class="confetti" style="left:40%; background:#34d399; animation-duration:2.2s; animation-delay:0.4s;"></div>
            <div class="confetti" style="left:55%; background:#fbbf24; animation-duration:2.6s; animation-delay:0.1s;"></div>
            <div class="confetti" style="left:70%; background:#a78bfa; animation-duration:2.5s; animation-delay:0.3s;"></div>
            <div class="confetti" style="left:85%; background:#38bdf8; animation-duration:2.7s; animation-delay:0.15s;"></div>
            <div class="confetti" style="left:50%; background:#fb7185; animation-duration:2.3s; animation-delay:0.5s;"></div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("lang_save_warning"):
        st.warning(st.session_state.lang_save_warning)
        st.session_state.lang_save_warning = None

    # ============================================================
    # MODE 1: LOGIN
    # ============================================================
    if st.session_state.login_mode == "login":

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown(
                f"<h3 class='fade-slide' style='color:white;margin-top:0;'>"
                f"{T.get('signin_title', 'Sign In')}</h3>",
                unsafe_allow_html=True
            )

            username = st.text_input(
                "👤 " + T.get("username", "Username"),
                placeholder=T.get("username_ph", "Enter your username")
            )
            password = st.text_input(
                "🔑 " + T.get("password", "Password"),
                type="password",
                placeholder=T.get("password_ph", "Enter your password")
            )
            remember = st.checkbox(T.get("remember", "Remember me"))

            submit = st.form_submit_button(
                T.get("signin_btn", "🔐 Sign In"),
                type="primary"
            )

            if submit:
                if not username or not password:
                    st.error(T.get("error_fill", "Please fill all fields."))
                else:
                    ok, user = verify_user(username.strip(), password)

                    if ok and user:
                        if isinstance(user, dict):
                            login_username = user.get("username", username.strip())
                            user_role = user.get("role", "user")
                        else:
                            login_username = username.strip()
                            user_role = "user"

                        st.session_state.user = login_username
                        st.session_state.user_role = user_role
                        st.session_state.logged_in = True
                        st.session_state.ui_lang = st.session_state.login_lang

                        if remember:
                            st.session_state.remember_token = True

                        try:
                            update_user_language(login_username, st.session_state.login_lang)
                        except Exception as e:
                            st.session_state.lang_save_warning = (
                                f"{T.get('lang_save_fail', 'Language preference could not be saved')}: {e}"
                            )

                        st.rerun()
                    else:
                        st.error(T.get("error_wrong", "Invalid username or password."))

        st.markdown('</div>', unsafe_allow_html=True)

        # Form बाहिर — Forgot Password
        col_f, col_s = st.columns(2)
        with col_f:
            if st.button(T.get("forgot_password", "Forgot Password?"), use_container_width=True, key="forgot_btn"):
                st.session_state.login_mode = "forgot"
                st.session_state.otp_sent = False
                st.rerun()
        with col_s:
            if st.button(f"👉 {T.get('new_user', 'Create Account')}", use_container_width=True, key="signup_btn"):
                st.session_state.login_mode = "signup"
                st.session_state.otp_sent = False
                st.rerun()

    # ============================================================
    # MODE 2: SIGN UP
    # ============================================================
    elif st.session_state.login_mode == "signup":

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        st.markdown(
            f"<h3 class='fade-slide' style='color:white;margin-top:0;'>"
            f"{T.get('signup_title', 'Create New Account')}</h3>",
            unsafe_allow_html=True
        )

        if not st.session_state.otp_sent:
            with st.form("signup_form"):
                new_user = st.text_input("👤 " + T.get("username", "Username"))
                new_email = st.text_input("📧 Email")
                new_pass = st.text_input("🔑 " + T.get("password", "Password"), type="password")
                new_pass2 = st.text_input("🔑 " + T.get("confirm_password", "Confirm Password"), type="password")

                send_otp = st.form_submit_button(
                    T.get("send_otp", "📧 Send OTP"),
                    type="primary"
                )

                if send_otp:
                    if not new_user or not new_pass or not new_email:
                        st.error(T.get("fill_all", "कृपया सबै फिल्ड भर्नुहोस्।"))
                    elif not re.match(EMAIL_PATTERN, new_email.strip()):
                        st.error(T.get("email_invalid", "कृपया सही Email भर्नुहोस्।"))
                    elif new_pass != new_pass2:
                        st.error(T.get("pass_mismatch", "Password मिलेन।"))
                    elif len(new_pass) < 6:
                        st.error(T.get("pass_short", "Password कम्तिमा ६ अक्षर हुनुपर्छ।"))
                    elif user_exists_by_email(new_email.strip()):
                        st.error(T.get("account_exists", "यो Email पहिले नै दर्ता छ।"))
                    else:
                        otp = generate_otp(new_email.strip(), purpose="signup")
                        ok_send, msg = send_otp_email(
                            new_email.strip(), otp,
                            purpose="signup", lang=lang
                        )

                        if ok_send:
                            st.session_state.otp_email = new_email.strip()
                            st.session_state.otp_purpose = "signup"
                            st.session_state.otp_sent = True
                            st.session_state.pending_signup = {
                                "username": new_user.strip(),
                                "email": new_email.strip(),
                                "password": new_pass,
                            }
                            st.success(T.get("otp_sent", "OTP इमेलमा पठाइयो।"))
                            st.rerun()
                        else:
                            st.error(f"{T.get('otp_send_fail', 'OTP पठाउन सकिएन।')} {msg}")

            if st.button(T.get("back_login", "⬅️ Back to Login"), key="back_from_signup"):
                st.session_state.login_mode = "login"
                st.rerun()

        else:
            st.info(f"📧 {T.get('otp_sent_to', 'OTP पठाइयो')}: **{st.session_state.otp_email}**")

            with st.form("otp_verify_form"):
                entered = st.text_input(
                    "🔢 " + T.get("otp_enter", "इमेलमा आएको ६ अंकको OTP हाल्नुहोस्"),
                    max_chars=6,
                    placeholder="• • • • • •"
                )
                verify_btn = st.form_submit_button(
                    T.get("otp_verify", "✅ Verify गर्नुहोस्"),
                    type="primary"
                )

                if verify_btn:
                    ok_v, msg_v = verify_otp(st.session_state.otp_email, entered)
                    if ok_v:
                        signup = st.session_state.pending_signup or {}
                        try:
                            ok_c, msg_c = create_user(
                                signup.get("username", ""),
                                signup.get("password", ""),
                                signup.get("email", ""),
                                preferred_language=st.session_state.login_lang
                            )
                            if ok_c:
                                clear_otp(st.session_state.otp_email)
                                st.session_state.login_success_msg = T.get(
                                    "signup_success", "✅ Account बन्यो! अब Login गर्नुहोस्।"
                                )
                                st.session_state.login_mode = "login"
                                st.session_state.otp_sent = False
                                st.session_state.pending_signup = None
                                st.rerun()
                            else:
                                st.error(f"❌ {msg_c}")
                        except Exception as e:
                            st.error(f"❌ {T.get('account_error', 'Account creation error')}: {e}")
                    else:
                        st.session_state.otp_anim_key += 1
                        st.error(f"❌ {msg_v}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(T.get("otp_resend", "🔄 OTP पुनः पठाउनुहोस्"), use_container_width=True, key="resend_otp"):
                    otp = generate_otp(st.session_state.otp_email, purpose="signup")
                    ok_s, msg_s = send_otp_email(
                        st.session_state.otp_email, otp,
                        purpose="signup", lang=lang
                    )
                    if ok_s:
                        st.success(T.get("otp_sent", "OTP इमेलमा पठाइयो।"))
                    else:
                        st.error(f"{T.get('otp_send_fail', 'OTP पठाउन सकिएन।')} {msg_s}")
            with col_b:
                if st.button(T.get("otp_back", "⬅️ पछाडि जानुहोस्"), use_container_width=True, key="back_otp"):
                    st.session_state.otp_sent = False
                    st.session_state.pending_signup = None
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ============================================================
    # MODE 3: FORGOT PASSWORD
    # ============================================================
    elif st.session_state.login_mode == "forgot":

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        st.markdown(
            f"<h3 class='fade-slide' style='color:white;margin-top:0;'>"
            f"{T.get('forgot_title', 'Forgot Password')}</h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:#a0aabf;'>{T.get('forgot_hint', 'तपाईंको इमेल हाल्नुहोस्, हामी OTP पठाउनेछौं।')}</p>",
            unsafe_allow_html=True
        )

        if not st.session_state.otp_sent:
            with st.form("forgot_form"):
                forgot_email = st.text_input("📧 Email")
                send_btn = st.form_submit_button(
                    T.get("send_otp", "📧 OTP पठाउनुहोस्"),
                    type="primary"
                )

                if send_btn:
                    if not forgot_email:
                        st.error(T.get("email_required", "Email भर्नुहोस्।"))
                    elif not re.match(EMAIL_PATTERN, forgot_email.strip()):
                        st.error(T.get("email_invalid", "कृपया सही Email भर्नुहोस्।"))
                    elif not user_exists_by_email(forgot_email.strip()):
                        st.error(T.get("account_not_found", "यो Email दर्ता छैन। पहिले Signup गर्नुहोस्।"))
                    else:
                        otp = generate_otp(forgot_email.strip(), purpose="reset")
                        ok_s, msg_s = send_otp_email(
                            forgot_email.strip(), otp,
                            purpose="reset", lang=lang
                        )

                        if ok_s:
                            st.session_state.otp_email = forgot_email.strip()
                            st.session_state.otp_purpose = "reset"
                            st.session_state.otp_sent = True
                            st.success(T.get("otp_sent", "OTP इमेलमा पठाइयो।"))
                            st.rerun()
                        else:
                            st.error(f"{T.get('otp_send_fail', 'OTP पठाउन सकिएन।')} {msg_s}")

            if st.button(T.get("back_login", "⬅️ Back to Login"), key="back_from_forgot"):
                st.session_state.login_mode = "login"
                st.rerun()

        else:
            st.info(f"📧 {T.get('otp_sent_to', 'OTP पठाइयो')}: **{st.session_state.otp_email}**")

            with st.form("reset_form"):
                entered_otp = st.text_input(
                    "🔢 " + T.get("otp_enter", "इमेलमा आएको ६ अंकको OTP हाल्नुहोस्"),
                    max_chars=6,
                    placeholder="• • • • • •"
                )
                new_pass = st.text_input(
                    "🔑 " + T.get("reset_new_pass", "नयाँ Password"), type="password"
                )
                new_pass2 = st.text_input(
                    "🔑 " + T.get("reset_confirm_pass", "नयाँ Password पुष्टि गर्नुहोस्"), type="password"
                )
                reset_btn = st.form_submit_button(
                    T.get("reset_btn", "🔐 Password Reset गर्नुहोस्"),
                    type="primary"
                )

                if reset_btn:
                    if not entered_otp or not new_pass or not new_pass2:
                        st.error(T.get("fill_all", "कृपया सबै फिल्ड भर्नुहोस्।"))
                    elif new_pass != new_pass2:
                        st.error(T.get("pass_mismatch", "Password मिलेन।"))
                    elif len(new_pass) < 6:
                        st.error(T.get("pass_short", "Password कम्तिमा ६ अक्षर हुनुपर्छ।"))
                    else:
                        ok_v, msg_v = verify_otp(st.session_state.otp_email, entered_otp)
                        if ok_v:
                            try:
                                ok_r, msg_r = update_user_password(
                                    st.session_state.otp_email, new_pass
                                )
                                if ok_r:
                                    clear_otp(st.session_state.otp_email)
                                    st.session_state.login_success_msg = T.get(
                                        "reset_success", "✅ Password सफलतापूर्वक बदलियो! अब Login गर्नुहोस्।"
                                    )
                                    st.session_state.login_mode = "login"
                                    st.session_state.otp_sent = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg_r}")
                            except Exception as e:
                                st.error(f"❌ {T.get('reset_error', 'Password reset error')}: {e}")
                        else:
                            st.session_state.otp_anim_key += 1
                            st.error(f"❌ {msg_v}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(T.get("otp_resend", "🔄 OTP पुनः पठाउनुहोस्"), use_container_width=True, key="resend_reset_otp"):
                    otp = generate_otp(st.session_state.otp_email, purpose="reset")
                    ok_s, msg_s = send_otp_email(
                        st.session_state.otp_email, otp,
                        purpose="reset", lang=lang
                    )
                    if ok_s:
                        st.success(T.get("otp_sent", "OTP इमेलमा पठाइयो।"))
                    else:
                        st.error(f"{T.get('otp_send_fail', 'OTP पठाउन सकिएन।')} {msg_s}")
            with col_b:
                if st.button(T.get("otp_back", "⬅️ पछाडि जानुहोस्"), use_container_width=True, key="back_reset_otp"):
                    st.session_state.otp_sent = False
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ============================================================
    # FOOTER
    # ============================================================
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"🛡️<br>{T.get('secure', 'Secure')}</p>", unsafe_allow_html=True
    )
    c2.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"🧠<br>{T.get('ai', 'AI Powered')}</p>", unsafe_allow_html=True
    )
    c3.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"💾<br>{T.get('memory', 'Smart Memory')}</p>", unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center;color:#667eea;font-size:12px;margin-top:20px;'>"
        f"{T.get('footer', 'PDF Brain - AI Knowledge Platform')}</p>",
        unsafe_allow_html=True
    )