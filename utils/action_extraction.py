import spacy

def extract_action_items(transcript_text):
    """
    Accept transcript text and use spaCy + keyword matching to find action items.
    Keywords: should, need to, must, will, please, have to, action, task
    """
    if not transcript_text:
        return []

    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback if spaCy model is not loaded (though we installed it)
        return [s.strip() for s in transcript_text.split(". ") if any(kw in s.lower() for kw in ["should", "need to", "must", "will", "please", "have to", "action", "task"])]

    doc = nlp(transcript_text)
    keywords = ["should", "need to", "must", "will", "please", "have to", "action", "task"]
    
    action_items = []
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if any(kw in sent_text.lower() for kw in keywords):
            action_items.append(sent_text)
            
    return action_items

if __name__ == "__main__":
    sample = "We need to finish the report by Friday. Please send me the link. John will take care of the backend. We will have a meeting."
    print(extract_action_items(sample))
