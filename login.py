# login.py — PDF Brain (Powerful Login System v5)
import streamlit as st
import time
from datetime import datetime
from auth import verify_user, create_user

try:
    from security import is_locked_out, record_failed_login, reset_failed_login, log_action
except ImportError:
    def is_locked_out(u): return False, None
    def record_failed_login(u): pass
    def reset_failed_login(u): pass
    def log_action(*a, **k): pass


def check_password_strength(password):
    score = 0
    feedback = []
    if len(password) >= 8: score += 1
    else: feedback.append("८+ अक्षर")
    if any(c.isupper() for c in password): score += 1
    else: feedback.append("ठूलो अक्षर")
    if any(c.islower() for c in password): score += 1
    else: feedback.append("सानो अक्षर")
    if any(c.isdigit() for c in password): score += 1
    else: feedback.append("अंक")
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): score += 1
    else: feedback.append("विशेष चिन्ह")
    return score, feedback


def login_page():
    """Powerful Login Page — compact + language + auto-scroll"""

    # ============================================================
    # CSS (compact spacing)
    # ============================================================
    st.markdown("""
    <style>
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }

        /* ✅ Page compact — सबै माथि */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            max-width: 1000px !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.4rem !important;
        }
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            gap: 0.3rem !important;
        }
        .stTextInput {
            margin-bottom: 0.3rem !important;
        }
        .stCheckbox {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        .login-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin: 0 0 2px 0;
            letter-spacing: -1px;
        }
        .login-sub {
            text-align: center;
            color: #6b7280;
            margin: 0 0 12px 0;
            font-size: 0.9em;
        }
        .login-footer {
            text-align: center;
            color: #9ca3af;
            font-size: 0.8em;
            margin-top: 12px;
        }
        .strength-bar {
            height: 6px;
            border-radius: 3px;
            margin-top: 3px;
            transition: all 0.3s ease;
        }
        .strength-weak { background: linear-gradient(90deg, #ef4444, #f87171); width: 25%; }
        .strength-fair { background: linear-gradient(90deg, #f59e0b, #fbbf24); width: 50%; }
        .strength-good { background: linear-gradient(90deg, #3b82f6, #60a5fa); width: 75%; }
        .strength-strong { background: linear-gradient(90deg, #10b981, #34d399); width: 100%; }

        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
            gap: 6px;
            background: #f3f4f6;
            padding: 4px;
            border-radius: 10px;
            margin-bottom: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85em;
            padding: 5px 10px;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
        }

        .stButton > button[kind="primary"],
        .stButton > button[kind="primaryFormSubmit"] {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            border: none !important;
            font-weight: 700 !important;
            padding: 9px !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
            transition: all 0.2s !important;
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[kind="primaryFormSubmit"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
        }

        .stTextInput input {
            border-radius: 10px !important;
            border: 1.5px solid #e5e7eb !important;
            padding: 9px 12px !important;
            font-size: 0.95em !important;
        }
        .stTextInput input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        }

        .security-badge {
            display: inline-block;
            background: linear-gradient(135deg, #d1fae5, #a7f3d0);
            color: #065f46;
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 0.72em;
            font-weight: 700;
            margin: 6px 0;
        }

        .forgot-link {
            text-align: right;
            font-size: 0.75em;
            color: #667eea;
            margin: 0 0 6px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # TRANSLATIONS
    # ============================================================
    TRANSLATIONS = {
        "ne": {
            "title": "🧠 PDF Brain",
            "subtitle": "AI-Powered Document Intelligence",
            "login_tab": "🔐 Login", "signup_tab": "📝 Sign Up", "forgot_tab": "🔑 Forgot Password",
            "username": "👤 Username", "password": "🔑 Password",
            "login_btn": "🔓 Login", "remember": "🕐 Remember me (30 days)",
            "forgot_hint": "🔑 Forgot password? → Use 'Forgot' tab",
            "login_error": "❌ गलत Username वा Password",
            "fill_both": "⚠️ Username र Password भर्नुहोस्",
            "new_username": "👤 नयाँ Username", "new_email": "📧 Email (optional)",
            "new_password": "🔑 Password", "confirm_password": "🔑 Confirm Password",
            "signup_btn": "📝 Sign Up", "password_mismatch": "❌ Password मिलेन",
            "password_short": "❌ Password कम्तिमा ८ अक्षर",
            "username_short": "❌ Username कम्तिमा ३ अक्षर",
            "reset_title": "### 🔑 Password Reset",
            "reset_caption": "तपाईंको इमेलमा ६-अंकको code पठाइनेछ",
            "email_label": "📧 तपाईंको Email", "send_otp_btn": "📧 OTP Code पठाउनुहोस्",
            "otp_sent": "✅ OTP code पठाइयो! इमेल जाँच्नुहोस्।",
            "otp_input": "🔢 OTP Code", "new_pass_label": "🔑 नयाँ Password",
            "confirm_pass_label": "🔑 Confirm Password", "reset_btn": "✅ Password Reset",
            "resend_otp": "🔄 नयाँ Code पठाउनुहोस्",
            "footer": "🧠 PDF Brain v52.0 · Made with ❤️ in Nepal",
            "brute_force": "🔐 Brute-force Protection Active",
            "default_admin": "🔑 Default Admin Credentials",
            "change_password": "⚠️ पहिलो login पछि password फेर्नुहोस्।",
        },
        "en": {
            "title": "🧠 PDF Brain",
            "subtitle": "AI-Powered Document Intelligence",
            "login_tab": "🔐 Login", "signup_tab": "📝 Sign Up", "forgot_tab": "🔑 Forgot Password",
            "username": "👤 Username", "password": "🔑 Password",
            "login_btn": "🔓 Login", "remember": "🕐 Remember me (30 days)",
            "forgot_hint": "🔑 Forgot password? → Use 'Forgot' tab",
            "login_error": "❌ Wrong Username or Password",
            "fill_both": "⚠️ Please fill Username and Password",
            "new_username": "👤 New Username", "new_email": "📧 Email (optional)",
            "new_password": "🔑 Password", "confirm_password": "🔑 Confirm Password",
            "signup_btn": "📝 Sign Up", "password_mismatch": "❌ Passwords don't match",
            "password_short": "❌ Password must be at least 8 characters",
            "username_short": "❌ Username must be at least 3 characters",
            "reset_title": "### 🔑 Password Reset",
            "reset_caption": "A 6-digit code will be sent to your email",
            "email_label": "📧 Your Email", "send_otp_btn": "📧 Send OTP Code",
            "otp_sent": "✅ OTP code sent! Check your email.",
            "otp_input": "🔢 OTP Code", "new_pass_label": "🔑 New Password",
            "confirm_pass_label": "🔑 Confirm Password", "reset_btn": "✅ Password Reset",
            "resend_otp": "🔄 Resend Code",
            "footer": "🧠 PDF Brain v52.0 · Made with ❤️ in Nepal",
            "brute_force": "🔐 Brute-force Protection Active",
            "default_admin": "🔑 Default Admin Credentials",
            "change_password": "⚠️ Change password after first login.",
        },
        "hi": {
            "title": "🧠 PDF Brain",
            "subtitle": "AI-Powered Document Intelligence",
            "login_tab": "🔐 Login", "signup_tab": "📝 Sign Up", "forgot_tab": "🔑 Forgot Password",
            "username": "👤 Username", "password": "🔑 Password",
            "login_btn": "🔓 Login", "remember": "🕐 Remember me (30 days)",
            "forgot_hint": "🔑 Forgot password? → Use 'Forgot' tab",
            "login_error": "❌ गलत Username या Password",
            "fill_both": "⚠️ Username और Password भरें",
            "new_username": "👤 नया Username", "new_email": "📧 Email (optional)",
            "new_password": "🔑 Password", "confirm_password": "🔑 Confirm Password",
            "signup_btn": "📝 Sign Up", "password_mismatch": "❌ Password मिलेन",
            "password_short": "❌ Password कम से कम ८ अक्षर",
            "username_short": "❌ Username कम से कम ३ अक्षर",
            "reset_title": "### 🔑 Password Reset",
            "reset_caption": "आपके ईमेल पर ६-अंक का कोड भेजा जाएगा",
            "email_label": "📧 आपका Email", "send_otp_btn": "📧 OTP Code भेजें",
            "otp_sent": "✅ OTP code भेजा गया! ईमेल जांचें।",
            "otp_input": "🔢 OTP Code", "new_pass_label": "🔑 नया Password",
            "confirm_pass_label": "🔑 Confirm Password", "reset_btn": "✅ Password Reset",
            "resend_otp": "🔄 नया Code भेजें",
            "footer": "🧠 PDF Brain v52.0 · Made with ❤️ in Nepal",
            "brute_force": "🔐 Brute-force Protection Active",
            "default_admin": "🔑 Default Admin Credentials",
            "change_password": "⚠️ पहिलो login के बाद password बदलें।",
        },
    }

    if "login_lang" not in st.session_state:
        st.session_state.login_lang = "ne"
    lang_key = st.session_state.login_lang
    T = TRANSLATIONS.get(lang_key, TRANSLATIONS["ne"])

    # ============================================================
    # ✅ HEADER + LANGUAGE (PDF Brain को दायाँ साइडमा)
    # ============================================================
    head_col1, head_col2 = st.columns([4, 1])

    with head_col1:
        st.markdown(f'<h1 class="login-title">{T["title"]}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="login-sub">{T["subtitle"]}</p>', unsafe_allow_html=True)

    with head_col2:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        lang_map = {"🇳🇵": "ne", "🇬🇧": "en", "🇮🇳": "hi"}
        lang_keys = list(lang_map.keys())
        lang_vals = list(lang_map.values())
        current_idx = lang_vals.index(st.session_state.login_lang) if st.session_state.login_lang in lang_vals else 0

        selected_flag = st.selectbox(
            "🌐",
            lang_keys,
            index=current_idx,
            key="login_lang_select",
            label_visibility="collapsed"
        )
        new_lang = lang_map[selected_flag]
        if new_lang != st.session_state.login_lang:
            st.session_state.login_lang = new_lang
            st.rerun()

    # ============================================================
    # LAYOUT (compact)
    # ============================================================
    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        tab_login, tab_signup, tab_forgot = st.tabs([
            T["login_tab"], T["signup_tab"], T["forgot_tab"]
        ])

        # ============================================================
        # TAB 1: LOGIN
        # ============================================================
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    T["username"], placeholder="admin", key="login_user"
                )
                password = st.text_input(
                    T["password"], type="password", placeholder="••••••••", key="login_pass"
                )

                # ✅ Login button password पछि तुरुन्तै
                submit = st.form_submit_button(
                    T["login_btn"], use_container_width=True, type="primary"
                )

                remember = st.checkbox(T["remember"], key="remember_me")

                st.markdown(
                    f'<p class="forgot-link">{T["forgot_hint"]}</p>',
                    unsafe_allow_html=True
                )

                if submit:
                    if not username or not password:
                        st.error(T["fill_both"])
                    else:
                        locked, until = is_locked_out(username)
                        if locked:
                            st.error(f"🔒 Account locked until {until.strftime('%H:%M')}")
                        else:
                            ok, user = verify_user(username, password)
                            if ok:
                                st.session_state.user = username
                                st.session_state.user_role = user.get("role", "user") if isinstance(user, dict) else "user"
                                st.session_state.user_email = user.get("email", "") if isinstance(user, dict) else ""
                                st.session_state.login_time = datetime.now().isoformat()
                                st.session_state.logged_in = True
                                st.session_state.ui_lang = st.session_state.login_lang

                                if remember:
                                    st.session_state.remember_until = (
                                        datetime.now().replace(hour=23, minute=59, second=59)
                                    ).isoformat()

                                reset_failed_login(username)
                                log_action(username, "LOGIN", status="success")
                                st.rerun()
                            else:
                                record_failed_login(username)
                                log_action(username, "LOGIN_FAILED", status="failed")
                                st.error(T["login_error"])

            st.markdown("---")
            st.markdown(f"""<div class="security-badge">{T["brute_force"]}</div>""", unsafe_allow_html=True)

            with st.expander(T["default_admin"]):
                st.code("Username: admin\nPassword: admin123", language=None)
                st.caption(T["change_password"])

        # ============================================================
        # TAB 2: SIGN UP
        # ============================================================
        with tab_signup:
            with st.form("signup_form", clear_on_submit=False):
                new_user = st.text_input(T["new_username"], placeholder="ramesh", key="signup_user")
                new_email = st.text_input(T["new_email"], placeholder="ramesh@example.com", key="signup_email")
                new_pass = st.text_input(T["new_password"], type="password", key="signup_pass")
                new_pass2 = st.text_input(T["confirm_password"], type="password", key="signup_pass2")

                if new_pass:
                    score, feedback = check_password_strength(new_pass)
                    if score <= 2:
                        cls, label = "strength-weak", "🔴 कमजोर"
                    elif score == 3:
                        cls, label = "strength-fair", "🟠 ठीक"
                    elif score == 4:
                        cls, label = "strength-good", "🔵 राम्रो"
                    else:
                        cls, label = "strength-strong", "🟢 बलियो"

                    st.markdown(
                        f'<div class="strength-bar {cls}"></div>'
                        f'<p style="font-size:0.75em; color:#6b7280; margin-top:2px;">'
                        f'Password: {label} '
                        f'{"✓ ".join(feedback[:2]) if feedback else "✅"}</p>',
                        unsafe_allow_html=True
                    )

                submit2 = st.form_submit_button(T["signup_btn"], use_container_width=True, type="primary")

                if submit2:
                    if not new_user or not new_pass:
                        st.error(T["fill_both"])
                    elif new_pass != new_pass2:
                        st.error(T["password_mismatch"])
                    elif len(new_pass) < 8:
                        st.error(T["password_short"])
                    elif len(new_user) < 3:
                        st.error(T["username_short"])
                    else:
                        ok, msg = create_user(new_user, new_pass, new_email)
                        if ok:
                            log_action(new_user, "SIGNUP", status="success")
                            st.success(f"✅ {msg}!")
                            st.balloons()
                            st.info("अब Login tab बाट login गर्नुहोस्।")
                        else:
                            st.error(f"❌ {msg}")

        # ============================================================
        # TAB 3: FORGOT PASSWORD (OTP)
        # ============================================================
        with tab_forgot:
            try:
                from auth import find_user_by_email, generate_otp, reset_password_with_otp
                from email_helper import send_otp_email
                otp_available = True
            except ImportError:
                otp_available = False

            if not otp_available:
                st.error("⚠️ OTP system configure भएको छैन")
            else:
                if "otp_sent" not in st.session_state:
                    st.session_state.otp_sent = False
                if "otp_username" not in st.session_state:
                    st.session_state.otp_username = None

                if not st.session_state.otp_sent:
                    st.markdown(T["reset_title"])
                    st.caption(T["reset_caption"])

                    with st.form("forgot_form"):
                        forgot_email = st.text_input(T["email_label"], placeholder="ramesh@example.com", key="forgot_email")
                        submit3 = st.form_submit_button(T["send_otp_btn"], use_container_width=True, type="primary")

                        if submit3:
                            if not forgot_email:
                                st.error("⚠️ Email भर्नुहोस्")
                            else:
                                username = find_user_by_email(forgot_email)
                                if not username:
                                    st.info("📧 यदि यो इमेल दर्ता छ भने, code पठाइनेछ।")
                                else:
                                    otp_code, msg = generate_otp(username, forgot_email)
                                    if otp_code:
                                        with st.spinner("📧 Email पठाउँदै..."):
                                            result = send_otp_email(forgot_email, otp_code, username)

                                        if result["success"]:
                                            st.session_state.otp_sent = True
                                            st.session_state.otp_username = username
                                            st.success(T["otp_sent"])
                                            st.info(f"🔢 **Dev mode:** `{otp_code}`")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Email पठाउन असफल: {result['error']}")
                                    else:
                                        st.error(f"❌ {msg}")

                else:
                    st.success(f"📧 **{st.session_state.otp_username}** को इमेलमा code पठाइयो!")
                    st.info("📬 इमेलमा आएको ६-अंकको code तल हाल्नुहोस्")

                    with st.form("otp_reset_form"):
                        otp_input = st.text_input(T["otp_input"], placeholder="123456", max_chars=6, key="otp_input")
                        new_pass = st.text_input(T["new_pass_label"], type="password", key="otp_new_pass")
                        new_pass2 = st.text_input(T["confirm_pass_label"], type="password", key="otp_new_pass2")
                        submit_reset = st.form_submit_button(T["reset_btn"], use_container_width=True, type="primary")

                        if submit_reset:
                            if not otp_input or not new_pass or not new_pass2:
                                st.error("⚠️ सबै field भर्नुहोस्")
                            elif new_pass != new_pass2:
                                st.error(T["password_mismatch"])
                            elif len(new_pass) < 6:
                                st.error("❌ Password कम्तिमा ६ अक्षर")
                            else:
                                ok, msg = reset_password_with_otp(st.session_state.otp_username, otp_input, new_pass)
                                if ok:
                                    st.success(f"✅ {msg}")
                                    st.balloons()
                                    st.info("अब login गर्नुहोस्।")
                                    time.sleep(2)
                                    st.session_state.otp_sent = False
                                    st.session_state.otp_username = None
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")

                    if st.button(T["resend_otp"], key="resend_otp", use_container_width=True):
                        st.session_state.otp_sent = False
                        st.session_state.otp_username = None
                        st.rerun()

        # ============================================================
        # FOOTER
        # ============================================================
        st.markdown(f'<p class="login-footer">{T["footer"]}</p>', unsafe_allow_html=True)

    # ============================================================
    # ✅ AUTO-SCROLL (Username → Password)
    # ============================================================
    st.markdown("""
    <script>
    (function() {
        function setup() {
            const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
            if (inputs.length < 2) return;

            // पहिलो input (username) मा Enter → password मा focus
            inputs.forEach(function(inp, idx) {
                inp.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        if (idx < inputs.length - 1) {
                            inputs[idx + 1].focus();
                        }
                    }
                });
            });
        }
        // DOM ready पछि setup
        setTimeout(setup, 500);
        setTimeout(setup, 1500);
    })();
    </script>
    """, unsafe_allow_html=True)