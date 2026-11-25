
# login.py
import streamlit as st
import time

from auth import (
    verify_user,
    create_user,
    update_user_language
)

from translations import LANGUAGES, TRANSLATIONS


def login_page():

    # ============================================================
    # LANGUAGE SETUP
    # ============================================================

    available_languages = list(LANGUAGES.keys())

    if not available_languages:
        available_languages = ["en"]

    if "login_lang" not in st.session_state:
        previous_lang = st.session_state.get("ui_lang", "en")

        if previous_lang in available_languages:
            st.session_state.login_lang = previous_lang
        else:
            st.session_state.login_lang = "en" if "en" in available_languages else available_languages[0]

    if st.session_state.login_lang not in available_languages:
        st.session_state.login_lang = "en" if "en" in available_languages else available_languages[0]

    lang = st.session_state.login_lang
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))

    # ============================================================
    # MODE STATE
    # ============================================================

    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "login"

    # ============================================================
    # DARK THEME + RTL SUPPORT
    # ============================================================

    if lang == "ar":
        direction_css = """
            .stApp {
                direction: rtl;
                text-align: right;
            }
            .stTextInput input {
                direction: rtl !important;
                text-align: right !important;
            }
            .stMarkdown {
                text-align: right;
            }
        """
    else:
        direction_css = """
            .stApp {
                direction: ltr;
                text-align: left;
            }
            .stTextInput input {
                direction: ltr !important;
                text-align: left !important;
            }
        """

    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #0E1117;
            color: white;
        }}

        .brand-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }}

        .brand-title {{
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin: 0;
        }}

        .brand-sub {{
            font-size: 12px;
            color: #a0aabf;
            margin: 0;
        }}

        .stTextInput>div>div>input {{
            background-color: #212937 !important;
            color: white !important;
            border: 1px solid #323d4e !important;
            border-radius: 10px !important;
        }}

        .stButton>button {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            padding: 10px !important;
            width: 100% !important;
            border: none !important;
        }}

        .link-btn {{
            text-align: center;
            margin-top: 10px;
        }}

        {direction_css}
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # HEADER + LANGUAGE SELECTOR
    # ============================================================

    col_logo, col_lang = st.columns([3, 1])

    with col_logo:
        st.markdown("""
        <div class="brand-header">
            <div style="font-size: 30px;">🧠</div>
            <div>
                <p class="brand-title">PDF Brain</p>
                <p class="brand-sub">AI Knowledge Platform</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_lang:

        selected_lang = st.selectbox(
            "Language",
            available_languages,
            format_func=lambda x: LANGUAGES.get(x, x),
            index=available_languages.index(st.session_state.login_lang),
            key="login_language_selector",
            label_visibility="collapsed"
        )

        if selected_lang != st.session_state.login_lang:
            st.session_state.login_lang = selected_lang
            st.rerun()

    # Refresh translation after language selection
    lang = st.session_state.login_lang
    T = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))

    # ============================================================
    # HEADER TEXT
    # ============================================================

    st.markdown(
        f"<h2 style='text-align:center;color:white;margin-top:20px;'>"
        f"{T.get('welcome', 'Welcome')}</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<p style='text-align:center;color:#a0aabf;margin-bottom:30px;'>"
        f"{T.get('subtitle', 'AI Knowledge Platform')}</p>",
        unsafe_allow_html=True
    )

    # ============================================================
    # MODE 1: LOGIN
    # ============================================================

    if st.session_state.login_mode == "login":

        with st.form("login_form"):

            st.markdown(
                f"<h3 style='color:white;'>"
                f"{T.get('signin_title', 'Sign In')}</h3>",
                unsafe_allow_html=True
            )

            username = st.text_input(
                T.get("username", "Username"),
                placeholder="👤 Enter your username"
            )

            password = st.text_input(
                T.get("password", "Password"),
                type="password",
                placeholder="🔑 Enter your password"
            )

            col_rem, col_for = st.columns(2)

            with col_rem:
                st.checkbox(T.get("remember", "Remember me"))

            with col_for:
                forgot_clicked = st.form_submit_button(
                    "Forgot Password?"
                )

            submit = st.form_submit_button(
                T.get("signin_btn", "Sign In"),
                type="primary"
            )

            if forgot_clicked:
                st.session_state.login_mode = "forgot"
                st.rerun()

            if submit:

                if not username or not password:
                    st.error(T.get("error_fill", "Please fill all fields."))

                else:

                    ok, user = verify_user(username.strip(), password)

                    if ok:

                        # User information
                        if isinstance(user, dict):
                            login_username = user.get("username", username.strip())
                            user_role = user.get("role", "user")
                        else:
                            login_username = username.strip()
                            user_role = "user"

                        # Save login session
                        st.session_state.user = login_username
                        st.session_state.user_role = user_role
                        st.session_state.logged_in = True

                        # Selected login language becomes Dashboard language
                        selected_language = st.session_state.login_lang

                        st.session_state.ui_lang = selected_language

                        # Persist selected language in user database
                        try:
                            update_user_language(
                                login_username,
                                selected_language
                            )
                        except Exception as e:
                            st.warning(
                                f"Language preference could not be saved: {e}"
                            )

                        st.rerun()

                    else:
                        st.error(
                            T.get("error_wrong", "Invalid username or password.")
                        )

        # CREATE ACCOUNT BUTTON

        st.markdown(
            "<div class='link-btn'>",
            unsafe_allow_html=True
        )

        if st.button(
            f"👉 {T.get('new_user', 'Create Account')}"
        ):
            st.session_state.login_mode = "signup"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # MODE 2: SIGN UP
    # ============================================================

    elif st.session_state.login_mode == "signup":

        st.markdown(
            "<h3 style='color:white;'>Create New Account</h3>",
            unsafe_allow_html=True
        )

        with st.form("signup_form"):

            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Password", type="password")
            new_pass2 = st.text_input(
                "Confirm Password",
                type="password"
            )

            submit_signup = st.form_submit_button("📝 Sign Up")

            if submit_signup:

                if not new_user or not new_pass:
                    st.error("Username र Password भर्नुहोस्।")

                elif new_pass != new_pass2:
                    st.error("Password मिलेन।")

                elif len(new_pass) < 6:
                    st.error("Password कम्तिमा ६ अक्षर हुनुपर्छ।")

                else:

                    try:
                        ok, msg = create_user(
                            new_user.strip(),
                            new_pass,
                            new_email.strip(),
                            preferred_language=st.session_state.login_lang
                        )

                        if ok:
                            st.success(
                                "✅ Account बन्यो! अब Login गर्नुहोस्।"
                            )

                            time.sleep(1)

                            st.session_state.login_mode = "login"
                            st.rerun()

                        else:
                            st.error(f"❌ {msg}")

                    except Exception as e:
                        st.error(f"❌ Account creation error: {e}")

        if st.button("⬅️ Back to Login"):
            st.session_state.login_mode = "login"
            st.rerun()

    # ============================================================
    # MODE 3: FORGOT PASSWORD
    # ============================================================

    elif st.session_state.login_mode == "forgot":

        st.markdown(
            "<h3 style='color:white;'>Forgot Password</h3>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<p style='color:#a0aabf;'>"
            "तपाईंको इमेल हाल्नुहोस्, हामी reset link पठाउनेछौं।"
            "</p>",
            unsafe_allow_html=True
        )

        with st.form("forgot_form"):

            forgot_email = st.text_input("Email")

            submit_forgot = st.form_submit_button(
                "📧 Send Reset Link"
            )

            if submit_forgot:

                if not forgot_email:
                    st.error("Email भर्नुहोस्।")

                else:
                    st.success(
                        "✅ यदि यो इमेल दर्ता छ भने, Reset Link पठाइनेछ।"
                    )

                    st.info(
                        "Dev mode: OTP/Reset link terminal मा हेर्नुहोस्।"
                    )

                    # Existing reset-email workflow can be connected here.

        if st.button("⬅️ Back to Login"):
            st.session_state.login_mode = "login"
            st.rerun()

    # ============================================================
    # FOOTER
    # ============================================================

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    col1.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"🛡️<br>{T.get('secure', 'Secure')}</p>",
        unsafe_allow_html=True
    )

    col2.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"🧠<br>{T.get('ai', 'AI Powered')}</p>",
        unsafe_allow_html=True
    )

    col3.markdown(
        f"<p style='text-align:center;color:#a0aabf;font-size:12px;'>"
        f"💾<br>{T.get('memory', 'Smart Memory')}</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<p style='text-align:center;color:#667eea;"
        f"font-size:12px;margin-top:20px;'>"
        f"{T.get('footer', 'PDF Brain - AI Knowledge Platform')}</p>",
        unsafe_allow_html=True
    )
