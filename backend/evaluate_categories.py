
import joblib
import pandas as pd
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

from ml.predict import APP_THRESHOLD, is_neutral_decline

MODEL_PATH = Path(__file__).parent / "ml" / "model.joblib"

URL = (
    "https://raw.githubusercontent.com/yamanalab/"
    "ec-darkpattern/master/dataset/dataset.tsv"
)

# Step 1: Load trained models
bundle = joblib.load(MODEL_PATH)

binary_model = bundle["pipeline"]
category_model = bundle["category_pipeline"]

print("=== MODEL INFORMATION ===")
print("Application threshold:", APP_THRESHOLD)
print("Available categories:", list(category_model.classes_))

# Step 2: Load and preprocess dataset
df = pd.read_csv(URL, sep="\t")

df = df[
    ["text", "label", "Pattern Category", "page_id"]
].dropna()

df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"] != ""]
df = df.drop_duplicates(subset="text")
df["label"] = df["label"].astype(int)

if len(df) != 2349:
    raise RuntimeError(
        f"Unexpected dataset size: {len(df)}. "
        "Original training dataset had 2349 samples."
    )

# Step 3: Reconstruct original group split
gss = GroupShuffleSplit(
    n_splits=1,
    test_size=0.3,
    random_state=42
)

train_idx, temp_idx = next(
    gss.split(df, df["label"], df["page_id"])
)

train_df = df.iloc[train_idx]
temp_df = df.iloc[temp_idx]

gss2 = GroupShuffleSplit(
    n_splits=1,
    test_size=0.5,
    random_state=42
)

val_idx, test_idx = next(
    gss2.split(
        temp_df,
        temp_df["label"],
        temp_df["page_id"]
    )
)

val_df = temp_df.iloc[val_idx]
test_df = temp_df.iloc[test_idx]

assert len(train_df) == 1609
assert len(val_df) == 354
assert len(test_df) == 386

assert set(train_df["page_id"]).isdisjoint(
    set(test_df["page_id"])
)
assert set(val_df["page_id"]).isdisjoint(
    set(test_df["page_id"])
)

print("\nTest samples:", len(test_df))

# Step 4: Evaluate deployed binary classifier
texts = test_df["text"].tolist()
y_true = test_df["label"].to_numpy()

probabilities = binary_model.predict_proba(texts)[:, 1]

binary_predictions = [
    int(
        probability >= APP_THRESHOLD
        and not is_neutral_decline(text)
    )
    for text, probability in zip(texts, probabilities)
]

print("\n=== BINARY CLASSIFIER: TEST RESULTS ===")

print(
    classification_report(
        y_true,
        binary_predictions,
        labels=[0, 1],
        target_names=["Normal", "Dark Pattern"],
        digits=3,
        zero_division=0
    )
)

print("Confusion matrix:")
print(confusion_matrix(y_true, binary_predictions, labels=[0, 1]))

# Step 5: Evaluate category classifier on known
# dark-pattern examples
dark_test = test_df[test_df["label"] == 1]

category_true = dark_test["Pattern Category"].tolist()
category_pred = category_model.predict(
    dark_test["text"].tolist()
)

print("\n=== CATEGORY CLASSIFICATION REPORT ===")

print(
    classification_report(
        category_true,
        category_pred,
        digits=3,
        zero_division=0
    )
)

print(
    "Category accuracy:",
    round(accuracy_score(category_true, category_pred), 3)
)

print("\n=== CATEGORY SUPPORT ===")
print(dark_test["Pattern Category"].value_counts())

# Step 6: Evaluate complete binary + category pipeline
# A dark example is correct only if it is first
# detected and then assigned the correct category.
dark_binary_predictions = [
    predicted
    for actual, predicted in zip(y_true, binary_predictions)
    if actual == 1
]

correct_end_to_end = sum(
    detected == 1 and predicted == actual
    for detected, predicted, actual in zip(
        dark_binary_predictions,
        category_pred,
        category_true
    )
)

print("\n=== END-TO-END CATEGORY RECALL ===")
print(
    "Correctly detected and categorized:",
    correct_end_to_end,
    "out of",
    len(category_true)
)

print(
    "End-to-end category recall:",
    round(correct_end_to_end / len(category_true), 3)
)

# Step 7: Display category classification mistakes
print("\n=== CATEGORY MISCLASSIFICATIONS ===")

mistakes = [
    (text, actual, predicted)
    for text, actual, predicted in zip(
        dark_test["text"],
        category_true,
        category_pred
    )
    if actual != predicted
]

for text, actual, predicted in mistakes[:10]:
    print("\nText:", text[:120])
    print("Actual:", actual)
    print("Predicted:", predicted)

print("\nTotal category mistakes:", len(mistakes))
print("\nEvaluation complete.")
