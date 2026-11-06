# tags.py
import os
import json

TAGS_FILE = "doc_tags.json"


def load_tags():
    """सबै PDF को tags load गर्ने"""
    if not os.path.exists(TAGS_FILE):
        return {}
    try:
        with open(TAGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_tags(tags):
    """Tags file save गर्ने"""
    try:
        with open(TAGS_FILE, "w", encoding="utf-8") as f:
            json.dump(tags, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def set_pdf_tags(pdf_name, tags_list):
    """PDF लाई tags दिने"""
    tags = load_tags()
    # Clean + deduplicate
    clean = []
    for t in tags_list:
        t = t.strip().lower()
        if t and t not in clean:
            clean.append(t)
    tags[pdf_name] = clean
    save_tags(tags)


def get_pdf_tags(pdf_name):
    """PDF को tags लिने"""
    tags = load_tags()
    return tags.get(pdf_name, [])


def get_all_tags():
    """सबै unique tags (sorted)"""
    tags = load_tags()
    all_tags = set()
    for t_list in tags.values():
        all_tags.update(t_list)
    return sorted(all_tags)


def get_pdfs_by_tag(tag):
    """कुन tag मा कुन PDF"""
    tags = load_tags()
    tag = tag.strip().lower()
    return [pdf for pdf, t_list in tags.items() if tag in t_list]


def get_pdfs_by_tags(tags_list, match_all=False):
    """
    Multiple tags बाट PDF खोज्ने।
    match_all=True भने सबै tag हुनुपर्छ।
    match_all=False भने कुनै एक भए पुग्छ।
    """
    if not tags_list:
        return list(load_tags().keys())
    
    tags = load_tags()
    tags_list = [t.strip().lower() for t in tags_list]
    
    result = []
    for pdf, t_list in tags.items():
        t_list_lower = [t.lower() for t in t_list]
        
        if match_all:
            if all(t in t_list_lower for t in tags_list):
                result.append(pdf)
        else:
            if any(t in t_list_lower for t in tags_list):
                result.append(pdf)
    
    return result


def remove_pdf_tags(pdf_name):
    """PDF को tags हटाउने"""
    tags = load_tags()
    if pdf_name in tags:
        del tags[pdf_name]
        save_tags(tags)
        return True
    return False


def get_tag_stats():
    """Tag statistics"""
    tags = load_tags()
    from collections import Counter
    
    counter = Counter()
    for t_list in tags.values():
        for t in t_list:
            counter[t] += 1
    
    return counter.most_common()


if __name__ == "__main__":
    # Test
    print("🧪 Testing tags.py\n")
    
    set_pdf_tags("sample-table.pdf", ["financial", "report", "2024"])
    set_pdf_tags("sample_letter.pdf", ["legal", "EPA", "letter"])
    
    print("sample-table.pdf tags:", get_pdf_tags("sample-table.pdf"))
    print("sample_letter.pdf tags:", get_pdf_tags("sample_letter.pdf"))
    print("\nAll tags:", get_all_tags())
    print("\nPDFs with 'financial':", get_pdfs_by_tag("financial"))
    print("\nTag stats:", get_tag_stats())