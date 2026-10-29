from schemas import PageElement, Rect, Styles
from ml.predict import run_ml
from rules import run_rules
from merge import merge_findings


def make_element(text):
    return PageElement(
        id=1,
        tag="button",
        text=text,
        rect=Rect(
            top=0,
            left=0,
            width=200,
            height=40
        ),
        styles=Styles()
    )


# Test 1: Neutral refusal phrases
neutral_texts = [
    "No thanks",
    "No, thanks",
    "No thank you",
    "Maybe later",
]

for text in neutral_texts:
    findings = run_ml([make_element(text)])

    assert len(findings) == 0, (
        f"False positive: {text}"
    )

    print(f"PASS: Neutral text ignored - {text}")


# Test 2: Suspicious scarcity wording
element = make_element("Only 2 left in stock!")

findings = run_ml([element])

assert any(
    f.category == "urgency_scarcity"
    for f in findings
)

print("PASS: Scarcity still detected")


# Test 3: Confirm-shaming in hybrid detection
element = make_element(
    "No thanks, I hate saving money"
)

rule_findings = run_rules([element])
ml_findings = run_ml([element])

merged = merge_findings(
    rule_findings,
    ml_findings
)

assert any(
    f.category == "confirm_shaming"
    for f in merged
)

print("PASS: Confirm-shaming detected by hybrid system")

print("\nALL TESTS PASSED")

print("\n=== TEST 4: ML DETECTION AT NEW THRESHOLD ===")

element = make_element(
    "No thanks, I hate saving money"
)

ml_findings = run_ml([element])

assert len(ml_findings) > 0, (
    "ML failed to detect confirm-shaming wording"
)

print("PASS: Suspicious wording detected by ML")

print("Detected category:", ml_findings[0].category)
print("Confidence:", ml_findings[0].confidence)