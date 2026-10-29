from schemas import PageElement, Rect, Styles
from rules import check_preselected, OPTIONAL_WORDS, normalize

element = PageElement(
    id=1,
    tag="input",
    text="Add a 2-year warranty for Rs. 299",
    checked=True,
    rect=Rect(top=0, left=0, width=100, height=20),
    styles=Styles(),
    inputType="checkbox",
    disabled=False,
    required=False,
)

print("=== TEST 1: PRESELECTED CHECKBOX ===")
print("Checked:", element.checked)
print("Warranty keyword exists:", "warranty" in OPTIONAL_WORDS)

result = check_preselected(element)
print("Detection:", result.category if result else "Not detected")

print("\n=== TEST 2: UNCHECKED CHECKBOX ===")

element.checked = False

result = check_preselected(element)
print("Detection:", result.category if result else "Not detected")

print("\n=== TEST 3: REQUIRED CHECKBOX ===")

element.checked = True
element.required = True

result = check_preselected(element)
print("Detection:", result.category if result else "Not detected")