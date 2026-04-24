Review and improve the layout/alignment on this page:

https://underlytics.vercel.app/applications/APP-001


The planner job agent is now okay but check the layout of the other agents specifically the status tag.
Review the application detail page UI, specifically the worker cards and Planner Workflow section.

Current issue:
The “Completed” status badges are positioned on the right side of the card headers, which is causing layout compression and squeezing of other elements like Score, Confidence, and Decision.

Required change:
Move all status badges (e.g. “Completed”) into their own dedicated row instead of placing them inline with the card header.

Implementation details:

1. Card Header Layout
- First row: agent icon + agent name (left aligned)
- Second row: status badges (e.g. “Completed”) and any related badges (e.g. “5 completed workers”)
- Ensure badges are left-aligned and wrap if necessary
- Do NOT place badges on the far right anymore

2. Spacing and Alignment
- Add vertical spacing between:
  - header row
  - status row
  - stats (Score, Confidence, Decision)
- Ensure consistent padding across all cards
- Prevent any element from being squeezed horizontally

3. Worker Cards
- Apply this structure consistently to:
  - Document Analysis
  - Policy Retrieval
  - Risk Assessment
  - Fraud Verification
  - Decision Summary
- Ensure uniform layout across all worker cards

4. Planner Job Card
- Apply the same pattern:
  - Title row
  - Status row (Completed + completed workers)
  - Stats row (Retries, Started, Updated)
- Ensure stats have enough horizontal space and are not compressed

5. Responsive Behavior
- On smaller screens:
  - Status badges should wrap naturally
  - Avoid shrinking text or compressing stat boxes
  - Stack sections vertically if needed

6. Constraints
- Do NOT redesign the visual style
- Keep existing colors, badges, and components
- Only improve layout, spacing, and alignment

Goal:
A clean, readable layout where:
- badges do not compete for horizontal space
- stats are clearly visible
- cards feel balanced and not cramped
- UI looks production-ready and consistent