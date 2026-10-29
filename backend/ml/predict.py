from pathlib import Path
import joblib

from schemas import Finding
from rules import SEVERITY

MODEL_PATH = Path(__file__).parent / "model.joblib"

# Deployment threshold. The benchmark threshold saved in the model is 0.5,
# but real pages are mostly normal text, so the app is stricter (tune in Step 8).
# Selected using validation data:
# Precision = 0.957
# Recall = 0.887
# F1-score = 0.921
APP_THRESHOLD = 0.50

# Model tactic names -> report categories.
# Obstruction / Sneaking / Forced Action had too few examples to trust,
# so they all become "other_manipulative".
ML_CATEGORY = {
    "Urgency": "urgency_scarcity",
    "Scarcity": "urgency_scarcity",
    "Social Proof": "social_proof",
    "Misdirection": "misdirection",
}

ML_EXPLANATION = {
    "urgency_scarcity": "The wording resembles urgency or scarcity claims that pressure quick decisions.",
    "social_proof": "The wording resembles social-proof claims (how many others are viewing or buying) used to push decisions.",
    "misdirection": "The wording resembles phrasing that steers or guilt-trips users toward one choice.",
    "other_manipulative": "The wording resembles another type of manipulative design. The model is less reliable for this type.",
}

ELIGIBLE_TAGS = {"a", "button", "label", "h1", "h2", "h3", "h4", "p", "span", "strong", "b"}
MAX_WORDS = 60

NEUTRAL_DECLINE_TEXTS = {
    "no thanks",
    "no, thanks",
    "no thank you",
    "not now",
    "maybe later",
    "skip",
}


def is_neutral_decline(text):
    normalized = " ".join(
        text.lower().replace("\u2019", "'").split()
    ).strip(" .!?")

    return normalized in NEUTRAL_DECLINE_TEXTS

_bundle = None


def model_available():
    return MODEL_PATH.exists()


def _load():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def predict_texts(texts):
    """Returns (probability, tactic) for each text. tactic is None if below the threshold."""
    bundle = _load()
    probs = bundle["pipeline"].predict_proba(texts)[:, 1]

    flagged = [i for i, p in enumerate(probs) if p >= APP_THRESHOLD]
    tactics = {}
    if flagged:
        names = bundle["category_pipeline"].predict([texts[i] for i in flagged])
        tactics = dict(zip(flagged, names))

    return [(float(probs[i]), tactics.get(i)) for i in range(len(texts))]


def run_ml(elements):
    candidates = []

    for el in elements:

        if el.tag not in ELIGIBLE_TAGS:
            continue

        words = len(el.text.split())

        if words == 0 or words > MAX_WORDS:
            continue

        # Prevent ordinary refusal text from producing
        # false-positive ML detections.
        if is_neutral_decline(el.text):
            continue

        candidates.append(el)
    if not candidates:
        return []

    unique_texts = list(dict.fromkeys(el.text for el in candidates))
    scored = dict(zip(unique_texts, predict_texts(unique_texts)))

    findings = []
    for el in candidates:
        prob, tactic = scored[el.text]
        if tactic is None:
            continue
        category = ML_CATEGORY.get(tactic, "other_manipulative")
        findings.append(Finding(
            element_id=el.id,
            category=category,
            method="ml",
            confidence=round(prob, 2),
            severity=SEVERITY[category],
            evidence=f'Text classifier flagged this wording as "{tactic}" (confidence {prob:.0%})',
            explanation=ML_EXPLANATION[category],
        ))
    return findings