import re

def detect_decisions(transcript_text):
    """
    Detect decision sentences using keywords:
    'we decided', 'we will go with', 'finalized', 'agreed', 'confirmed', 'we are going with', 'decision is'
    """
    if not transcript_text:
        return []

    keywords = ["we decided", "we will go with", "finalized", "agreed", "confirmed", "we are going with", "decision is"]
    
    # Split into sentences (simple regex fallback)
    sentences = re.split(r'(?<=[.!?])\s+', transcript_text)
    
    decisions = []
    for sent in sentences:
        sent_strip = sent.strip()
        if any(kw in sent_strip.lower() for kw in keywords):
            decisions.append(sent_strip)
            
    return decisions

if __name__ == "__main__":
    sample = "We decided to use React. We finalized the architecture. It was agreed that John will lead."
    print(detect_decisions(sample))
