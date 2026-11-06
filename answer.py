# answer.py — Level 4 (Tag Filter सहित)
import os
import time
from dotenv import load_dotenv
from google import genai
from vector_store import hybrid_search

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model — धेरै quota दिन्छ
MODEL = "gemini-3.5-flash-lite"


def answer_question(question, username="guest", tag_filter=None, max_retries=3):
    """
    प्रश्नको जवाफ AI बाट लिने।
    
    Args:
        question: User को प्रश्न
        username: User को नाम (analytics को लागि)
        tag_filter: List of tags — यी tags भएका PDF मा मात्र खोज्ने
        max_retries: Retry attempts (503/429 को लागि)
    
    Returns:
        {"answer": str, "sources": list}
    """
    start_time = time.time()
    
    # ============================================================
    # Search (Tag Filter सहित)
    # ============================================================
    try:
        results = hybrid_search(
            question,
            n=10,
            top_n=6,
            tag_filter=tag_filter
        )
    except Exception as e:
        return {
            "answer": f"❌ Search error: {e}",
            "sources": []
        }
    
    # कुनै result छैन भने
    if not results:
        if tag_filter:
            tag_str = ", ".join(tag_filter)
            return {
                "answer": f"⚠️ **'{tag_str}'** tag भएको कुनै PDF मा यो जानकारी भेटिएन।\n\n💡 Filter हटाएर फेरि try गर्नुहोस्।",
                "sources": []
            }
        return {
            "answer": "⚠️ Database खाली छ। पहिले `python vector_store.py` चलाउनुहोस्।",
            "sources": []
        }
    
    # ============================================================
    # Context बनाउने
    # ============================================================
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(f"[स्रोत {i}: {r['source']}]\n{r['text']}")
    context = "\n\n---\n\n".join(context_parts)
    
    sources = list(set([r["source"] for r in results]))
    
    # ============================================================
    # Prompt
    # ============================================================
    prompt = f"""तपाईं सहयोगी सहायक हुनुहुन्छ।
तलको जानकारी ध्यानपूर्वक पढ्नुहोस् र प्रश्नको जवाफ दिनुहोस्।

⚠️ महत्त्वपूर्ण नियमहरू:
1. जानकारीमा भएको कुरा मात्र भन्नुहोस् — कल्पना नगर्नुहोस्
2. नाम, मिति, संख्या ध्यानपूर्वक खोज्नुहोस्
3. यदि जानकारीमा छैन भने स्पष्ट "भेटिएन" भन्नुहोस्
4. जवाफ सरल नेपालीमा दिनुहोस्
5. Table को data भए exact number भन्नुहोस्

जानकारी:
{context}

प्रश्न: {question}

जवाफ:"""
    
    # ============================================================
    # AI Call (Retry सहित)
    # ============================================================
    answer_text = "❌ AI जवाफ दिन सकेन।"
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            answer_text = response.text
            break
        except Exception as e:
            error_str = str(e)
            
            # Retry logic
            if ("503" in error_str or "429" in error_str) and attempt < max_retries - 1:
                wait = (attempt + 1) * 3
                print(f"⚠️ Retry {attempt+1}/{max_retries} — {wait}s...")
                time.sleep(wait)
                continue
            
            # Friendly error messages
            if "429" in error_str:
                answer_text = "⏳ **दिनको quota सकियो।** भोलि try गर्नुहोस्, वा नयाँ API key बनाउनुहोस्।"
            elif "503" in error_str:
                answer_text = "⏳ **Google server व्यस्त छ।** १ मिनेट पछि try गर्नुहोस्।"
            elif "401" in error_str or "API_KEY" in error_str:
                answer_text = "❌ **API Key गलत छ।** `.env` file जाँच्नुहोस्।"
            else:
                answer_text = f"❌ Error: {e}"
            break
    
    # ============================================================
    # Analytics Log
    # ============================================================
    elapsed = time.time() - start_time
    try:
        from analytics import log_query
        log_query(username, question, answer_text, elapsed, sources)
    except Exception:
        pass  # Log fail भए पनि जवाफ दिने
    
    return {
        "answer": answer_text,
        "sources": sources
    }


# ============================================================
# Streaming Version (Optional — भविष्यको लागि)
# ============================================================
def answer_question_stream(question, username="guest", tag_filter=None):
    """
    Streaming response — शब्द-शब्द जवाफ।
    Generator function — `for chunk in answer_question_stream(...)` प्रयोग गर्नुहोस्।
    """
    start_time = time.time()
    
    # Search
    try:
        results = hybrid_search(question, n=10, top_n=6, tag_filter=tag_filter)
    except Exception as e:
        yield f"❌ Search error: {e}"
        return
    
    if not results:
        if tag_filter:
            yield f"⚠️ **'{', '.join(tag_filter)}'** tag मा केही भेटिएन।"
        else:
            yield "⚠️ Database खाली छ।"
        return
    
    # Context
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(f"[स्रोत {i}: {r['source']}]\n{r['text']}")
    context = "\n\n---\n\n".join(context_parts)
    sources = list(set([r["source"] for r in results]))
    
    prompt = f"""तपाईं सहयोगी सहायक हुनुहुन्छ।
तलको जानकारी प्रयोग गरेर प्रश्नको जवाफ दिनुहोस्।
जानकारीमा छैन भने "भेटिएन" भन्नुहोस्।

जानकारी:
{context}

प्रश्न: {question}

जवाफ:"""
    
    full_answer = ""
    
    try:
        response = client.models.generate_content_stream(
            model=MODEL,
            contents=prompt
        )
        
        for chunk in response:
            if chunk.text:
                full_answer += chunk.text
                yield chunk.text
    except Exception as e:
        yield f"\n\n❌ Error: {e}"
        full_answer = f"Error: {e}"
    
    # Log
    elapsed = time.time() - start_time
    try:
        from analytics import log_query
        log_query(username, question, full_answer, elapsed, sources)
    except Exception:
        pass


# ============================================================
# CLI Test
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("💬 PDF Brain — CLI Test (Tag Filter सहित)")
    print("=" * 60)
    
    # Tag info
    try:
        from tags import get_all_tags
        all_tags = get_all_tags()
        if all_tags:
            print(f"\n🏷️  Available tags: {', '.join(all_tags)}")
        else:
            print("\n🏷️  कुनै tags छैन")
    except ImportError:
        all_tags = []
        print("\n⚠️  tags.py भेटिएन")
    
    print("\n💡 प्रश्न सोध्नुहोस् (exit = बाहिर)")
    print("   Tag filter को लागि: 'tag:financial यो किताब कसको हो?'")
    print()
    
    while True:
        try:
            q = input("📝 प्रश्न: ").strip()
            
            if not q or q.lower() in ["exit", "quit", "q"]:
                print("👋 Bye!")
                break
            
            # Tag filter parse
            tag_filter = None
            if q.startswith("tag:"):
                parts = q.split(" ", 1)
                if len(parts) == 2:
                    tag_str = parts[0].replace("tag:", "")
                    tag_filter = [t.strip() for t in tag_str.split(",") if t.strip()]
                    q = parts[1]
                    print(f"   🏷️ Filter: {tag_filter}")
            
            print("\n🤔 सोच्दै...")
            result = answer_question(q, username="cli_test", tag_filter=tag_filter)
            
            print("\n💡 जवाफ:")
            print("-" * 60)
            print(result["answer"])
            print("-" * 60)
            
            if result["sources"]:
                print(f"📚 स्रोत: {', '.join(result['sources'])}")
            
            print()
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")