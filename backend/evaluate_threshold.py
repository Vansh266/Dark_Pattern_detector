
import joblib
import pandas as pd
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from ml.predict import is_neutral_decline

# Load the actual trained model
MODEL_PATH = Path(__file__).parent / "ml" / "model.joblib"
bundle = joblib.load(MODEL_PATH)
model = bundle["pipeline"]

# Same dataset used in the original training notebook
URL = (
    "https://raw.githubusercontent.com/yamanalab/"
    "ec-darkpattern/master/dataset/dataset.tsv"
)

df = pd.read_csv(URL, sep="\t")

# Reproduce the notebook's preprocessing
df = df[
    ["text", "label", "Pattern Category", "page_id"]
].dropna()

df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"] != ""]
df = df.drop_duplicates(subset="text")
df["label"] = df["label"].astype(int)

# Check expected dataset size
if len(df) != 2349:
    raise RuntimeError(
        "Dataset has changed since training. "
        f"Expected 2349 rows, found {len(df)}."
    )

# Recreate original group-based train/validation/test split
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

# Check the expected split sizes and group separation
assert len(train_df) == 1609
assert len(val_df) == 354
assert len(test_df) == 386

assert set(train_df["page_id"]).isdisjoint(
    set(val_df["page_id"])
)
assert set(train_df["page_id"]).isdisjoint(
    set(test_df["page_id"])
)
assert set(val_df["page_id"]).isdisjoint(
    set(test_df["page_id"])
)

print("=== VALIDATION DATA ===")
print("Training samples:", len(train_df))
print("Validation samples:", len(val_df))
print("Test samples reserved:", len(test_df))

# Obtain probabilities on validation data only
texts = val_df["text"].tolist()
y_true = val_df["label"].to_numpy()

probabilities = model.predict_proba(texts)[:, 1]

# Apply the same neutral-text safeguard as run_ml()
neutral_mask = [
    is_neutral_decline(text)
    for text in texts
]

print("\n=== THRESHOLD EVALUATION ===")
print(
    f"{'Threshold':<12}"
    f"{'Precision':<12}"
    f"{'Recall':<12}"
    f"{'F1':<12}"
    f"{'FPR':<12}"
)

thresholds = [
    0.40, 0.45, 0.50, 0.55,
    0.60, 0.65, 0.70, 0.75, 0.80
]

for threshold in thresholds:

    predictions = [
        int(prob >= threshold and not neutral)
        for prob, neutral in zip(
            probabilities, neutral_mask
        )
    ]

    precision = precision_score(
        y_true, predictions, zero_division=0
    )

    recall = recall_score(
        y_true, predictions, zero_division=0
    )

    f1 = f1_score(
        y_true, predictions, zero_division=0
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true, predictions, labels=[0, 1]
    ).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0

    print(
        f"{threshold:<12.2f}"
        f"{precision:<12.3f}"
        f"{recall:<12.3f}"
        f"{f1:<12.3f}"
        f"{fpr:<12.3f}"
    )

print("\nThreshold evaluation completed.")
print("Do not use the test set to choose a threshold.")
