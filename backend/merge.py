# If the model and a rule flag the same element for related reasons,
# keep ONE finding (marked "rule+ml") instead of counting it twice.
MERGES_INTO = {
    "misdirection": ["confirm_shaming"],
    "social_proof": ["urgency_scarcity"],
}


def merge_findings(rule_findings, ml_findings):
    merged = list(rule_findings)
    for m in ml_findings:
        target = None
        for f in merged:
            if f.element_id != m.element_id:
                continue
            if f.category == m.category or f.category in MERGES_INTO.get(m.category, []):
                target = f
                break
        if target is None:
            merged.append(m)
        else:
            target.method = "rule+ml"
            target.confidence = m.confidence
            target.evidence = target.evidence + " | " + m.evidence
    # Correct category when ML identifies social proof
    # that the urgency rule also detected
            if (
                m.category == "social_proof"
                and target.category == "urgency_scarcity"
            ):
                target.category = "social_proof"
                target.severity = m.severity
                target.explanation = m.explanation            
    return merged