# create_admin.py — PDF Brain Secure Admin Creator
"""
Terminal बाट मात्र Admin बनाउने स्क्रिप्ट।
Deploy अघि यो चलाएर users.json बनाउनुहोस्।

Usage:
    python create_admin.py                    → Interactive menu
    python create_admin.py create <user> <email> <pass> [name]  → CLI
    python create_admin.py list               → Admin list
    python create_admin.py export             → users.json export
    python create_admin.py help               → Help
"""
import sys
import os
import json
import getpass
import bcrypt
import re
from datetime import datetime

USERS_FILE = "users.json"


# ============================================================
# 📁 FILE HELPERS
# ============================================================
def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ File load error: {e}")
        return {}


def _save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False


# ============================================================
# 🔍 VALIDATION
# ============================================================
def validate_email(email):
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_username(username):
    if len(username) < 3:
        return False, "Username कम्तिमा ३ अक्षर"
    if len(username) > 20:
        return False, "Username अधिकतम २० अक्षर"
    if not re.match(r'^[\w]+$', username):
        return False, "Username: अक्षर, अंक, _ मात्र"
    return True, "OK"


def check_password_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): score += 1
    return score


# ============================================================
# 👑 ADMIN CREATION
# ============================================================
def _create_admin_dict(username, email, password, name=""):
    """Admin dict बनाउने (common logic)"""
    return {
        "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "email": email,
        "created": datetime.now().isoformat(),
        "last_login": None,
        "login_count": 0,
        "failed_attempts": 0,
        "locked_until": None,
        "profile": {"name": name or username, "phone": ""}
    }


def create_admin_interactive():
    """Interactive Admin creation"""
    print("\n" + "=" * 60)
    print("👑 PDF Brain — नयाँ Admin Account")
    print("=" * 60)
    print("⚠️  यो स्क्रिप्ट Terminal बाट मात्र चल्छ — web UI बाट कोही Admin बन्न सक्दैन।\n")

    users = _load_users()

    # ---- Username ----
    while True:
        username = input("👤 Admin Username: ").strip()
        if not username:
            print("❌ Username खाली हुन सक्दैन।")
            continue

        valid, msg = validate_username(username)
        if not valid:
            print(f"❌ {msg}")
            continue

        if username in users:
            print(f"⚠️  '{username}' पहिले नै छ।")
            choice = input("   के यसलाई Admin बनाउने? (y/n): ").strip().lower()
            if choice == 'y':
                users[username]["role"] = "admin"
                _save_users(users)
                print(f"✅ '{username}' अब Admin बन्यो!")
                return True
            continue
        break

    # ---- Email ----
    while True:
        email = input("📧 Admin Email: ").strip()
        if not email:
            print("❌ Email खाली हुन सक्दैन।")
            continue

        if not validate_email(email):
            print("❌ Email format गलत (जस्तै: admin@example.com)।")
            continue

        # Email uniqueness
        email_taken = False
        for u, data in users.items():
            if data.get("email", "").lower() == email.lower():
                print(f"❌ Email '{email}' पहिले नै '{u}' मा प्रयोग भएको छ।")
                email_taken = True
                break
        if email_taken:
            continue
        break

    # ---- Password ----
    while True:
        password = getpass.getpass("🔑 Admin Password (कम्तिमा ८ अक्षर): ")
        if len(password) < 8:
            print("❌ Password कम्तिमा ८ अक्षर।")
            continue

        strength = check_password_strength(password)
        if strength <= 2:
            print(f"⚠️  Password कमजोर (score: {strength}/5)। राम्रो password प्रयास गर्नुहोस्।")
            confirm = input("   के यसै password प्रयोग गर्ने? (y/n): ").strip().lower()
            if confirm != 'y':
                continue

        password2 = getpass.getpass("🔑 Confirm Password: ")
        if password != password2:
            print("❌ Password मिलेन।")
            continue
        break

    # ---- Name (optional) ----
    name = input("📝 Full Name (optional, Enter थिच्नुहोस् skip गर्न): ").strip() or username

    # ---- Create ----
    users[username] = _create_admin_dict(username, email, password, name)
    if not _save_users(users):
        print("❌ Save गर्न असफल।")
        return False

    print("\n" + "=" * 60)
    print("✅ Admin Account सफलतापूर्वक बन्यो!")
    print("=" * 60)
    print(f"👤 Username: {username}")
    print(f"📧 Email:    {email}")
    print(f"📝 Name:     {name}")
    print(f"🎭 Role:     admin")
    print("=" * 60)
    print("\n⚠️  यो password सुरक्षित राख्नुहोस्!")
    print("💡 अब PDF Brain मा login गर्नुहोस्।\n")
    return True


def create_admin_cli(username, email, password, name=""):
    """CLI बाट Admin बनाउने"""
    users = _load_users()

    valid, msg = validate_username(username)
    if not valid:
        print(f"❌ {msg}")
        return False

    if username in users:
        print(f"⚠️  '{username}' पहिले नै छ। Admin बनाउँदै...")
        users[username]["role"] = "admin"
        _save_users(users)
        print(f"✅ '{username}' अब Admin बन्यो!")
        return True

    if not validate_email(email):
        print("❌ Email format गलत।")
        return False

    if len(password) < 8:
        print("❌ Password कम्तिमा ८ अक्षर।")
        return False

    # Email uniqueness
    for u, data in users.items():
        if data.get("email", "").lower() == email.lower():
            print(f"❌ Email '{email}' पहिले नै '{u}' मा छ।")
            return False

    users[username] = _create_admin_dict(username, email, password, name)
    _save_users(users)
    print(f"✅ Admin '{username}' सिर्जना भयो!")
    print(f"   📧 {email}")
    return True


# ============================================================
# 📋 ADMIN LIST
# ============================================================
def list_admins():
    users = _load_users()
    admins = [(u, d) for u, d in users.items() if d.get("role") == "admin"]

    print("\n" + "=" * 60)
    print(f"👑 Admin Accounts ({len(admins)})")
    print("=" * 60)

    if not admins:
        print("❌ कुनै Admin छैन।")
    else:
        for username, data in admins:
            print(f"👤 {username}")
            print(f"   📧 {data.get('email', 'N/A')}")
            print(f"   📝 {data.get('profile', {}).get('name', 'N/A')}")
            print(f"   🕒 Created: {data.get('created', 'N/A')[:10]}")
            print(f"   🔐 Last Login: {data.get('last_login', 'never')[:10] if data.get('last_login') else 'never'}")
            print()
    print("=" * 60 + "\n")


# ============================================================
# 🔑 PASSWORD CHANGE
# ============================================================
def change_admin_password():
    users = _load_users()
    username = input("\n👤 Admin Username: ").strip()

    if username not in users:
        print(f"❌ '{username}' भेटिएन।")
        return False

    if users[username].get("role") != "admin":
        print(f"⚠️  '{username}' Admin होइन।")
        return False

    while True:
        new_pass = getpass.getpass("🔑 नयाँ Password (कम्तिमा ८ अक्षर): ")
        if len(new_pass) < 8:
            print("❌ Password कम्तिमा ८ अक्षर।")
            continue
        new_pass2 = getpass.getpass("🔑 Confirm Password: ")
        if new_pass != new_pass2:
            print("❌ Password मिलेन।")
            continue
        break

    users[username]["password"] = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
    users[username]["failed_attempts"] = 0
    users[username]["locked_until"] = None
    _save_users(users)
    print(f"✅ '{username}' को password फेरियो!")
    return True


# ============================================================
# 💾 EXPORT (Deploy को लागि)
# ============================================================
def export_users():
    """Users JSON export (deploy को लागि)"""
    users = _load_users()
    if not users:
        print("❌ कुनै user छैन।")
        return

    export_file = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Export भयो: {export_file}")
    print(f"📊 Total users: {len(users)}")
    print(f"👑 Admins: {sum(1 for u in users.values() if u.get('role') == 'admin')}")
    print(f"\n💡 यो फाइल Streamlit Secrets मा राख्नुहोस् (deploy को लागि):")
    print(f"   st.secrets['USERS_JSON'] = {export_file} को content")
    print()


# ============================================================
# 🚀 MAIN
# ============================================================
def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == "create" and len(sys.argv) >= 5:
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
            name = sys.argv[5] if len(sys.argv) > 5 else ""
            create_admin_cli(username, email, password, name)

        elif cmd == "list":
            list_admins()

        elif cmd == "export":
            export_users()

        elif cmd == "password":
            change_admin_password()

        elif cmd == "help":
            print("\n📖 PDF Brain Admin Creator — Usage\n")
            print("  python create_admin.py                    → Interactive menu")
            print("  python create_admin.py create <user> <email> <pass> [name]")
            print("  python create_admin.py list              → Admin list")
            print("  python create_admin.py password          → Password change")
            print("  python create_admin.py export            → users.json export")
            print("  python create_admin.py help              → Help\n")

        else:
            print("❌ Unknown command. 'help' प्रयास गर्नुहोस्।")
    else:
        # Interactive menu
        print("\n" + "=" * 60)
        print("👑 PDF Brain — Admin Management")
        print("=" * 60)
        print("1. ➕ नयाँ Admin बनाउनुहोस्")
        print("2. 📋 Admin list हेर्नुहोस्")
        print("3. 🔑 Admin password फेर्नुहोस्")
        print("4. 💾 Users JSON export (deploy को लागि)")
        print("5. 🚪 बाहिर निस्कनुहोस्")
        print("=" * 60)

        choice = input("\n👉 छान्नुहोस् (1-5): ").strip()

        if choice == "1":
            create_admin_interactive()
        elif choice == "2":
            list_admins()
        elif choice == "3":
            change_admin_password()
        elif choice == "4":
            export_users()
        elif choice == "5":
            print("👋 बिदा!")
        else:
            print("❌ गलत विकल्प।")


if __name__ == "__main__":
    main()