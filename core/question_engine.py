import json
import os

def load_questions(path=None):
    if path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "config", "questions.json")
    with open(path, "r") as f:
        return json.load(f)

def get_visible_questions(questions, answers):
    visible = []
    for q in questions:
        dep = q.get("depends_on")
        if dep is None:
            visible.append(q)
        else:
            # Support both old ("question_id") and dep-style dicts
            dep_id = dep.get("question_id") or dep.get("id")
            dep_val = dep.get("value")
            if answers.get(dep_id) == dep_val:
                visible.append(q)
    return visible