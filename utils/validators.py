def validate_answers(questions: list, answers: dict) -> list:
    """
    Validate that all required (visible) questions have been answered.
    Returns a list of error strings; empty list means valid.
    """
    errors = []
    for q in questions:
        qid = q["id"]
        dep = q.get("depends_on")
        # Skip questions whose dependency isn't satisfied
        if dep and answers.get(dep["question_id"]) != dep["value"]:
            continue
        val = answers.get(qid, "").strip()
        if not val:
            errors.append(f"'{q['label']}' is required.")
    return errors
