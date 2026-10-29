
# Dark Pattern Detector — ML Evaluation

## 1. Model Architecture

The system uses a two-stage machine learning architecture:

1. Binary classification: Dark Pattern vs Normal
2. Multiclass classification: Predicts the dark-pattern category

Both models use:
- TF-IDF vectorization (unigrams and bigrams)
- Logistic Regression
- Balanced class weights

The ML engine operates alongside rule-based detection
in the hybrid detection pipeline.

## 2. Dataset

Source: Yamanaka Lab EC Dark Pattern Dataset

Repository:
https://github.com/yamanalab/ec-darkpattern

Original samples: 2,356
Samples after preprocessing: 2,349

Dataset splitting:
- Training: 1,609 samples
- Validation: 354 samples
- Testing: 386 samples

GroupShuffleSplit was used with page_id grouping,
random_state=42, and separate validation/test groups.

## 3. Model Configuration

Machine learning library: scikit-learn 1.6.1

Binary model:
- TF-IDF: ngram_range=(1, 2)
- min_df=2
- sublinear_tf=True
- LogisticRegression(max_iter=1000,
  class_weight="balanced")

Application classification threshold: 0.50

An exact-match neutral-refusal safeguard is applied
at inference time to reduce known false positives.

## 4. Binary Classification Results

Evaluation: Reconstructed test split (386 samples)

| Metric | Result |
|---|---:|
| Accuracy | 93.8% |
| Dark-pattern precision | 94.7% |
| Dark-pattern recall | 91.4% |
| Dark-pattern F1-score | 93.0% |

Confusion matrix:

                 Predicted Normal   Predicted Dark
Actual Normal           202                9
Actual Dark              15              160

These results use the application threshold of 0.50.

## 5. Category Classification Results

Evaluation: 175 known dark-pattern examples

| Category | F1-score | Support |
|---|---:|---:|
| Misdirection | 0.912 | 30 |
| Obstruction | 0.909 | 5 |
| Scarcity | 0.973 | 58 |
| Sneaking | 0.000 | 1 |
| Social Proof | 0.953 | 51 |
| Urgency | 0.918 | 30 |

Overall category accuracy: 94.3%
Macro F1-score: 0.778
Weighted F1-score: 0.940

Forced Action had no examples in this test split.

## 6. End-to-End Classification

Total actual dark-pattern examples: 175

Correctly detected by the binary classifier: 160

Correctly detected and categorized: 154

End-to-end category recall: 88.0%

This metric evaluates both classification stages together.

## 7. Hybrid Integration Tests

10 integration tests passed, covering:

- Normal interface text
- Scarcity detection
- Confirm-shaming detection
- Social-proof category resolution
- Preselected paid add-ons
- Clearly disclosed fees
- Potentially delayed additional fees
- Low-prominence refusal controls
- Rules-only, ML-only, and hybrid modes
- Risk-scoring consistency

These are controlled backend integration tests,
not full browser-level performance measurements.

## 8. Limitations

1. The model is trained on a relatively small dataset.
2. Rare categories are insufficiently represented.
3. Sneaking detection was unsuccessful on its single
   available test example.
4. Model probabilities have not been calibrated.
5. Text classification cannot verify whether scarcity,
   urgency, or popularity claims are truthful.
6. The evaluation does not demonstrate performance
   across all real-world websites.
7. The original test split was previously inspected
   during development, so this is not an entirely
   untouched blind evaluation.
8. The neutral-refusal safeguard is a limited heuristic,
   not a comprehensive solution to false positives.

## 9. Reproducibility

Recommended environment:
- Python 3.11
- scikit-learn 1.6.1

From the backend directory:

python evaluate_threshold.py
python evaluate_categories.py
python test_hybrid_integration.py

These scripts reproduce threshold comparisons,
classification evaluation, and controlled integration
tests against the saved model.
