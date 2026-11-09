// Cover letter page. Typography follows the resume skill's template so a
// letter and a resume opened together read as one set: Lato for text,
// Oswald for the name, the same ink and navy, from the fonts the resume
// skill ships. The body is larger than the resume's 9pt because this page
// is one full-width column and the resume is two narrow ones; 9pt across a
// 6.5 inch measure is a wall.
#let data = json(sys.inputs.content)

#set page(paper: "us-letter", margin: (x: 72pt, y: 64pt))
#set text(font: "Lato", weight: 400, size: 10pt, fill: rgb("#0D111A"))
#set par(justify: false, leading: 6pt, spacing: 11pt)
// Typst breaks a line after a hyphen, which splits a hyphenated name across
// two lines when it falls at a line end. A hyphenated word is one word on
// this page.
#show regex("\w+(-\w+)+"): box

#text(font: "Oswald", weight: 500, size: 20pt, fill: black)[#data.name]
#v(2pt)
#text(size: 8.5pt, fill: rgb("#082A4D"))[
  #data.contact.join("  ·  ")
]
#v(3pt)
#line(length: 100%, stroke: 0.5pt + rgb("#959BA6"))
#v(14pt)

#for block in data.body [
  #block
  #v(9pt)
]

#v(4pt)
#text(weight: 700)[#data.name]
