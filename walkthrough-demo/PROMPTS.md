# AI Image Prompts — The One Club Walkthrough

Generate each image at **1920×1080** (landscape). Use Midjourney, DALL·E 3, or Firefly.
Save to `walkthrough-demo/images/` with the exact filename shown.

---

## 01-exterior.jpg — Dusk approach

```
Ultra-luxury modern Australian beachside home exterior, Burleigh Heads Gold Coast, 
photographed at golden hour dusk. Warm amber light glowing from inside large timber-framed 
windows. White render and natural timber facade, lush tropical landscaping, 
stone pathway leading to the front door. Deep green tropical palms silhouetted 
against a soft coral and lavender sky. Architectural photography, Canon 5D, 
sharp foreground, dreamy background bokeh. Style: luxury real estate editorial.
--ar 16:9 --v 6 --style raw
```

---

## 02-door.jpg — Front door close-up

```
Close-up of a bespoke luxury pivot front door, natural blackbutt timber with 
integrated brass/gold handle and sidelights. Soft afternoon light casting 
a warm rectangle onto polished concrete entry floor. Flanked by tall tropical 
greenery in matte black planters. Shot from a low, slightly looking-up angle, 
suggesting arrival. Architectural photography, extremely detailed, editorial magazine style.
--ar 16:9 --v 6 --style raw
```

---

## 03-hallway.jpg — Entry hallway

```
Interior of a luxury modern Australian coastal home, wide entry hallway. 
European oak herringbone timber floors, crisp white walls with a single 
large-scale framed artwork in a brushed gold frame. Ceiling height 3.2m. 
Natural light flooding in from the far end, hinting at a green-walled 
dining room beyond. Architectural interior photography, natural light, 
no flash. Style: Vogue Living, Australian House & Garden editorial.
--ar 16:9 --v 6 --style raw
```

---

## 04-dining.jpg — The dining room

```
Luxury Australian coastal dining room, deep forest green (Dulux Cactus) 
walls and ceiling, European oak floor, large custom dining table in dark 
walnut with 6 linen upholstered chairs. Oversized rattan-wrapped brass 
pendant light above the table. Floor-to-ceiling glass sliding doors open 
to a deck with a glimpse of turquoise ocean in the distance. 
Late afternoon golden light. Architectural interior photography. 
Style: The Design Files, Vogue Living Australia. Moody, warm, magazine quality.
--ar 16:9 --v 6 --style raw
```

---

## 05-ocean.jpg — Beachside view through the window

```
POV from inside a luxury Gold Coast home dining room looking through 
floor-to-ceiling frameless glass to a private deck, infinity pool edge, 
sand dunes and turquoise Pacific Ocean beyond. Late afternoon, warm golden 
light on the water. Interior is softly reflected in the glass. 
Calm, luxurious, editorial. Shot on medium format camera, architectural photography.
--ar 16:9 --v 6 --style raw
```

---

## 06-magazine.jpg — Magazine on the dining table

```
Top-down flat lay photograph of a luxury lifestyle magazine resting on a 
dark walnut dining table. Magazine cover is deep forest green with gold 
typography reading "THE ONE CLUB" and "A HOME WORTH OWNING." 
A single perfect dried palm leaf and a small brass object beside it. 
Warm natural light from the side. Shot directly overhead, styled editorial 
flat lay. Ultra sharp, magazine quality photography.
--ar 16:9 --v 6 --style raw
```

---

## Tips for best results

- Run each prompt 4× and pick the sharpest, most cinematic result
- Keep consistent lighting direction (warm light from left or right — be consistent across all 6)
- The green in scene 04 should feel rich and dark, not bright — reference "Dulux Cactus" or "Farrow & Ball Calke Green"
- Export at maximum resolution, save as high-quality JPG (quality 90+)
- Once images are in `walkthrough-demo/images/`, add `background-image: url('images/XX-name.jpg')` 
  to the matching `.scene-X` CSS rule in `walkthrough-demo/index.html`
