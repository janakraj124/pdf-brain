# login.py
import streamlit as st
import time
from datetime import datetime
from auth import verify_user, create_user
from translations import LANGUAGES, TRANSLATIONS

def login_page():
    # ✅ भाषा सेटअप
    if "login_lang" not in st.session_state:
        st.session_state.login_lang = "en"
    
    lang = st.session_state.login_lang
    T = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    # ✅ Mode State (Login, Signup, Forgot)
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "login"

    # ✅ डार्क थिम CSS
    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: white; }
        .brand-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
        .brand-title { font-size: 24px; font-weight: bold; color: white; margin: 0; }
        .brand-sub { font-size: 12px; color: #a0aabf; margin: 0; }
        .stTextInput>div>div>input {
            background-color: #212937 !important; color: white !important;
            border: 1px solid #323d4e !important; border-radius: 10px !important;
        }
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important; border-radius: 10px !important;
            font-weight: bold !important; padding: 10px !important;
            width: 100% !important; border: none !important;
        }
        .link-btn { text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

    # ✅ माथिको भाग (लोगो र भाषा)
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
        lang_options = list(LANGUAGES.keys())
        selected_lang = st.selectbox(
            "", lang_options, format_func=lambda x: LANGUAGES[x],
            index=lang_options.index(st.session_state.login_lang),
            label_visibility="collapsed"
        )
        if selected_lang != st.session_state.login_lang:
            st.session_state.login_lang = selected_lang
            st.rerun()

    # ✅ हेडर
    st.markdown(f"<h2 style='text-align: center; color: white; margin-top: 20px;'>{T['welcome']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #a0aabf; margin-bottom: 30px;'>{T['subtitle']}</p>", unsafe_allow_html=True)

    # ============================================================
    # 🔐 MODE 1: LOGIN
    # ============================================================
    if st.session_state.login_mode == "login":
        with st.form("login_form"):
            st.markdown(f"<h3 style='color: white;'>{T['signin_title']}</h3>", unsafe_allow_html=True)
            
            username = st.text_input(T['username'], placeholder="👤 Enter your username")
            password = st.text_input(T['password'], type="password", placeholder="🔑 Enter your password")
            
            col_rem, col_for = st.columns(2)
            with col_rem:
                st.checkbox(T['remember'])
            with col_for:
                # ✅ Forgot Password Link (Button को रूपमा)
                if st.form_submit_button("Forgot Password?"):
                    st.session_state.login_mode = "forgot"
                    st.rerun()
            
            submit = st.form_submit_button(T['signin_btn'])
            
            if submit:
                if not username or not password:
                    st.error(T['error_fill'])
                else:
                    ok, user = verify_user(username, password)
                    if ok:
                        st.session_state.user = username
                        st.session_state.user_role = user.get("role", "user") if isinstance(user, dict) else "user"
                        st.session_state.logged_in = True
                        st.session_state.ui_lang = st.session_state.login_lang
                        st.rerun()
                    else:
                        st.error(T['error_wrong'])

        # ✅ Create Account Link (Button को रूपमा)
        st.markdown("<div class='link-btn'>", unsafe_allow_html=True)
        if st.button(f"👉 {T['new_user']}"):
            st.session_state.login_mode = "signup"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # 📝 MODE 2: SIGN UP
    # ============================================================
    elif st.session_state.login_mode == "signup":
        st.markdown("<h3 style='color: white;'>Create New Account</h3>", unsafe_allow_html=True)
        with st.form("signup_form"):
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Password", type="password")
            new_pass2 = st.text_input("Confirm Password", type="password")
            
            submit_signup = st.form_submit_button("📝 Sign Up")
            
            if submit_signup:
                if not new_user or not new_pass:
                    st.error("Username र Password भर्नुहोस्।")
                elif new_pass != new_pass2:
                    st.error("Password मिलेन।")
                elif len(new_pass) < 6:
                    st.error("Password कम्तिमा ६ अक्षर।")
                else:
                    ok, msg = create_user(new_user, new_pass, new_email)
                    if ok:
                        st.success("✅ Account बन्यो! अब Login गर्नुहोस्।")
                        time.sleep(1)
                        st.session_state.login_mode = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        if st.button("⬅️ Back to Login"):
            st.session_state.login_mode = "login"
            st.rerun()

    # ============================================================
    # 🔑 MODE 3: FORGOT PASSWORD
    # ============================================================
    elif st.session_state.login_mode == "forgot":
        st.markdown("<h3 style='color: white;'>Forgot Password</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #a0aabf;'>तपाईंको इमेल हाल्नुहोस्, हामी reset link पठाउनेछौं।</p>", unsafe_allow_html=True)
        
        with st.form("forgot_form"):
            forgot_email = st.text_input("Email")
            submit_forgot = st.form_submit_button("📧 Send Reset Link")
            
            if submit_forgot:
                if not forgot_email:
                    st.error("Email भर्नुहोस्।")
                else:
                    st.success("✅ यदि यो इमेल दर्ता छ भने, Reset Link पठाइनेछ।")
                    st.info("Dev mode: OTP/Reset link terminal मा हेर्नुहोस्।")
                    # यहाँ तपाईंको अघिल्लो OTP/Reset code राख्न सक्नुहुन्छ
        
        if st.button("⬅️ Back to Login"):
            st.session_state.login_mode = "login"
            st.rerun()

    # ✅ तलको फुटर
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<p style='text-align: center; color: #a0aabf; font-size: 12px;'>🛡️<br>{T['secure']}</p>", unsafe_allow_html=True)
    col2.markdown(f"<p style='text-align: center; color: #a0aabf; font-size: 12px;'>🧠<br>{T['ai']}</p>", unsafe_allow_html=True)
    col3.markdown(f"<p style='text-align: center; color: #a0aabf; font-size: 12px;'>💾<br>{T['memory']}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<p style='text-align: center; color: #667eea; font-size: 12px; margin-top: 20px;'>{T['footer']}</p>", unsafe_allow_html=True)