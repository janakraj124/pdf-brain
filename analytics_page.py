# analytics_page.py
import streamlit as st
import pandas as pd
from analytics import get_analytics, clear_logs


def show_analytics():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h2 class="main-header">📈 Analytics Dashboard</h2>', unsafe_allow_html=True)
    with col2:
        if st.button("← Chat", use_container_width=True, key="back_analytics"):
            st.session_state.show_analytics = False
            st.rerun()
    
    is_admin = st.session_state.get("user_role") == "admin"
    
    if is_admin:
        view_mode = st.radio(
            "के हेर्ने?",
            ["🌐 सबै users", f"👤 मेरो मात्र ({st.session_state.user})"],
            horizontal=True,
            key="analytics_view"
        )
        username = None if "सबै" in view_mode else st.session_state.user
    else:
        username = st.session_state.user
        st.caption(f"👤 तपाईंको analytics — {username}")
    
    a = get_analytics(username=username)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💬 Total Queries", a["total"])
    with col2:
        st.metric("📅 Today", a["today"])
    with col3:
        st.metric("📆 Last 7 Days", a["week"])
    with col4:
        st.metric("⚡ Avg Response", f"{a['avg_response']}s")
    
    if a["total"] == 0:
        st.info("📊 अझै कुनै query छैन। Chat मा प्रश्न सोध्नुहोस्!")
        return
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Last 7 Days")
        df_daily = pd.DataFrame(a["daily_counts"])
        if not df_daily.empty:
            st.bar_chart(df_daily.set_index("date")["count"])
    
    with col2:
        st.markdown("### 🕐 Hourly Distribution")
        df_hourly = pd.DataFrame(a["hourly_counts"])
        if not df_hourly.empty:
            st.bar_chart(df_hourly.set_index("hour")["count"])
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔥 Top 10 प्रश्न")
        if a["top_questions"]:
            for i, (q, c) in enumerate(a["top_questions"], 1):
                st.markdown(f"**{i}.** {q[:60]} — `{c}×`")
        else:
            st.caption("कुनै डाटा छैन")
    
    with col2:
        if is_admin:
            st.markdown("### 👥 Active Users")
            for u, c in a["top_users"]:
                st.markdown(f"👤 **{u}** — `{c} queries`")
        else:
            st.markdown("### 📊 तपाईंको Activity")
            st.metric("तपाईंका Queries", a["total"])
            st.metric("आजका", a["today"])
            st.metric("साप्ताहिक", a["week"])
    
    st.markdown("---")
    st.markdown("### 📄 Top PDFs")
    if a["top_pdfs"]:
        df_pdfs = pd.DataFrame(a["top_pdfs"], columns=["PDF", "Count"])
        st.dataframe(df_pdfs, use_container_width=True, hide_index=True)
    
    if is_admin:
        st.markdown("---")
        with st.expander("⚠️ Admin Actions"):
            if st.button("🗑️ सबै Logs हटाउनुहोस्"):
                clear_logs()
                st.success("✅ Logs हटाइयो")
                st.rerun()

                
    # Tag Statistics
    st.markdown("---")
    st.markdown("### 🏷️ Tag Statistics")
    
    try:
        from tags import get_tag_stats
        stats = get_tag_stats()
        
        if stats:
            df_tags = pd.DataFrame(stats, columns=["Tag", "PDFs"])
            st.dataframe(df_tags, use_container_width=True, hide_index=True)
        else:
            st.caption("कुनै tags छैन")
    except Exception:
        pass