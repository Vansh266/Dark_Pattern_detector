from collections import defaultdict
from schemas import TacticSummary

SEVERITY_POINTS = {"low": 6, "medium": 15, "high": 30}
REPEAT_FACTOR = [1.0, 0.5, 0.25]  # 1st finding of a tactic counts fully, 2nd half, the rest a quarter

TACTICS = {
    "preselected_optional": {
        "title": "Pre-ticked optional choices",
        "how_it_works": (
            "People rarely change default settings (default bias). A box that is "
            "already ticked signs you up for marketing or extras unless you notice "
            "and untick it."
        ),
        "advice": "Untick optional boxes before continuing and read what each one signs you up for.",
    },
    "urgency_scarcity": {
        "title": "Urgency and scarcity pressure",
        "how_it_works": (
            "Countdowns and 'only a few left' messages trigger fear of missing out. "
            "Time pressure makes people skip comparing prices and reading terms. "
            "This tool cannot verify whether the claim is true."
        ),
        "advice": "Pause before buying. Reload the page or check elsewhere. A real deadline will still be there.",
    },
    "confirm_shaming": {
        "title": "Confirm-shaming",
        "how_it_works": (
            "Wording that makes declining feel foolish or guilty turns a neutral "
            "choice into an emotional one, nudging you to accept."
        ),
        "advice": "Ignore the wording. The choice is still yours, and declining is fine if you don't want the offer.",
    },
    "low_prominence_decline": {
        "title": "Hard-to-find decline option",
        "how_it_works": (
            "Accepting is made big and easy while declining is tiny or faint. "
            "The extra effort of finding it wears people down into accepting."
        ),
        "advice": "Look for the small or faint option. It is usually the one that lets you say no.",
    },
        "social_proof": {
        "title": "Social-proof pressure",
        "how_it_works": (
            "Messages about how many others are viewing, buying or reviewing trigger "
            "the bandwagon effect: we assume popular means good or urgent. "
            "These numbers are often impossible to verify."
        ),
        "advice": "Treat such counts as marketing, not evidence. Compare independent reviews.",
    },
    "misdirection": {
        "title": "Wording that steers your choice",
        "how_it_works": (
            "Wording that frames one option as smart and the other as foolish, or "
            "blurs what a choice means, steers decisions through emotion or "
            "confusion rather than information."
        ),
        "advice": "Re-read the options in plain terms: what actually happens if you click each one?",
    },
    "other_manipulative": {
        "title": "Other manipulative design",
        "how_it_works": (
            "The text classifier matched a rarer type of manipulative wording "
            "(such as obstruction, sneaking or forced action). It has few examples "
            "of these, so treat them as leads to check yourself."
        ),
        "advice": "Read this element carefully and check what it commits you to.",
    },
        "trial_unclear_terms": {
        "title": "Unclear free-trial terms",
        "how_it_works": (
            "Free trials that don't say what you will pay afterwards rely on inertia: "
            "people forget to cancel, and the first charge arrives as a surprise."
        ),
        "advice": "Before starting, find the price after the trial and the exact date you would be charged. Set a reminder to cancel.",
    },
    "obscured_billing_terms": {
        "title": "Billing terms hidden in small print",
        "how_it_works": (
            "Renewal and billing conditions in tiny or faint text are technically "
            "disclosed but practically unreadable, so people agree without knowing "
            "what they are committing to."
        ),
        "advice": "Zoom in and read the small print before you start. If you cannot find the total cost, treat that as a warning sign.",
    },
    "extra_fees": {
        "title": "Extra fees added to the price",
        "how_it_works": (
            "Fees that appear after the headline price make the real cost higher than "
            "the number that first attracted you (often called drip pricing)."
        ),
        "advice": "Compare the final total, not the headline price.",
    },
    "monthly_vs_annual": {
        "title": "Monthly price, annual billing",
        "how_it_works": (
            "A low per-month figure anchors your expectation of the cost and can hide "
            "that a whole year is charged up front."
        ),
        "advice": "Look for the total you will be charged today and how often it renews.",
    }
}

DEFAULT_TACTIC = {
    "title": "Other suspicious pattern",
    "how_it_works": "This element matched a pattern associated with manipulative design.",
    "advice": "Read this element carefully before acting on it.",
}


def band_for(score):
    if score == 0:
        return "None detected"
    if score < 20:
        return "Low"
    if score < 45:
        return "Moderate"
    if score < 70:
        return "High"
    return "Severe"


def build_report(findings):
    by_category = defaultdict(list)
    for f in findings:
        by_category[f.category].append(f)

    total = 0.0
    tactics = []
    for category, items in by_category.items():
        items.sort(key=lambda f: SEVERITY_POINTS[f.severity], reverse=True)
        points = 0.0
        for i, f in enumerate(items):
            factor = REPEAT_FACTOR[min(i, len(REPEAT_FACTOR) - 1)]
            weight = f.confidence if f.confidence is not None else 1.0
            points += SEVERITY_POINTS[f.severity] * factor * weight
        total += points

        info = TACTICS.get(category, DEFAULT_TACTIC)
        tactics.append(TacticSummary(
            category=category,
            title=info["title"],
            how_it_works=info["how_it_works"],
            advice=info["advice"],
            count=len(items),
            worst_severity=items[0].severity,
            points=round(points, 1),
            examples=[f.evidence for f in items[:3]],
        ))

    tactics.sort(key=lambda t: t.points, reverse=True)
    score = min(100, round(total))
    band = band_for(score)

    if not findings:
        summary = (
            "No manipulative patterns were detected among the elements this tool checks. "
            "That does not prove the page is free of them."
        )
    else:
        summary = (
            f"{len(findings)} suspicious patterns were found across {len(tactics)} "
            f"tactics. The biggest contributor is \"{tactics[0].title}\". "
            "The score reflects how manipulative the page design looks, "
            "not the intent of the site's owner."
        )

    return score, band, summary, tactics