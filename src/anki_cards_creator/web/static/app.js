const FORMATTING_TAGS = ["b", "i", "small"];

// Rebuild the card's source text, in which only the formatting tags are markup.
function toSource(node) {
  return [...node.childNodes]
    .map((child) => {
      if (child.nodeType === Node.TEXT_NODE) return child.nodeValue;
      if (child.nodeType !== Node.ELEMENT_NODE) return "";
      const tag = child.tagName.toLowerCase();
      if (tag === "br") return "<br>";
      const inner = toSource(child);
      return FORMATTING_TAGS.includes(tag) ? `<${tag}>${inner}</${tag}>` : inner;
    })
    .join("");
}

document.addEventListener("input", (event) => {
  const field = event.target.closest("[data-field]");
  if (!field) return;
  field.closest("form").elements[field.dataset.field].value = toSource(field);
});

// Select the word on the first click, so the next word can be typed straight
// over it. Later clicks place the caret as usual, so the word can still be fixed.
const word = document.getElementById("word");
let selectOnClick = true;

word.addEventListener("click", () => {
  const dragged = word.selectionStart !== word.selectionEnd;
  if (selectOnClick && !dragged) word.select();
  selectOnClick = false;
});
word.addEventListener("input", () => { selectOnClick = false; });
word.addEventListener("blur", () => { selectOnClick = true; });
word.form.addEventListener("submit", () => { selectOnClick = true; });
