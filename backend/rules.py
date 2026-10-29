import re
from schemas import Finding, PageElement

# Severity methodology (document this in your report):
#   low    = wording that may be legitimate and cannot be verified by this tool
#   medium = interface design that pushes, hides or pre-decides a user's choice
#   high   = reserved for hidden costs / hidden cancellation (added later)
SEVERITY = {
    "preselected_optional": "medium",
    "urgency_scarcity": "low",
    "confirm_shaming": "medium",
    "low_prominence_decline": "medium",
    "social_proof": "low",
    "misdirection": "medium",
    "other_manipulative": "low",
    "trial_unclear_terms": "medium",
    "obscured_billing_terms": "high",
    "extra_fees": "low",
    "monthly_vs_annual": "medium",
}
OPTIONAL_WORDS = [
    "offers",
    "newsletter",
    "partners",
    "promotions",
    "marketing",
    "deals",
    "updates",
    "subscribe",
    "third party",
    "third-party",
    "warranty",
    "insurance",
    "protection plan",
    "gift wrap",
    "gift wrapping",
    "donation",
    "extended coverage",
    "add-on",
    "optional extra",
]

URGENCY_PATTERNS = [
    r"only \d+ (left|remaining)",
    r"\bhurry\b",
    r"(offer|sale|deal) ends",
    r"ends in \d",
    r"limited time",
    r"last chance",
    r"selling fast",
    r"almost (gone|sold out)",
    r"\d+ (people|others|customers) (are )?(viewing|looking|watching)",
]

SHAMING_PATTERNS = [
    r"no,? thanks?,? i (hate|don'?t|do not|prefer|like|would rather|'d rather)",
    r"i (hate|don'?t like|do not like) (saving|discounts|deals|money)",
    r"i('d| would) rather (pay|miss|not)",
    r"no,? i (don'?t|do not) (want|need|like)",
    r"i (don'?t|do not) want to (save|be|get)",
]

DECLINE_WORDS = [
    "no thanks", "no, thanks", "no thank you", "not now",
    "maybe later", "skip", "decline", "i'll pass",
]

SMALL_FONT_PX = 11
MIN_CONTRAST = 3.0


def normalize(text: str) -> str:
    # lowercase, and turn curly apostrophes into normal ones
    return text.lower().replace("\u2019", "'").strip()


def make_finding(el, category, evidence, explanation):
    return Finding(
        element_id=el.id,
        category=category,
        method="rule",
        confidence=None,
        severity=SEVERITY[category],
        evidence=evidence,
        explanation=explanation,
    )


# ---------- colour helpers (for the contrast check) ----------

def parse_color(css):
    if not css.startswith("rgb"):
        return None
    nums = re.findall(r"[\d.]+", css)
    if len(nums) < 3:
        return None
    r, g, b = float(nums[0]), float(nums[1]), float(nums[2])
    a = float(nums[3]) if len(nums) > 3 else 1.0
    return (r, g, b, a)


def luminance(r, g, b):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(fg, bg):
    l1 = luminance(fg[0], fg[1], fg[2])
    l2 = luminance(bg[0], bg[1], bg[2])
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def text_contrast(styles):
    fg = parse_color(styles.color)
    if fg is None:
        return None
    bg = parse_color(styles.backgroundColor)
    if bg is None or bg[3] == 0:      # transparent background: assume white page
        bg = (255, 255, 255, 1.0)
    return contrast_ratio(fg, bg)


def parse_px(value):
    try:
        return float(value.replace("px", "").strip())
    except ValueError:
        return None


# ---------- the four rules ----------

def check_preselected(el):
    if el.tag != "input":
        return None

    # Only checkbox inputs are relevant
    if el.inputType != "checkbox":
        return None

    # Ignore disabled or mandatory checkboxes
    if el.disabled or el.required:
        return None

    if not el.checked:
        return None

    text = normalize(el.text)

    hits = [
        word for word in OPTIONAL_WORDS
        if word in text
    ]

    if not hits:
        return None

    return make_finding(
        el,
        "preselected_optional",
        f'Preselected optional choice detected: "{el.text}"',
        "An optional choice is already selected, potentially causing "
        "unwanted subscriptions, marketing consent, or extra charges."
    )

def check_urgency(el):
    if el.tag == "input":      # input text is borrowed from its label, which is checked separately
        return None
    text = normalize(el.text)
    for pattern in URGENCY_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return make_finding(
                el, "urgency_scarcity",
                f'Urgency or scarcity wording: "{m.group(0)}"',
                "Urgency and scarcity claims can pressure quick decisions. This tool cannot check whether the claim is true.",
            )
    return None


def check_confirm_shaming(el):
    if el.tag not in ("a", "button"):
        return None
    text = normalize(el.text)
    for pattern in SHAMING_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return make_finding(
                el, "confirm_shaming",
                f'Refusal wording: "{m.group(0)}"',
                "The wording may make users feel guilty or foolish for declining the offer.",
            )
    return None


def check_low_prominence_decline(el):
    if el.tag not in ("a", "button"):
        return None
    text = normalize(el.text)
    if not any(w in text for w in DECLINE_WORDS):
        return None

    problems = []
    size = parse_px(el.styles.fontSize)
    if size is not None and size <= SMALL_FONT_PX:
        problems.append(f"font size {size:g}px")
    ratio = text_contrast(el.styles)
    if ratio is not None and ratio < MIN_CONTRAST:
        problems.append(f"text contrast {ratio:.1f}:1")
    if not problems:
        return None

    return make_finding(
        el, "low_prominence_decline",
        "Decline option is hard to see: " + ", ".join(problems),
        "A tiny or faint decline option makes refusing harder than accepting.",
    )


CHECKS = [
    check_preselected,
    check_urgency,
    check_confirm_shaming,
    check_low_prominence_decline,
]


def run_rules(elements):
    findings = []
    seen = set()
    for el in elements:
        for check in CHECKS:
            f = check(el)
            if f is None:
                continue
            key = (f.element_id, f.category)    # one finding per element per category
            if key in seen:
                continue
            seen.add(key)
            findings.append(f)
    return findings