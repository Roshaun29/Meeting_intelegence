from transformers import pipeline
import torch

def analyze_sentiment(transcript_text):
    """
    Use distilbert-base-uncased-finetuned-sst-2-english for sentiment analysis.
    Handles long text by chunking and averaging.
    """
    if not transcript_text:
        return "neutral"

    try:
        device = 0 if torch.cuda.is_available() else -1
        classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)
        
        # Chunk text (DistilBERT limit 512 tokens)
        max_chunk_chars = 2000 
        chunks = [transcript_text[i:i+max_chunk_chars] for i in range(0, len(transcript_text), max_chunk_chars)]
        
        results = classifier(chunks)
        
        # Calculate scores
        label_weights = {"POSITIVE": 1, "NEGATIVE": -1}
        total_score = sum(label_weights[res['label']] * res['score'] for res in results)
        avg_score = total_score / len(results)
        
        if avg_score > 0.3:
            return "positive"
        elif avg_score < -0.3:
            return "negative"
        else:
            return "neutral"
            
    except Exception as e:
        print(f"Sentiment analysis error: {str(e)}")
        return "neutral"

if __name__ == "__main__":
    sample = "I am so happy with our progress today! It was amazing."
    print(analyze_sentiment(sample))
