def calculate_productivity_score(action_items, decisions, risks, sentiment):
    """
    Calculate score out of 100 based on insights.
    +30 points if action items found
    +25 points if decisions found
    +20 points if sentiment is positive
    +15 points if risks are low (less than 3)
    +10 points base score always
    """
    score = 10  # Base score
    
    if action_items:
        score += 30
        
    if decisions:
        score += 25
        
    if sentiment.lower() == "positive":
        score += 20
        
    if len(risks) < 3:
        score += 15
        
    # Cap at 100
    score = min(score, 100)
    
    label = "Low"
    if score >= 80:
        label = "High"
    elif score >= 50:
        label = "Medium"
        
    return score, label

if __name__ == "__main__":
    # Test
    s, l = calculate_productivity_score(["Do X"], ["Decision Y"], [], "positive")
    print(f"Score: {s}, Label: {l}")
