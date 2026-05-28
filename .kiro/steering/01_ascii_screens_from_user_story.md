---
inclusion: manual
---

# ASCII Screen Generation from User Stories

## Purpose
Generate ASCII-style user interface screens from a given user story to quickly visualize the interface layout and flow before any design or code work begins.

## Process

1. **Parse the User Story**: Extract actors, actions, inputs, outputs, and navigation flows.
2. **Identify Screens**: Break the story into discrete screens/views the user will interact with.
3. **Generate ASCII Layouts**: For each screen, produce a text-based wireframe using box-drawing characters.

## ASCII Screen Conventions

### Layout Characters
```
┌──────────────────────────┐   Box borders
│                          │   Content area
├──────────────────────────┤   Section dividers
└──────────────────────────┘   Box bottom

[ Button Label ]               Buttons
[_______________]              Text inputs
[▼ Dropdown    ]              Select/dropdown
(●) Selected  ( ) Option      Radio buttons
[✓] Checked   [ ] Unchecked   Checkboxes
═══════════════════════════    Page header separator
```

### Screen Template
```
╔══════════════════════════════════════╗
║         SCREEN TITLE                 ║
╠══════════════════════════════════════╣
║                                      ║
║   [Content Area]                     ║
║                                      ║
╠══════════════════════════════════════╣
║   [Navigation / Actions]             ║
╚══════════════════════════════════════╝
```

### Rules
- Each screen must have a clear title
- Show all interactive elements (inputs, buttons, links)
- Indicate navigation flow between screens with arrows: `──▶`
- Mark required fields with `*`
- Show error/success message placement with `⚠` or `✓`
- Include responsive hints: `[mobile: stack vertical]`
- Number screens sequentially for flow reference

## Output Format

For each user story, produce:
1. **Screen inventory**: List of all screens identified
2. **Flow diagram**: ASCII arrow diagram showing navigation between screens
3. **Individual screens**: Each screen rendered in ASCII with annotations
4. **Interaction notes**: Brief notes on dynamic behavior (loading states, validation, transitions)

## Example

Given: "As a user, I want to register so I can access the platform"

**Flow**: Register Screen ──▶ Email Verification ──▶ Profile Setup ──▶ Dashboard

**Screen 1: Registration**
```
╔══════════════════════════════════════╗
║         CREATE ACCOUNT               ║
╠══════════════════════════════════════╣
║                                      ║
║   Full Name *                        ║
║   [___________________________]      ║
║                                      ║
║   Email *                            ║
║   [___________________________]      ║
║                                      ║
║   Password *                         ║
║   [___________________________]      ║
║                                      ║
║   Confirm Password *                 ║
║   [___________________________]      ║
║                                      ║
║   [ Create Account ]                 ║
║                                      ║
║   Already have an account? Login     ║
║                                      ║
╚══════════════════════════════════════╝
```
