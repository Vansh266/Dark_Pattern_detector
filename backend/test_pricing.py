from schemas import PageElement, Rect, Styles
from pricing import run_pricing


def create_element(text, element_id):
    return PageElement(
        id=element_id,
        tag="p",
        text=text,
        rect=Rect(top=0, left=0, width=200, height=30),
        styles=Styles()
    )


test_cases = [
    ("Delivery fee ₹50 included in total", False),
    ("Convenience fee ₹49 added at checkout", True),
    ("Service fee ₹99 revealed at payment", True),
    ("No delivery fee", False),
    ("Platform fee ₹25 already included", False),
]

print("=== PRICING DETECTION TESTS ===")

for index, (text, expected) in enumerate(test_cases):
    element = create_element(text, index)

    findings = run_pricing([element])

    detected = any(
        finding.category == "extra_fees"
        for finding in findings
    )

    passed = detected == expected

    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{text} | "
        f"Detected: {detected}"
    )