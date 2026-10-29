from pathlib import Path

import joblib
import sklearn

MODEL_PATH = Path(__file__).parent / "ml" / "model.joblib"
APP_THRESHOLD = 0.65

print("=== ML MODEL VERIFICATION ===")
print("scikit-learn version:", sklearn.__version__)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

bundle = joblib.load(MODEL_PATH)

print("\nModel components:", list(bundle.keys()))
print("Saved threshold:", bundle.get("threshold"))

if "pipeline" not in bundle:
    raise RuntimeError("Binary classification model missing")

if "category_pipeline" not in bundle:
    raise RuntimeError("Category classifier missing")

binary_model = bundle["pipeline"]
category_model = bundle["category_pipeline"]

print("\n=== TEST PREDICTIONS ===")

samples = [
    "Add to cart",
    "Contact us",
    "Sign in",
    "No thanks",
    "Your cart is empty",
    "Free delivery on orders above 499",
    "Subscribe to our newsletter",
    "Only 2 left in stock!",
    "Hurry! Offer ends in 09:59",
    "12 people are viewing this right now",
    "No thanks, I hate saving money",
    "No thanks, I'd rather pay full price",
]

probabilities = binary_model.predict_proba(samples)[:, 1]

for text, probability in zip(samples, probabilities):

    detected = probability >= APP_THRESHOLD

    if detected:
        category = category_model.predict([text])[0]
    else:
        category = "Not flagged"

    print("\nText:", text)
    print("Probability:", round(float(probability), 3))
    print("Detected:", detected)
    print("Category:", category)

print("\n=== VERIFICATION COMPLETED ===")