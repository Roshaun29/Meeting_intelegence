from transformers import pipeline
import torch

def chunk_text(text, max_length=512):
    """Split text into chunks of roughly max_length characters."""
    # Simple character-based chunking for speed, or sentence based
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def generate_summary(transcript_text):
    """
    Load facebook/bart-large-cnn and generate a summary.
    Handles long transcripts by chunking.
    """
    if not transcript_text or len(transcript_text.strip()) < 50:
        return "Transcript too short for meaningful summarization."

    try:
        # Load local model
        device = 0 if torch.cuda.is_available() else -1
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
        
        # Chunk if text is too long (BART limit is 1024 tokens)
        # Using ~3000 chars as a safe limit for chunking
        if len(transcript_text) > 3000:
            chunks = chunk_text(transcript_text, max_length=3000)
            summaries = []
            for chunk in chunks:
                res = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
                summaries.append(res[0]['summary_text'])
            combined_summary = " ".join(summaries)
            # Re-summarize if the combination is still too long
            if len(combined_summary.split()) > 200:
                final_res = summarizer(combined_summary[:3000], max_length=200, min_length=50, do_sample=False)
                return final_res[0]['summary_text']
            return combined_summary
        else:
            res = summarizer(transcript_text, max_length=200, min_length=50, do_sample=False)
            return res[0]['summary_text']
            
    except Exception as e:
        return f"Error during summarization: {str(e)}"

if __name__ == "__main__":
    # Test
    sample = "The meeting started at 10 AM. We discussed the new project roadmap. John suggested we use React for the frontend. Sarah agreed and mentioned that we should also use FastAPI for the backend. We decided to finalize the architecture by next Friday. There was some concern about the timeline. We will have another sync on Monday."
    print(generate_summary(sample))
