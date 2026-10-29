from schemas import Finding
from merge import merge_findings


def create_finding(element_id, category, method):
    return Finding(
        element_id=element_id,
        category=category,
        method=method,
        confidence=0.90 if method == "ml" else None,
        severity="low",
        evidence=f"{method} detected {category}",
        explanation=f"Detected by {method}"
    )


# Test 1: Same element, related categories
rule = create_finding(1, "urgency_scarcity", "rule")
ml = create_finding(1, "social_proof", "ml")

result = merge_findings([rule], [ml])

assert len(result) == 1
assert result[0].category == "social_proof"
assert result[0].method == "rule+ml"
print("PASS: Social proof merged correctly")


# Test 2: Same element, same category
rule = create_finding(2, "urgency_scarcity", "rule")
ml = create_finding(2, "urgency_scarcity", "ml")

result = merge_findings([rule], [ml])

assert len(result) == 1
assert result[0].method == "rule+ml"
print("PASS: Duplicate finding merged")


# Test 3: Different elements must remain separate
rule = create_finding(3, "urgency_scarcity", "rule")
ml = create_finding(4, "urgency_scarcity", "ml")

result = merge_findings([rule], [ml])

assert len(result) == 2
print("PASS: Independent elements preserved")


# Test 4: Confirm-shaming should retain its category
rule = create_finding(5, "confirm_shaming", "rule")
ml = create_finding(5, "misdirection", "ml")

result = merge_findings([rule], [ml])

assert len(result) == 1
assert result[0].category == "confirm_shaming"
print("PASS: Confirm-shaming correctly retained")