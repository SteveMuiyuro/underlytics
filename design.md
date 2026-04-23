Redesign and modernize the full Underlytics UI so it feels like a premium, production-ready fintech and AI underwriting platform.

Important:
- Keep all existing functionality working
- Improve the UI significantly without breaking routes, auth, workflow logic, uploads, or backend integration
- Use shadcn/ui components wherever appropriate
- The design should feel modern, trustworthy, clean, premium, and responsive
- Avoid anything that looks outdated, boxy, or like a generic admin template

## Product context

Underlytics is an AI-powered loan underwriting platform with:
- public landing page
- applicant authentication
- dashboard
- applications list
- application detail page
- document uploads
- planner + worker workflow visibility
- structured agent outputs
- manual review support later
- email notifications later

The product should feel like:
- fintech
- explainable AI
- enterprise-ready but still clean for B2C users

---

## Color system

Use this as the visual direction:

- Base: `oklch(14% 0.01 230)`
- Primary: `oklch(60% 0.15 250)`  // indigo
- Accent: `oklch(70.4% 0.14 182.503)`  // cool cyan-teal
- Warning / Manual Review: `oklch(60% 0.20 25)`
- Add a true red for rejected / destructive states
- Add a proper green for approved / success states

Interpretation:
- Primary indigo = trust, professionalism, product identity
- Accent cyan-teal = intelligence, AI activity, insights, advanced system feel
- Orange warning = caution, manual review, pending attention
- Red = rejection, failed states, destructive actions
- Green = approval, success, completed-safe states

Do not use the warning orange as the rejected color.
Do not overuse the accent.
Keep the UI mostly light with white surfaces and soft borders.

---

## Visual style

The product should use:
- light theme
- white cards
- subtle gray borders
- soft indigo/cyan highlights
- excellent spacing
- clean typography
- better visual hierarchy
- polished hover states
- modern rounded corners
- responsive layout

The aesthetic should feel closer to:
- premium SaaS
- fintech dashboard
- explainable AI platform

Avoid:
- heavy dark backgrounds inside app content
- clunky spacing
- overly dense pages
- dated admin panel look
- inconsistent paddings and misaligned cards

---

## Required UI work

## 1. Public landing page

Create a polished public landing page for Underlytics.

Requirements:
- logo or brand on the top left
- Register and Sign In on the top right
- signed-in users should see “Go to Dashboard”
- strong hero section
- clean supporting body sections
- strong footer with legal links
- fully responsive

Sections to include:
- hero
- feature highlights
- how it works
- explainable AI / trust section
- optional stats / product preview
- footer with:
  - Privacy Policy
  - Terms of Service
  - Cookie Policy

Tone:
- premium
- credible
- fintech / AI
- creative but not flashy

Use shadcn/ui where appropriate.

---

## 2. App shell redesign

Modernize the internal application shell.

Improve:
- sidebar
- topbar
- page header layout
- content spacing
- section hierarchy
- mobile responsiveness

Use modern patterns:
- better navigation grouping
- cleaner active states
- strong page titles
- subtle breadcrumb support where useful
- action buttons aligned properly

The shell should feel like a modern SaaS app, not an early scaffold.

---

## 3. Forms

Refactor forms to use proper shadcn/ui form patterns.

Use relevant components such as:
- Form
- FormField
- FormItem
- FormLabel
- FormControl
- FormMessage
- Input
- Select
- Textarea
- Checkbox if needed
- Button

Focus especially on:
- New Application page
- any future manual review forms
- document upload area styling

Goals:
- more polished structure
- better labels
- cleaner error states
- improved spacing and alignment
- modern form composition

---

## 4. Tables and list pages

Upgrade the Applications list page and any tabular data areas.

Use shadcn table components and improve:
- row spacing
- badge styling
- action alignment
- empty states
- hover states
- visual balance

Make the table feel premium and readable.

If helpful, introduce:
- filters row
- better page-level actions
- cleaner table container cards

---

## 5. Dashboard redesign

The dashboard already works with real data. Improve the presentation.

Goals:
- real premium fintech dashboard feel
- better card layout
- stronger metric hierarchy
- more polished recent applications section
- cleaner alerts / activity panels

Use:
- Cards
- Badges
- Buttons
- Tabs if useful
- subtle visual emphasis for important metrics

Dashboard cards should feel intentionally designed, not just functional.

---

## 6. Application detail page redesign

This page is the most important screen in the product and should feel significantly upgraded.

Improve these sections:
- Decision Summary
- Planner Workflow
- Worker cards
- Agent outputs
- Application Details
- Documents upload
- Uploaded Documents
- Communication Log
- Workflow Timeline

Specific improvements:
- make the planner card more visually important
- make worker cards clearer and easier to scan
- separate status, score, confidence, decision, reasoning, and flags cleanly
- use better badges and grouping
- improve content hierarchy within cards
- make uploaded documents look more like a proper document center
- reduce the “stacked utility card” feeling

The page should feel like a premium underwriting workspace.

---

## 7. Workflow UI improvements

The workflow section currently works, but should look much better.

Redesign it so:
- planner status is easy to understand
- workers feel like independent agents
- scores/confidence look intentional
- decisions are readable
- flags are visually meaningful
- reasoning blocks are easy to scan

Use components like:
- Card
- Badge
- Separator
- Accordion or collapsible sections if useful
- Tabs if useful
- icons if they add clarity

Avoid clutter.
Do not hide critical information.

---

## 8. Document upload UX

The upload flow works. Improve the experience.

Goals:
- make upload cards cleaner
- improve spacing and hierarchy
- show selected file and upload result more elegantly
- make uploaded document list feel more polished and trustworthy

The documents area should feel like a real part of the underwriting product, not a placeholder.

---

## 9. Status styling

Standardize status colors and labels everywhere.

Use human-friendly labels instead of raw snake_case where possible.

Examples:
- `manual_review` → `Manual Review`
- `workers_completed` → `Workers Completed`
- `policy_mismatch` → `Policy Mismatch`

Status colors:
- Approved = green
- Rejected = red
- Manual Review = orange
- Running / In Progress = primary/accent
- Pending = neutral
- Completed = green
- Failed = red

Make this consistent across:
- dashboard
- applications list
- detail page
- workflow cards
- document statuses

---

## 10. Use shadcn/ui deeply

Use the most relevant shadcn/ui components instead of hand-rolled UI wherever appropriate.

Expected components to consider:
- Card
- Table
- Badge
- Button
- Form
- Input
- Select
- Textarea
- Dropdown Menu
- Tabs
- Separator
- Dialog
- Sheet
- Breadcrumb
- Skeleton
- Accordion
- Alert
- Tooltip if useful

Do not add components just for the sake of it.
Use them where they genuinely improve quality and consistency.

---

## 11. Design quality bar

The final UI should feel:
- modern
- clean
- premium
- responsive
- trustworthy
- fintech-grade
- AI-enabled without looking gimmicky

It should not feel:
- old
- bulky
- overly plain
- unfinished
- generic

---

## 12. Keep functionality intact

Do not break:
- Clerk auth
- routes
- dashboard data
- application creation
- document uploads
- workflow rendering
- agent output display
- current backend integrations

This is a UI modernization, not a rewrite of business logic.

---

## 13. Deliverables

Provide:
- updated landing page
- updated layout shell
- updated dashboard
- updated application list page
- updated application detail page
- updated form UI
- any new reusable components
- brief explanation of file changes

Prefer componentized changes over one giant page file.
Keep code clean and maintainable and use your judgment based on the logic you have built so far.