def build_context(answers: dict) -> dict:
    """
    Build a context dict from the answers map.
    Answers are keyed by question_id (from questions.json).
    """
    return {
        "business_name":      answers.get("business_name", ""),
        "objective":          answers.get("objective", ""),
        "target_audience":    answers.get("target_audience", ""),
        "location":           answers.get("location", ""),
        "speciality":         answers.get("speciality", ""),
        "tone":               answers.get("tone", ""),
        "menu_items":         answers.get("menu_items", ""),
        "price_range":        answers.get("price_range", ""),
        "promotion_channel":  answers.get("promotion_channel", ""),
        "offers":             answers.get("offers", ""),
    }