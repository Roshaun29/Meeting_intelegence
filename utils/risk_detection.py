import re

def detect_risks(transcript_text):
    """
    Detect risk sentences using keywords:
    'not sure', 'maybe', 'delay', 'unclear', 'depends', 'uncertain', 'problem', 'issue', 'concern', 'blocker'
    """
    if not transcript_text:
        return []

    keywords = ["not sure", "maybe", "delay", "unclear", "depends", "uncertain", "problem", "issue", "concern", "blocker"]
    
    sentences = re.split(r'(?<=[.!?])\s+', transcript_text)
    
    risks = []
    for sent in sentences:
        sent_strip = sent.strip()
        if any(kw in sent_strip.lower() for kw in keywords):
            risks.append(sent_strip)
            
    return risks

if __name__ == "__main__":
    sample = "I am not sure about the deadline. There might be a delay. This is a big blocker."
    print(detect_risks(sample))
