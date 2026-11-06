# create_key.py
from api import create_api_key

print("=" * 60)
print("🔑 API Key बनाउँदै...")
print("=" * 60 + "\n")

key = create_api_key(
    name="My First App",
    username="admin",
    rate_limit=100
)

print(f"✅ API Key बन्यो:\n")
print(f"   {key}\n")
print(f"⚠️  यो key एकैचोटि मात्र देखिन्छ — save गर्नुहोस्!")
print(f"\n💡 Test गर्न:")
print(f'   curl -H "X-API-Key: {key}" http://localhost:8000/health')