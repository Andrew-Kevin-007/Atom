def calculate_hit_type(claim: str, opponent_last_claim: str, evidence_type: str) -> str:
    claim_norm = claim.lower()
    opp_norm = opponent_last_claim.lower()
    
    if evidence_type == "production_log":
        if "test" in opp_norm or "contract" in opp_norm:
            return "BLOCK"
            
    if evidence_type == "unit_test":
        if "edge" in opp_norm or "null" in opp_norm or "async" in opp_norm:
            return "BLOCK"
            
    # Word sharing check
    def get_words(s):
        # Basic cleanup: remove common punctuation if any, split by whitespace
        return set(s.replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " ").split())

    claim_words = get_words(claim_norm)
    opp_words = get_words(opp_norm)
    common = claim_words.intersection(opp_words)
    
    if len(common) > 3:
        return "DEFLECT"
        
    return "HIT"

def update_confidence(
    agent_name: str,
    opponent_name: str,
    hit_type: str,
    evidence_type: str,
    scores: dict,
    evidence_weights_attacker: dict
) -> dict:
    weight = evidence_weights_attacker.get(evidence_type, 0)
    
    if hit_type == "HIT":
        scores[agent_name] += weight * 0.3
    elif hit_type == "BLOCK":
        scores[opponent_name] -= weight * 0.2
        
    # Clamp
    for key in scores:
        scores[key] = max(0.0, min(1.0, scores[key]))
        
    return scores

def determine_winner(
    atlas_confidence: float,
    riot_confidence: float,
    rounds: list
) -> dict:
    if atlas_confidence > riot_confidence:
        winner = "ATLAS"
        fix_direction = "Strengthen contracts and add type guards"
    else:
        winner = "RIOT"
        fix_direction = "Add null checks and wrap async calls in try/except"
        
    # Find most frequent evidence type in rounds (assuming rounds is list of dicts with 'evidence_type')
    counts = {}
    for r in rounds:
        etype = r.get("evidence_type", "unknown")
        counts[etype] = counts.get(etype, 0) + 1
        
    most_frequent = "None"
    max_count = -1
    for etype, count in counts.items():
        if count > max_count:
            max_count = count
            most_frequent = etype
            
    reason = f"The debate was primarily decided by {most_frequent} evidence patterns."
    
    return {
        "winner": winner,
        "reason": reason,
        "fix_direction": fix_direction
    }
