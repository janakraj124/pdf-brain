# admin.py — PDF Brain Admin Dashboard (Powerful v2)
import os
import sqlite3
import json
import shutil
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

DB_FILE = "pdf_brain.db"

def _get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 📊 STATS
# ============================================================
def get_system_stats():
    conn = _get_conn()
    c = conn.cursor()
    stats = {}
    for key, query in [
        ("total_users", "SELECT COUNT(*) as n FROM users"),
        ("total_actions", "SELECT COUNT(*) as n FROM audit_log"),
        ("total_logins", "SELECT COUNT(*) as n FROM audit_log WHERE action='LOGIN'"),
        ("failed_actions", "SELECT COUNT(*) as n FROM audit_log WHERE status='failed'"),
        ("total_messages", "SELECT COUNT(*) as n FROM dm_messages"),
    ]:
        try:
            c.execute(query)
            stats[key] = c.fetchone()["n"]
        except:
            stats[key] = 0
    conn.close()
    return stats


def get_user_list():
    conn = _get_conn()
    c = conn.cursor()
    users = []
    try:
        c.execute("SELECT username, role, last_read FROM users ORDER BY username")
        users = [dict(r) for r in c.fetchall()]
    except Exception as e:
        print(f"[USER LIST ERROR] {e}")
    conn.close()
    return users


def update_user_role(username, new_role):
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET role=? WHERE username=?", (new_role, username))
        conn.commit()
        return True
    except Exception as e:
        print(f"[ROLE ERROR] {e}")
        return False
    finally:
        conn.close()


def delete_user(username):
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username=?", (username,))
        c.execute("DELETE FROM audit_log WHERE username=?", (username,))
        c.execute("DELETE FROM dm_messages WHERE sender=? OR receiver=?", (username, username))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DELETE ERROR] {e}")
        return False
    finally:
        conn.close()


def get_recent_actions(limit=50, filter_user=None, filter_action=None):
    conn = _get_conn()
    c = conn.cursor()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if filter_user:
        query += " AND username LIKE ?"
        params.append(f"%{filter_user}%")
    if filter_action:
        query += " AND action LIKE ?"
        params.append(f"%{filter_action}%")
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_stats():
    if not os.path.exists("feedback.csv"):
        return pd.DataFrame()
    try:
        return pd.read_csv("feedback.csv")
    except:
        return pd.DataFrame()


def get_daily_activity(days=7):
    conn = _get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    data = []
    try:
        c.execute(
            "SELECT DATE(timestamp) as day, COUNT(*) as count FROM audit_log "
            "WHERE timestamp > ? GROUP BY DATE(timestamp) ORDER BY day",
            (cutoff,)
        )
        data = [{"day": r["day"], "count": r["count"]} for r in c.fetchall()]
    except Exception as e:
        print(f"[ACTIVITY ERROR] {e}")
    conn.close()
    return data


def get_action_breakdown():
    conn = _get_conn()
    c = conn.cursor()
    data = []
    try:
        c.execute("SELECT action, COUNT(*) as count FROM audit_log GROUP BY action ORDER BY count DESC")
        data = [{"action": r["action"], "count": r["count"]} for r in c.fetchall()]
    except: pass
    conn.close()
    return data


# ============================================================
# 👤 USER ACTIVITY (प्रति user)
# ============================================================
def get_user_activity(username, days=30):
    conn = _get_conn()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    data = []
    try:
        c.execute(
            "SELECT DATE(timestamp) as day, COUNT(*) as count FROM audit_log "
            "WHERE username=? AND timestamp > ? GROUP BY DATE(timestamp) ORDER BY day",
            (username, cutoff)
        )
        data = [{"day": r["day"], "count": r["count"]} for r in c.fetchall()]
    except: pass
    conn.close()
    return data


def get_user_stats(username):
    """एक user को सबै stats"""
    conn = _get_conn()
    c = conn.cursor()
    stats = {}
    try:
        c.execute("SELECT COUNT(*) as n FROM audit_log WHERE username=?", (username,))
        stats["actions"] = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) as n FROM audit_log WHERE username=? AND action='LOGIN'", (username,))
        stats["logins"] = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) as n FROM audit_log WHERE username=? AND status='failed'", (username,))
        stats["failed"] = c.fetchone()["n"]
        c.execute("SELECT timestamp FROM audit_log WHERE username=? AND action='LOGIN' ORDER BY timestamp DESC LIMIT 1", (username,))
        row = c.fetchone()
        stats["last_login"] = row["timestamp"][:16] if row else "कहिल्यै छैन"
    except: pass
    conn.close()
    return stats


# ============================================================
# 📧 EMAIL BROADCAST
# ============================================================
def send_broadcast_email(subject, message):
    """सबै users लाई email पठाउने"""
    users = get_user_list()
    if not users:
        return {"success": 0, "failed": 0, "errors": []}

    try:
        from email_server import send_email_with_attachment
    except ImportError:
        return {"success": 0, "failed": len(users), "errors": ["email_server.py भेटिएन"]}

    success = 0
    failed = 0
    errors = []
    for u in users:
        email = u["username"]
        if "@" not in email:
            continue
        try:
            ok = send_email_with_attachment(email, subject, message)
            if ok:
                success += 1
            else:
                failed += 1
                errors.append(f"{email}: failed")
        except Exception as e:
            failed += 1
            errors.append(f"{email}: {e}")
    return {"success": success, "failed": failed, "errors": errors[:5]}


# ============================================================
# 💾 BACKUP / RESTORE
# ============================================================
def create_backup():
    """DB backup बनाउने"""
    os.makedirs("backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/backup_{timestamp}.db"
    try:
        shutil.copy2(DB_FILE, backup_path)
        return backup_path
    except Exception as e:
        return None


def list_backups():
    if not os.path.exists("backups"):
        return []
    files = [f for f in os.listdir("backups") if f.endswith(".db")]
    return sorted(files, reverse=True)


def restore_backup(backup_name):
    """Backup बाट DB restore"""
    src = os.path.join("backups", backup_name)
    if not os.path.exists(src):
        return False
    try:
        # पुरानो DB लाई backup
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, f"backups/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(src, DB_FILE)
        return True
    except Exception as e:
        print(f"[RESTORE ERROR] {e}")
        return False


# ============================================================
# 🔐 LOGIN HISTORY
# ============================================================
def get_login_history(limit=100):
    conn = _get_conn()
    c = conn.cursor()
    data = []
    try:
        c.execute(
            "SELECT username, timestamp, status, details FROM audit_log "
            "WHERE action='LOGIN' ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        data = [dict(r) for r in c.fetchall()]
    except: pass
    conn.close()
    return data


# ============================================================
# 🎨 MAIN ADMIN PANEL
# ============================================================
def render_admin_panel():
    st.markdown("## 👑 Admin Dashboard")
    st.caption("PDF Brain को पूरा नियन्त्रण — Users, Audit, Feedback, System")

    tab_dash, tab_users, tab_audit, tab_feedback, tab_system = st.tabs([
        "📊 Dashboard", "👥 Users", "📋 Audit Log", "💬 Feedback", "🖥️ System"
    ])

    # ============================================================
    # 📊 DASHBOARD
    # ============================================================
    with tab_dash:
        stats = get_system_stats()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("👥 Users", stats["total_users"])
        m2.metric("🔐 Logins", stats["total_logins"])
        m3.metric("📋 Actions", stats["total_actions"])
        m4.metric("💬 Messages", stats["total_messages"])
        m5.metric("⚠️ Failed", stats["failed_actions"])

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Daily Activity (7 days)")
            daily = get_daily_activity(7)
            if daily:
                try:
                    import plotly.express as px
                    df = pd.DataFrame(daily)
                    fig = px.line(df, x="day", y="count", markers=True, title="Actions per Day")
                    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.dataframe(pd.DataFrame(daily))
            else:
                st.caption("कुनै activity छैन")

        with col2:
            st.markdown("### 🎯 Action Breakdown")
            breakdown = get_action_breakdown()
            if breakdown:
                try:
                    import plotly.express as px
                    df = pd.DataFrame(breakdown)
                    fig = px.pie(df, names="action", values="count", title="Actions by Type")
                    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.dataframe(pd.DataFrame(breakdown))
            else:
                st.caption("कुनै action छैन")

        st.markdown("---")
        st.markdown("### 🕒 Recent Activity")
        recent = get_recent_actions(limit=10)
        if recent:
            st.dataframe(pd.DataFrame(recent)[["timestamp", "username", "action", "target", "status"]],
                         use_container_width=True, height=300)
        else:
            st.caption("कुनै activity छैन")

        st.markdown("---")
        st.markdown("### 🔐 Recent Login History")
        logins = get_login_history(limit=10)
        if logins:
            st.dataframe(pd.DataFrame(logins), use_container_width=True, height=250)
        else:
            st.caption("कुनै login छैन")

    # ============================================================
    # 👥 USERS
    # ============================================================
    with tab_users:
        st.markdown("### 👥 User Management")

        users = get_user_list()
        if not users:
            st.warning("⚠️ कुनै user छैन। पहिले register गर्नुहोस्।")
        else:
            # Search
            user_search = st.text_input("🔍 Search user", key="admin_user_search")
            filtered = [u for u in users if not user_search or user_search.lower() in u["username"].lower()]

            # Table
            df = pd.DataFrame(filtered)
            if "role" not in df.columns:
                df["role"] = "user"
            st.dataframe(df, use_container_width=True, height=250)

            st.markdown("---")
            st.markdown("### ⚙️ Manage User")

            # User select
            selected_user = st.selectbox(
                "Select user",
                [u["username"] for u in filtered],
                key="admin_sel_user"
            )

            if selected_user:
                # User stats
                ustats = get_user_stats(selected_user)
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("📋 Actions", ustats.get("actions", 0))
                sc2.metric("🔐 Logins", ustats.get("logins", 0))
                sc3.metric("⚠️ Failed", ustats.get("failed", 0))
                sc4.metric("🕒 Last Login", ustats.get("last_login", "—"))

                # Activity chart
                st.markdown("#### 📈 User Activity (30 days)")
                uact = get_user_activity(selected_user, 30)
                if uact:
                    try:
                        import plotly.express as px
                        df_act = pd.DataFrame(uact)
                        fig = px.bar(df_act, x="day", y="count", title=f"{selected_user} Activity")
                        fig.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        st.dataframe(pd.DataFrame(uact))
                else:
                    st.caption("कुनै activity छैन")

                st.markdown("---")
                st.markdown("### 🎭 Change Role")

                current_role = next((u.get("role", "user") for u in filtered if u["username"] == selected_user), "user")
                col1, col2 = st.columns([4, 1])
                with col1:
                    new_role = st.selectbox(
                        "New role",
                        ["user", "manager", "admin", "accountant"],
                        index=["user", "manager", "admin", "accountant"].index(current_role) if current_role in ["user", "manager", "admin", "accountant"] else 0,
                        key="admin_new_role"
                    )
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("💾 Update", key="admin_update_role", use_container_width=True):
                        if update_user_role(selected_user, new_role):
                            st.success(f"✅ {selected_user} → {new_role}")
                            st.rerun()
                        else:
                            st.error("❌ Failed")

                st.markdown("---")
                st.markdown("### 🗑️ Delete User")
                st.warning(f"⚠️ यो कार्य अपरिवर्तनीय छ — **{selected_user}** + audit + messages मेटिन्छ")
                confirm_delete = st.checkbox(f"म {selected_user} मेटाउन चाहन्छु", key="admin_confirm_del")
                if confirm_delete:
                    if st.button(f"🗑️ Delete {selected_user}", key="admin_del_user", type="primary"):
                        if delete_user(selected_user):
                            st.success(f"✅ {selected_user} deleted")
                            st.rerun()
                        else:
                            st.error("❌ Failed")

    # ============================================================
    # 📋 AUDIT LOG
    # ============================================================
    with tab_audit:
        st.markdown("### 📋 Audit Log")

        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            filter_user = st.text_input("👤 Filter user", key="admin_audit_user")
        with fcol2:
            filter_action = st.text_input("🎯 Filter action", key="admin_audit_action")
        with fcol3:
            limit = st.number_input("📊 Limit", 10, 1000, 100, key="admin_audit_limit")

        logs = get_recent_actions(limit=int(limit), filter_user=filter_user or None, filter_action=filter_action or None)
        if logs:
            df = pd.DataFrame(logs)
            cols = [c for c in ["timestamp", "username", "action", "target", "status", "details"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, height=400)

            csv = df[cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="admin_download_audit"
            )
        else:
            st.caption("कुनै log छैन")

    # ============================================================
    # 💬 FEEDBACK
    # ============================================================
    with tab_feedback:
        st.markdown("### 💬 Feedback Analysis")
        df = get_feedback_stats()
        if not df.empty:
            fcol1, fcol2, fcol3 = st.columns(3)
            total = len(df)
            like = len(df[df["rating"] == "like"]) if "rating" in df.columns else 0
            dislike = len(df[df["rating"] == "dislike"]) if "rating" in df.columns else 0

            fcol1.metric("📊 Total", total)
            fcol2.metric("👍 Like", like)
            fcol3.metric("👎 Dislike", dislike)

            st.markdown("---")
            st.dataframe(df.tail(50), use_container_width=True, height=300)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Feedback CSV", data=csv,
                               file_name=f"feedback_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv")
        else:
            st.caption("कुनै feedback छैन")

    # ============================================================
    # 🖥️ SYSTEM
    # ============================================================
    with tab_system:
        st.markdown("### 🖥️ System Health")

        sys_col1, sys_col2 = st.columns(2)
        with sys_col1:
            st.markdown("#### 💾 Database")
            if os.path.exists(DB_FILE):
                size = os.path.getsize(DB_FILE) / 1024
                st.metric("DB Size", f"{size:.1f} KB")
            else:
                st.caption("DB छैन")

            st.markdown("#### 📁 Folders")
            folders = ["docs", "history_data", "messenger_uploads", "avatar_uploads", "temp_images", "backups"]
            for f in folders:
                if os.path.exists(f):
                    count = len(os.listdir(f))
                    st.caption(f"✅ `{f}` ({count} files)")
                else:
                    st.caption(f"❌ `{f}` (missing)")

        with sys_col2:
            st.markdown("#### 🔌 API Status")
            st.caption(f"{'✅' if os.getenv('GEMINI_API_KEY') else '❌'} GEMINI_API_KEY")
            st.caption(f"{'✅' if os.getenv('SMTP_USER') else '❌'} SMTP_USER")
            st.caption(f"{'✅' if os.getenv('WHATSAPP_ACCESS_TOKEN') else '❌'} WHATSAPP_ACCESS_TOKEN")

            st.markdown("#### 📊 Quick Stats")
            stats = get_system_stats()
            st.caption(f"👥 {stats['total_users']} users")
            st.caption(f"📋 {stats['total_actions']} actions")
            st.caption(f"💬 {stats['total_messages']} messages")

        st.markdown("---")
        st.markdown("### 💾 Backup & Restore")

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("💾 Create Backup Now", key="admin_backup_btn", use_container_width=True, type="primary"):
                path = create_backup()
                if path:
                    st.success(f"✅ Backup created: `{path}`")
                else:
                    st.error("❌ Backup failed")

        with bcol2:
            backups = list_backups()
            if backups:
                selected_backup = st.selectbox("Select backup", backups, key="admin_sel_backup")
                if st.button("♻️ Restore Backup", key="admin_restore_btn", use_container_width=True):
                    if restore_backup(selected_backup):
                        st.success(f"✅ Restored: {selected_backup}")
                        st.info("⚠️ Streamlit पुनः सुरु गर्नुहोस्")
                    else:
                        st.error("❌ Restore failed")
            else:
                st.caption("कुनै backup छैन")

        st.markdown("---")
        st.markdown("### 📧 Email Broadcast")
        st.caption("सबै users लाई एकैचोटि email पठाउनुहोस्")

        with st.form("broadcast_form"):
            bc_subject = st.text_input("Subject", key="bc_subject")
            bc_message = st.text_area("Message", height=150, key="bc_message")
            bc_submit = st.form_submit_button("📧 Send to All Users", type="primary")

            if bc_submit:
                if not bc_subject or not bc_message:
                    st.warning("Subject र Message दुवै चाहिन्छ")
                else:
                    with st.spinner("📧 पठाउँदै..."):
                        result = send_broadcast_email(bc_subject, bc_message)
                    if result["success"] > 0:
                        st.success(f"✅ {result['success']} users लाई पठाइयो")
                    if result["failed"] > 0:
                        st.warning(f"⚠️ {result['failed']} failed")
                        for err in result["errors"]:
                            st.caption(f"  • {err}")