# chunker.py
import re

def split_into_sentences(text):
    """Text लाई वाक्यमा बाँड्ने"""
    # ।, ., !, ? पछि split गर्ने
    sentences = re.split(r'(?<=[।.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text, size=800, overlap=150):
    """
    Smart chunking — वाक्य सीमामा काट्ने।
    Overlap ले context जोगाउँछ।
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # यदि यो sentence थप्दा size नाघ्छ भने
        if len(current_chunk) + len(sentence) > size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Overlap को लागि अन्तिम भाग राख्ने
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += " " + sentence
    
    # अन्तिम chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def chunk_all(texts):
    """सबै file लाई chunks मा बदल्ने"""
    all_chunks = []
    
    for filename, text in texts.items():
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": filename,
                "id": f"{filename}_{i}"
            })
    
    return all_chunks


# Test
if __name__ == "__main__":
    from reader import read_all_docs
    
    print("📚 PDF पढ्दै...\n")
    texts = read_all_docs()
    
    print("✂️  Smart Chunks बनाउँदै...\n")
    chunks = chunk_all(texts)
    
    print(f"🎉 जम्मा {len(chunks)} chunks बने\n")
    
    if chunks:
        print("पहिलो chunk:")
        print("-" * 60)
        print(chunks[0]["text"][:400])
        print("-" * 60)
        print(f"\nSource: {chunks[0]['source']}")
        print(f"Length: {len(chunks[0]['text'])} अक्षर")