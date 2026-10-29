
from main import analyze
from schemas import AnalyzeRequest, PageElement, Rect, Styles


def make_element(
    text,
    element_id=1,
    tag="button",
    checked=False,
    input_type="",
    font_size="16px",
):
    return PageElement(
        id=element_id,
        tag=tag,
        text=text,
        checked=checked,
        inputType=input_type,
        disabled=False,
        required=False,
        rect=Rect(
            top=0,
            left=0,
            width=200,
            height=40,
        ),
        styles=Styles(
            fontSize=font_size,
            color="rgb(0, 0, 0)",
            backgroundColor="rgb(255, 255, 255)",
            opacity="1",
        ),
    )


def scan(elements, mode="hybrid"):
    request = AnalyzeRequest(
        url="https://example.com/test",
        elements=elements,
        mode=mode,
    )
    return analyze(request)


# TEST 1: Normal interface
response = scan([
    make_element("Add to cart", 1),
    make_element("No thanks", 2),
])

assert len(response.findings) == 0
assert response.risk_score == 0
print("PASS 1: Normal interface not flagged")


# TEST 2: Scarcity detected by rules + ML
response = scan([
    make_element("Only 2 left in stock!")
])

scarcity = [
    f for f in response.findings
    if f.category == "urgency_scarcity"
]

assert len(scarcity) == 1
assert scarcity[0].method == "rule+ml"
assert len(response.findings) == 1

print("PASS 2: Scarcity detected and merged")


# TEST 3: Confirm-shaming
response = scan([
    make_element("No thanks, I hate saving money")
])

shaming = [
    f for f in response.findings
    if f.category == "confirm_shaming"
]

assert len(shaming) == 1
assert shaming[0].method == "rule+ml"

print("PASS 3: Confirm-shaming detected")


# TEST 4: Social proof category resolution
response = scan([
    make_element(
        "12 people are viewing this right now"
    )
])

social = [
    f for f in response.findings
    if f.category == "social_proof"
]

assert len(social) == 1
assert social[0].method == "rule+ml"
assert len(response.findings) == 1

print("PASS 4: Social proof category preserved")


# TEST 5: Preselected paid add-on
response = scan([
    make_element(
        "Add a 2-year warranty for Rs. 299",
        tag="input",
        checked=True,
        input_type="checkbox",
    )
])

assert any(
    f.category == "preselected_optional"
    for f in response.findings
)

print("PASS 5: Preselected paid add-on detected")


# TEST 6: Clearly disclosed delivery fee
response = scan([
    make_element(
        "Delivery fee Rs. 50 included in total",
        tag="p",
    )
])

assert not any(
    f.category == "extra_fees"
    for f in response.findings
)

print("PASS 6: Disclosed fee not flagged")


# TEST 7: Later-added fee
response = scan([
    make_element(
        "Convenience fee Rs. 49 added at checkout",
        tag="p",
    )
])

assert any(
    f.category == "extra_fees"
    for f in response.findings
)

print("PASS 7: Later-added fee flagged")


# TEST 8: Neutral refusal with low visibility
response = scan([
    make_element(
        "No thanks",
        font_size="9px",
    )
])

assert any(
    f.category == "low_prominence_decline"
    and f.method == "rule"
    for f in response.findings
)

print("PASS 8: Low-prominence refusal detected")


# TEST 9: Detection modes
element = make_element("Only 2 left in stock!")

rules_response = scan([element], mode="rules")
ml_response = scan([element], mode="ml")
hybrid_response = scan([element], mode="hybrid")

assert rules_response.findings
assert ml_response.findings

assert all(
    f.method == "rule"
    for f in rules_response.findings
)

assert all(
    f.method == "ml"
    for f in ml_response.findings
)

assert len(hybrid_response.findings) == 1
assert hybrid_response.findings[0].method == "rule+ml"

print("PASS 9: All detection modes work")


# TEST 10: ML agreement must not lower a rule-based score

test_texts = [
    "No thanks, I hate saving money",
    "12 people are viewing this right now",
    "Only 2 left in stock!",
]

for text in test_texts:
    element = make_element(text)

    rules_result = scan(
        [element],
        mode="rules"
    )

    hybrid_result = scan(
        [element],
        mode="hybrid"
    )

    assert hybrid_result.risk_score == rules_result.risk_score, (
        f"Score mismatch for '{text}': "
        f"rules={rules_result.risk_score}, "
        f"hybrid={hybrid_result.risk_score}"
    )

print("PASS 10: ML agreement does not reduce rule scores")


print("\nALL 10 HYBRID INTEGRATION TESTS PASSED")
