Adjust the Underlytics UI on the New Application page and related layout with the following fixes.

## 1. Form alignment and spacing
Improve the layout of the form fields so labels, inputs, helper text, and grid columns are properly aligned and consistently spaced.

Requirements:
- labels should align cleanly across columns
- input heights should feel consistent
- helper text should not feel cramped
- vertical spacing between label, field, and helper text should be more deliberate
- the overall form should feel polished and balanced

## 2. Phone number field
Improve the phone number input.

Requirements:
- make the phone number input wider so it can comfortably fit longer numbers
- accept numbers only for the phone number portion
- keep the country code selector separate from the local number input
- ensure the field still looks clean and aligned with the rest of the form

## 3. Selection controls
For anything that requires a selection, use the shadcn select pattern based on:
https://ui.shadcn.com/docs/components/radix/select

This applies especially to:
- employment status
- country code selector
- any dropdown-style input in the app

Do not use plain browser selects if a shadcn/radix select is more appropriate.

## 4. Sticky profile card issue
The card containing the profile icon on the side is currently sticking while scrolling.

Fix this so:
- it should NOT remain sticky
- it should scroll away naturally with the page
- it should disappear from view as the user scrolls down
- remove any sticky positioning causing it to stay pinned

## 5. Save as Draft button layering issue
The “Save as Draft” button appears above other elements while scrolling, likely due to z-index or positioning.

Fix this so:
- it should not float above unrelated content
- it should stay in normal document flow unless intentionally placed
- remove incorrect z-index or sticky/fixed positioning
- make sure it remains visually aligned with the rest of the action buttons

## 6. General polish
While making these fixes:
- preserve existing functionality
- keep the premium fintech styling direction
- do not break Clerk auth or form submission
- keep the layout responsive

Deliver:
- updated components/pages
- brief explanation of what was changed