# test_api.py
import requests

API_URL = "http://localhost:8000"
API_KEY = "pb_eT_tldW7kJims99o1gkJvAaFa-0p1UBon954MfgOOTI"

headers = {"X-API-Key": API_KEY}


def test_health():
    r = requests.get(f"{API_URL}/health")
    print("✅ Health:", r.json())


def test_me():
    r = requests.get(f"{API_URL}/me", headers=headers)
    print("👤 Me:", r.json())


def test_ask(question):
    r = requests.post(
        f"{API_URL}/ask",
        headers=headers,
        json={"question": question}
    )
    if r.status_code == 200:
        data = r.json()
        print(f"\n📝 प्रश्न: {question}")
        print(f"💡 जवाफ: {data['answer'][:200]}...")
        print(f"📚 स्रोत: {data['sources']}")
        print(f"⏱️  समय: {data['response_time']}s")
    else:
        print(f"❌ Error: {r.status_code} — {r.text}")


def test_tags():
    r = requests.get(f"{API_URL}/tags", headers=headers)
    print("\n🏷️  Tags:", r.json())


def test_pdfs():
    r = requests.get(f"{API_URL}/pdfs", headers=headers)
    print("\n📄 PDFs:", r.json())


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PDF Brain API Test")
    print("=" * 60)
    
    test_health()
    test_me()
    test_ask("यो document मा के छ ?")
    test_ask("कति amount छ?")
    test_tags()
    test_pdfs()