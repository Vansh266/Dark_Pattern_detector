import re
from rules import (
    normalize, make_finding, parse_px, text_contrast,
    SMALL_FONT_PX, MIN_CONTRAST,
)

# Currency amounts: $9.99  ₹299  €5  £3  Rs. 499  INR 299  (written with \u escapes so file encoding can't break it)
AMOUNT = re.compile(
    r"(?:[$\u20b9\u20ac\u00a3]\s?|\b(?:rs\.?|inr|usd|eur)\s?)\d[\d,]*(?:\.\d+)?"
)

TRIAL = re.compile(
    r"free trial|\d+[- ]days? (?:free )?trial|free for \d+ (?:days?|weeks?|months?)"
    r"|try (?:it |us )?free|start(?:ing)? (?:your |a )?free"
)
RENEWAL_WORDS = re.compile(r"\b(?:then|after|renews?|renewal|billed|charged|auto-?renew)")
BILLING_TERMS = re.compile(
    r"auto-?renew|renews? (?:automatically|at|for|on)|billed (?:monthly|annually|yearly|every)"
    r"|will be charged|cancell?ation fee|recurring (?:payment|charge|billing)"
    r"|charged (?:monthly|annually|yearly|after)"
)
MONTHLY = re.compile(r"/\s?(?:mo|month)\b|per month|a month|monthly")
ANNUAL_BILLED = re.compile(r"(?:billed|charged|paid) (?:annually|yearly|once a year|upfront)")
YEARLY_TOTAL = re.compile(r"per year|/\s?(?:yr|year)\b|annually|yearly|a year|total")
FEE = re.compile(r"(?:service|convenience|handling|processing|booking|platform|delivery) fees?")
FEE_LATE = re.compile(
    r"added at checkout|added during checkout|"
    r"revealed at (?:checkout|payment)|"
    r"applied at checkout|"
    r"charged at checkout|"
    r"extra charge at checkout|"
    r"not included in (?:the )?(?:shown |displayed )?price"
)

FEE_INCLUDED = re.compile(
    r"included in (?:the )?(?:total|price)|"
    r"already included|"
    r"no additional (?:fees|charges)|"
    r"no (?:service|delivery|processing|booking) fee|"
    r"all fees included"
)


def short(text):
    return text.strip()[:60]


def obscured_reasons(el):
    """Measured reasons why an element's text is hard to read."""
    reasons = []
    size = parse_px(el.styles.fontSize)
    if size is not None and size <= SMALL_FONT_PX:
        reasons.append(f"font size {size:g}px")
    ratio = text_contrast(el.styles)
    if ratio is not None and ratio < MIN_CONTRAST:
        reasons.append(f"text contrast {ratio:.1f}:1")
    try:
        opacity = float(el.styles.opacity)
        if opacity < 0.6:
            reasons.append(f"opacity {opacity:g}")
    except ValueError:
        pass
    return reasons


def run_pricing(elements):
    findings = []
    seen = set()   # (category, text) so a parent and child with the same text count once

    def add(el, category, evidence, explanation):
        key = (category, normalize(el.text))
        if key in seen:
            return
        seen.add(key)
        findings.append(make_finding(el, category, evidence, explanation))

    items = [(el, normalize(el.text)) for el in elements if el.tag != "input"]
    trial_els = [el for el, t in items if TRIAL.search(t)]
    has_offer = bool(trial_els) or any(AMOUNT.search(t) for _, t in items)

    # 1. Free trial with no renewal price or billing date on the page
    if trial_els:
        disclosed = any(AMOUNT.search(t) and RENEWAL_WORDS.search(t) for _, t in items)
        if not disclosed:
            el = trial_els[0]
            add(el, "trial_unclear_terms",
                f'Trial offer ("{short(el.text)}") but no renewal price or billing date appears on this page',
                "Trials that hide what you pay afterwards rely on people forgetting to cancel. "
                "The terms may be shown on a later page, which this tool does not check.")

    # 2. Billing terms shown in tiny, faint or see-through text
    if has_offer:
        for el, t in items:
            m = BILLING_TERMS.search(t)
            if not m:
                continue
            reasons = obscured_reasons(el)
            if reasons:
                add(el, "obscured_billing_terms",
                    f'Billing term "{m.group(0)}" is hard to read: ' + ", ".join(reasons),
                    "Renewal and billing conditions in tiny or faint text are technically disclosed "
                    "but practically unreadable.")

    # 3. Detect potentially delayed or hidden extra fees
    for el, t in items:

        # A fee and monetary amount must both be present
        if not (FEE.search(t) and AMOUNT.search(t)):
            continue

        # Clearly included fees are not automatically suspicious
        if FEE_INCLUDED.search(t):
            continue

        # Flag language indicating later fee disclosure
        if FEE_LATE.search(t):
            add(
                el,
                "extra_fees",
                f'Potentially delayed fee: "{short(el.text)}"',
                (
                    "The page indicates that an additional fee may "
                    "be applied later in the purchase process. "
                    "Check the final price before proceeding."
                )
            )
            
    # 4. Monthly price shown, annual billing mentioned, no yearly total visible
    monthly_els = [el for el, t in items if AMOUNT.search(t) and MONTHLY.search(t)]
    annual_els = [el for el, t in items if ANNUAL_BILLED.search(t)]
    yearly_total_shown = any(AMOUNT.search(t) and YEARLY_TOTAL.search(t) for _, t in items)
    if monthly_els and annual_els and not yearly_total_shown:
        el = annual_els[0]
        add(el, "monthly_vs_annual",
            f'Monthly price "{short(monthly_els[0].text)}" is shown, but the page says billing is annual and shows no yearly total',
            "A low per-month figure can hide that a whole year is charged up front.")

    return findings