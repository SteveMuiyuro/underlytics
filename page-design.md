Review and improve the layout/alignment on this page:

https://underlytics.vercel.app/applications/APP-001

Focus especially on the “Planner Workflow” section and the worker result cards below it.

Main issues visible from the screenshots:

1. Planner Job card layout is not well aligned
The “Retries”, “Started”, and “Updated” stat boxes are squeezed and not visually balanced.
The “Completed” status pill and “5 completed workers” pill currently appear on the left side and take space away from the main metadata layout.

Required change:
Move the “Completed” status pill and “5 completed workers” pill so they appear after the Retries / Started / Updated stat boxes, or redesign the card so all elements have enough room and align cleanly.
The Planner Job card should look balanced on desktop and mobile.

2. Worker cards are too squeezed
Some cards have narrow stat boxes where text like “CONFID…” and decisions like “documents missing” are cramped or wrapping badly.
The card grid needs better spacing, consistent widths, and cleaner alignment.

Required change:
Improve the worker card layout so Score, Confidence, and Decision have enough space.
Avoid awkward text clipping or cramped vertical boxes.
Decision values should be readable without breaking the layout.

3. Completed status buttons/pills are misaligned
The green “Completed” pills on the worker cards are not consistently aligned with the card headers.
Some overlap or sit too far to the right.

Required change:
Ensure all status pills align consistently inside the card header area.
They should not overflow, overlap, or create uneven spacing.

4. Preserve existing design direction
Do not redesign the whole page.
Keep the current visual style, colors, rounded cards, badges, and overall structure.
Only improve spacing, alignment, responsiveness, and readability.

5. Responsive behavior
Check desktop and mobile layouts.
On smaller widths, stack elements gracefully instead of squeezing them.
Use flex-wrap, responsive grids, min-widths, or stacked layouts where necessary.

Please inspect the relevant components for the application detail page, Planner Workflow card, and worker result cards. Refactor the layout/CSS/Tailwind classes to make the page visually polished, readable, and production-ready.