---
inclusion: manual
---

# Wireframe Generation from ASCII Screens

## Purpose
Convert ASCII-style screens into structured wireframe specifications that bridge the gap between text visualization and actual UI implementation.

## Process

1. **Ingest ASCII Screens**: Take the ASCII screens generated in the previous step.
2. **Extract Components**: Identify UI components, layout structure, and hierarchy.
3. **Produce Wireframe Spec**: Output a structured wireframe document with component details.

## Wireframe Specification Format

For each screen, produce a structured specification:

### Screen Metadata
```yaml
screen:
  id: SCR-001
  name: "Registration"
  route: "/register"
  parent: null
  access: public
```

### Layout Structure
```yaml
layout:
  type: single-column | two-column | sidebar | dashboard
  max_width: sm | md | lg | xl | full
  padding: standard
  sections:
    - id: header
      type: page-header
      content: "Create Account"
    - id: form
      type: form
      fields: [...]
    - id: actions
      type: action-bar
      buttons: [...]
```

### Component Definitions
```yaml
components:
  - id: comp-001
    type: text-input | select | checkbox | radio | button | file-upload | textarea | card | table | modal
    label: "Full Name"
    placeholder: "Enter your full name"
    required: true
    validation:
      - rule: min_length
        value: 2
        message: "Name must be at least 2 characters"
    responsive:
      mobile: full-width
      desktop: half-width
```

### Interaction Specifications
```yaml
interactions:
  - trigger: form_submit
    action: api_call
    endpoint: POST /api/auth/register
    loading_state: "Creating account..."
    success: navigate_to("/verify-email")
    error: show_inline_errors
  - trigger: field_blur
    action: validate_field
    realtime: true
```

### Navigation Map
```yaml
navigation:
  from: SCR-001
  transitions:
    - to: SCR-002
      trigger: successful_registration
      type: redirect
    - to: SCR-LOGIN
      trigger: click_login_link
      type: navigate
```

## Component Library Reference

Map ASCII elements to component types:

| ASCII Pattern | Component Type | Properties |
|---|---|---|
| `[____]` | TextInput | single line |
| `[▼ ]` | Select/Dropdown | options list |
| `(●) ( )` | RadioGroup | options |
| `[✓] [ ]` | CheckboxGroup | options |
| `[ Button ]` | Button | variant, action |
| `[📎 Upload]` | FileUpload | accept types |
| `┌─table─┐` | DataTable | columns, rows |
| `⚠ message` | Alert | variant: error |
| `✓ message` | Alert | variant: success |
| `[...]` | Pagination | pages |
| `🔍 [___]` | SearchInput | with icon |

## Responsive Breakpoints

Define behavior at each breakpoint:
- **mobile** (< 640px): Stack all columns, full-width inputs, bottom-sheet modals
- **tablet** (640px - 1024px): Two-column where appropriate, side modals
- **desktop** (> 1024px): Full layout as designed

## State Specifications

For each screen, define:
```yaml
states:
  default: "Empty form, all fields pristine"
  loading: "Submit button disabled, spinner shown"
  error: "Inline field errors displayed, form scrolls to first error"
  success: "Brief success toast, then redirect"
  empty: "No data state with illustration and CTA"
```

## Full Examples

### Example 1: Resume Upload Screen

**Input ASCII:**
```
╔══════════════════════════════════════╗
║         UPLOAD YOUR RESUME           ║
╠══════════════════════════════════════╣
║                                      ║
║   Supported formats: PDF, DOCX       ║
║   Max size: 5MB                      ║
║                                      ║
║   ┌──────────────────────────────┐   ║
║   │                              │   ║
║   │   📎 Drag & drop your file   │   ║
║   │      or click to browse      │   ║
║   │                              │   ║
║   └──────────────────────────────┘   ║
║                                      ║
║   ✓ resume_john_doe.pdf (2.3MB)      ║
║                                      ║
║   [ Continue ──▶ ]                   ║
║                                      ║
╚══════════════════════════════════════╝
```

**Output Wireframe Spec:**
```yaml
screen:
  id: SCR-003
  name: "Resume Upload"
  route: "/onboarding/resume"
  parent: SCR-002
  access: authenticated

layout:
  type: single-column
  max_width: md
  padding: standard
  sections:
    - id: header
      type: page-header
      content: "Upload Your Resume"
    - id: instructions
      type: info-text
      content: "Supported formats: PDF, DOCX. Max size: 5MB"
    - id: upload-area
      type: file-upload-zone
    - id: file-preview
      type: uploaded-file-card
      conditional: file_uploaded
    - id: actions
      type: action-bar

components:
  - id: comp-upload
    type: file-upload
    label: "Resume File"
    accept: [".pdf", ".docx"]
    maxSize: 5242880  # 5MB in bytes
    dragDrop: true
    placeholder: "Drag & drop your file or click to browse"
    required: true
    validation:
      - rule: file_type
        value: ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        message: "Only PDF and DOCX files are accepted"
      - rule: file_size
        value: 5242880
        message: "File must be under 5MB"
    responsive:
      mobile: full-width
      desktop: full-width

  - id: comp-file-preview
    type: card
    conditional: "file !== null"
    content:
      icon: "checkmark-circle"
      filename: "{{file.name}}"
      filesize: "{{file.size | formatBytes}}"
      action: remove_file

  - id: comp-continue-btn
    type: button
    label: "Continue"
    variant: primary
    icon: arrow-right
    disabled_when: "file === null"
    action: submit_and_navigate

interactions:
  - trigger: file_drop
    action: validate_and_preview
    validation: [file_type, file_size]
    success: show_preview_card
    error: show_inline_error

  - trigger: click_continue
    action: api_call
    endpoint: POST /api/resume/upload
    content_type: multipart/form-data
    payload: { file: uploaded_file }
    loading_state: "Uploading resume..."
    success: navigate_to("/onboarding/preferences")
    error: show_toast_error

  - trigger: click_remove
    action: clear_file
    reset: upload_zone_to_default

states:
  default: "Empty drop zone, continue button disabled"
  dragging: "Drop zone highlighted with dashed border"
  uploading: "Progress bar shown, continue disabled"
  uploaded: "File preview card shown, continue enabled"
  error: "Error message below drop zone, file cleared"

navigation:
  from: SCR-003
  transitions:
    - to: SCR-004
      trigger: successful_upload
      type: redirect
    - to: SCR-002
      trigger: click_back
      type: navigate
```

---

### Example 2: Interview Session Screen

**Input ASCII:**
```
╔══════════════════════════════════════════════════╗
║  INTERVIEW SESSION          Question 3 of 10    ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Topic: React Hooks                              ║
║  Difficulty: ●●●○○ Medium                        ║
║                                                  ║
║  ┌────────────────────────────────────────────┐  ║
║  │ Q3: Explain the difference between         │  ║
║  │ useEffect and useLayoutEffect. When would  │  ║
║  │ you choose one over the other?             │  ║
║  └────────────────────────────────────────────┘  ║
║                                                  ║
║  Your Answer:                                    ║
║  ┌────────────────────────────────────────────┐  ║
║  │                                            │  ║
║  │                                            │  ║
║  │                                            │  ║
║  │                                            │  ║
║  └────────────────────────────────────────────┘  ║
║  Characters: 0/2000                              ║
║                                                  ║
║  ⏱ Time remaining: 4:32                          ║
║                                                  ║
║  [ ◀ Previous ]          [ Submit & Next ▶ ]     ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

**Output Wireframe Spec:**
```yaml
screen:
  id: SCR-007
  name: "Interview Question"
  route: "/interview/:sessionId/question/:questionNumber"
  parent: SCR-006
  access: authenticated
  guard: active_session_required

layout:
  type: single-column
  max_width: lg
  padding: standard
  sections:
    - id: header
      type: interview-header
      content: "Interview Session"
      meta: "Question {{currentQuestion}} of {{totalQuestions}}"
    - id: progress-bar
      type: progress
      value: "{{currentQuestion / totalQuestions * 100}}"
    - id: question-meta
      type: metadata-row
    - id: question-card
      type: card
    - id: answer-area
      type: form
    - id: timer
      type: countdown
    - id: navigation
      type: action-bar

components:
  - id: comp-progress
    type: progress-bar
    value: "{{(currentQuestion / totalQuestions) * 100}}"
    label: "Question {{currentQuestion}} of {{totalQuestions}}"
    variant: segmented

  - id: comp-topic-badge
    type: badge
    label: "{{question.topic}}"
    variant: info

  - id: comp-difficulty
    type: difficulty-indicator
    value: "{{question.difficulty}}"
    max: 5
    display: dots  # ●●●○○

  - id: comp-question-card
    type: card
    variant: elevated
    content:
      prefix: "Q{{currentQuestion}}:"
      text: "{{question.text}}"
    accessibility:
      role: region
      aria-label: "Interview question"
      aria-live: polite

  - id: comp-answer-textarea
    type: textarea
    label: "Your Answer"
    placeholder: "Type your answer here..."
    maxLength: 2000
    rows: 6
    showCharCount: true
    required: true
    validation:
      - rule: min_length
        value: 50
        message: "Please provide a more detailed answer (at least 50 characters)"
      - rule: max_length
        value: 2000
        message: "Answer must be under 2000 characters"
    responsive:
      mobile: full-width, rows: 8
      desktop: full-width, rows: 6

  - id: comp-timer
    type: countdown-timer
    duration: "{{question.timeLimitSeconds}}"
    warning_at: 60  # Show warning color at 60 seconds remaining
    expired_action: auto_submit
    display: "mm:ss"
    icon: clock
    accessibility:
      aria-live: assertive
      aria-label: "Time remaining"

  - id: comp-prev-btn
    type: button
    label: "Previous"
    variant: secondary
    icon: arrow-left
    icon_position: left
    disabled_when: "currentQuestion === 1"

  - id: comp-submit-btn
    type: button
    label: "Submit & Next"
    variant: primary
    icon: arrow-right
    icon_position: right
    disabled_when: "answer.length < 50"
    loading_label: "Submitting..."

interactions:
  - trigger: click_submit_next
    action: api_call
    endpoint: POST /api/interview/{{sessionId}}/answer
    payload:
      questionId: "{{question.id}}"
      answer: "{{answerText}}"
      timeSpent: "{{totalTime - remainingTime}}"
    loading_state: "Submitting answer..."
    success:
      condition_if_last: navigate_to("/interview/{{sessionId}}/complete")
      condition_else: navigate_to("/interview/{{sessionId}}/question/{{currentQuestion + 1}}")
    error: show_toast_error("Failed to submit. Your answer is saved locally.")

  - trigger: click_previous
    action: navigate
    target: "/interview/{{sessionId}}/question/{{currentQuestion - 1}}"
    save_draft: true

  - trigger: timer_expired
    action: auto_submit
    same_as: click_submit_next
    show_toast: "Time's up! Your answer has been submitted."

  - trigger: textarea_change
    action: auto_save_draft
    debounce: 2000  # Save draft every 2 seconds of inactivity
    endpoint: PUT /api/interview/{{sessionId}}/draft
    silent: true  # No loading indicator

  - trigger: page_unload
    action: save_draft
    endpoint: PUT /api/interview/{{sessionId}}/draft
    use_beacon: true  # navigator.sendBeacon for reliability

states:
  default: "Question displayed, empty answer textarea, timer running"
  answering: "User typing, character count updating, draft auto-saving"
  submitting: "Submit button loading, textarea disabled"
  time_warning: "Timer turns red/orange at 60 seconds"
  time_expired: "Auto-submit triggered, modal shown briefly"
  draft_saved: "Small 'Draft saved' indicator near textarea"
  error: "Toast notification, answer preserved locally"
  last_question: "Submit button label changes to 'Finish Interview'"

navigation:
  from: SCR-007
  transitions:
    - to: SCR-007 (next question)
      trigger: successful_answer_submit
      type: replace (not push, to avoid back-button issues)
    - to: SCR-007 (prev question)
      trigger: click_previous
      type: replace
    - to: SCR-008 (completion)
      trigger: last_question_submitted
      type: redirect
```

---

### Example 3: Scorecard / Results Screen

**Input ASCII:**
```
╔══════════════════════════════════════════════════╗
║         INTERVIEW SCORECARD                      ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Overall Score: ████████░░ 78/100                ║
║  Grade: B+                                       ║
║                                                  ║
║  ┌────────────────────────────────────────────┐  ║
║  │  Category Breakdown                        │  ║
║  ├────────────────────────────────────────────┤  ║
║  │  Accuracy     ████████░░  8.2/10           │  ║
║  │  Depth        ███████░░░  7.0/10           │  ║
║  │  Clarity      █████████░  9.1/10           │  ║
║  │  Relevance    ███████░░░  7.5/10           │  ║
║  └────────────────────────────────────────────┘  ║
║                                                  ║
║  ┌────────────────────────────────────────────┐  ║
║  │  Question-wise Results                     │  ║
║  ├────┬──────────────────┬────────┬───────────┤  ║
║  │ #  │ Topic            │ Score  │ Status    │  ║
║  ├────┼──────────────────┼────────┼───────────┤  ║
║  │ 1  │ React Basics     │ 9/10   │ ✓ Strong  │  ║
║  │ 2  │ State Mgmt       │ 7/10   │ ~ Fair    │  ║
║  │ 3  │ React Hooks      │ 8/10   │ ✓ Strong  │  ║
║  │ 4  │ Performance      │ 6/10   │ ⚠ Weak    │  ║
║  │ ...│ ...              │ ...    │ ...       │  ║
║  └────┴──────────────────┴────────┴───────────┘  ║
║                                                  ║
║  ┌────────────────────────────────────────────┐  ║
║  │  💡 AI Feedback Summary                    │  ║
║  │                                            │  ║
║  │  Strengths:                                │  ║
║  │  • Strong understanding of React basics    │  ║
║  │  • Clear communication style               │  ║
║  │                                            │  ║
║  │  Areas to Improve:                         │  ║
║  │  • Deepen knowledge of performance tuning  │  ║
║  │  • Practice system design scenarios        │  ║
║  │                                            │  ║
║  │  Recommended Resources:                    │  ║
║  │  • React Performance Patterns (link)       │  ║
║  │  • System Design Primer (link)             │  ║
║  └────────────────────────────────────────────┘  ║
║                                                  ║
║  [ Download PDF ]  [ Share ]  [ Retake Interview ]║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

**Output Wireframe Spec:**
```yaml
screen:
  id: SCR-008
  name: "Interview Scorecard"
  route: "/interview/:sessionId/scorecard"
  parent: SCR-007
  access: authenticated
  guard: completed_session_required

layout:
  type: single-column
  max_width: lg
  padding: standard
  sections:
    - id: header
      type: page-header
      content: "Interview Scorecard"
    - id: overall-score
      type: score-summary
    - id: category-breakdown
      type: card
    - id: question-results
      type: card-with-table
    - id: ai-feedback
      type: card
    - id: actions
      type: action-bar

components:
  - id: comp-overall-score
    type: score-display
    variant: large
    value: "{{scorecard.overallScore}}"
    max: 100
    grade: "{{scorecard.grade}}"
    display: progress-bar-with-number
    color_scale:
      - range: [0, 40]
        color: red
        label: "Needs Improvement"
      - range: [41, 60]
        color: orange
        label: "Fair"
      - range: [61, 80]
        color: blue
        label: "Good"
      - range: [81, 100]
        color: green
        label: "Excellent"

  - id: comp-category-breakdown
    type: card
    title: "Category Breakdown"
    content:
      type: score-bars
      items:
        - label: "Accuracy"
          value: "{{scorecard.categories.accuracy}}"
          max: 10
        - label: "Depth"
          value: "{{scorecard.categories.depth}}"
          max: 10
        - label: "Clarity"
          value: "{{scorecard.categories.clarity}}"
          max: 10
        - label: "Relevance"
          value: "{{scorecard.categories.relevance}}"
          max: 10
    accessibility:
      role: region
      aria-label: "Score breakdown by category"

  - id: comp-question-table
    type: data-table
    title: "Question-wise Results"
    columns:
      - key: number
        label: "#"
        width: 50px
      - key: topic
        label: "Topic"
        width: auto
      - key: score
        label: "Score"
        width: 80px
      - key: status
        label: "Status"
        width: 100px
        render: status-badge
    rows: "{{scorecard.questions}}"
    status_mapping:
      strong: { icon: "checkmark", color: "green", threshold: 8 }
      fair: { icon: "tilde", color: "orange", threshold: 6 }
      weak: { icon: "warning", color: "red", threshold: 0 }
    row_click: expand_question_detail
    responsive:
      mobile: card-list  # Convert table to stacked cards on mobile
      desktop: table

  - id: comp-ai-feedback
    type: card
    title: "AI Feedback Summary"
    icon: lightbulb
    content:
      sections:
        - title: "Strengths"
          type: bullet-list
          items: "{{scorecard.feedback.strengths}}"
          icon: checkmark-circle
          color: green
        - title: "Areas to Improve"
          type: bullet-list
          items: "{{scorecard.feedback.improvements}}"
          icon: arrow-up-circle
          color: orange
        - title: "Recommended Resources"
          type: link-list
          items: "{{scorecard.feedback.resources}}"
          icon: book

  - id: comp-download-btn
    type: button
    label: "Download PDF"
    variant: secondary
    icon: download

  - id: comp-share-btn
    type: button
    label: "Share"
    variant: secondary
    icon: share

  - id: comp-retake-btn
    type: button
    label: "Retake Interview"
    variant: primary
    icon: refresh

interactions:
  - trigger: page_load
    action: api_call
    endpoint: GET /api/interview/{{sessionId}}/scorecard
    loading_state: "Generating your scorecard..."
    success: render_scorecard
    error: show_error_page("Unable to load scorecard")

  - trigger: click_download_pdf
    action: api_call
    endpoint: GET /api/interview/{{sessionId}}/scorecard/pdf
    response_type: blob
    success: download_file("interview_scorecard.pdf")
    loading_state: "Generating PDF..."

  - trigger: click_share
    action: open_modal
    modal: share-modal
    content:
      shareable_link: "{{scorecard.shareableUrl}}"
      options: [copy_link, email, linkedin]

  - trigger: click_retake
    action: confirm_dialog
    message: "Start a new interview with the same settings?"
    confirm_action: api_call
    endpoint: POST /api/interview/create
    payload: { copySettingsFrom: "{{sessionId}}" }
    success: navigate_to("/interview/{{newSessionId}}/question/1")

  - trigger: click_table_row
    action: expand_inline
    content:
      question_text: "{{row.question}}"
      user_answer: "{{row.answer}}"
      ai_evaluation: "{{row.evaluation}}"
      key_points_hit: "{{row.keyPointsHit}}"
      key_points_missed: "{{row.keyPointsMissed}}"

states:
  loading: "Skeleton screen with shimmer placeholders for all sections"
  loaded: "Full scorecard displayed with animations on score bars"
  expanded_row: "Table row expanded showing question detail inline"
  share_modal_open: "Modal overlay with sharing options"
  pdf_generating: "Download button shows spinner"
  error: "Error state with retry button"

navigation:
  from: SCR-008
  transitions:
    - to: SCR-DASHBOARD
      trigger: click_back_to_dashboard
      type: navigate
    - to: SCR-007 (new session)
      trigger: retake_confirmed
      type: redirect
```

---

### Example 4: Interview Preferences / Setup Screen

**Input ASCII:**
```
╔══════════════════════════════════════════════════╗
║         INTERVIEW SETUP                          ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Target Role *                                   ║
║  [▼ Select role...                          ]    ║
║                                                  ║
║  Experience Level *                              ║
║  (●) Junior (0-2 yrs)                           ║
║  ( ) Mid-level (2-5 yrs)                        ║
║  ( ) Senior (5+ yrs)                            ║
║  ( ) Lead/Architect (8+ yrs)                    ║
║                                                  ║
║  Focus Topics (select up to 5) *                 ║
║  [✓] JavaScript    [✓] React     [ ] Angular    ║
║  [ ] Node.js       [✓] TypeScript [ ] Python    ║
║  [ ] System Design [ ] DSA       [ ] DevOps     ║
║  [ ] Databases     [ ] APIs      [ ] Testing    ║
║                                                  ║
║  Topics to Avoid                                 ║
║  [___________________________________________]   ║
║  (comma separated, optional)                     ║
║                                                  ║
║  Interview Duration                              ║
║  [▼ 30 minutes (10 questions)               ]   ║
║                                                  ║
║  Difficulty Preference                           ║
║  ○────────●────────○  Medium                     ║
║  Easy            Hard                            ║
║                                                  ║
║  [ Start Interview ──▶ ]                         ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

**Output Wireframe Spec:**
```yaml
screen:
  id: SCR-005
  name: "Interview Setup"
  route: "/interview/setup"
  parent: SCR-004
  access: authenticated
  guard: resume_uploaded_required

layout:
  type: single-column
  max_width: md
  padding: standard
  sections:
    - id: header
      type: page-header
      content: "Interview Setup"
    - id: form
      type: form
      submit_action: start_interview
    - id: actions
      type: action-bar

components:
  - id: comp-target-role
    type: select
    label: "Target Role"
    placeholder: "Select role..."
    required: true
    options:
      - { value: "frontend", label: "Frontend Developer" }
      - { value: "backend", label: "Backend Developer" }
      - { value: "fullstack", label: "Full Stack Developer" }
      - { value: "devops", label: "DevOps Engineer" }
      - { value: "data", label: "Data Engineer" }
      - { value: "mobile", label: "Mobile Developer" }
    validation:
      - rule: required
        message: "Please select a target role"

  - id: comp-experience-level
    type: radio-group
    label: "Experience Level"
    required: true
    options:
      - { value: "junior", label: "Junior (0-2 yrs)" }
      - { value: "mid", label: "Mid-level (2-5 yrs)" }
      - { value: "senior", label: "Senior (5+ yrs)" }
      - { value: "lead", label: "Lead/Architect (8+ yrs)" }
    default: "junior"
    layout: vertical

  - id: comp-focus-topics
    type: checkbox-group
    label: "Focus Topics"
    required: true
    max_selections: 5
    options:
      - { value: "javascript", label: "JavaScript" }
      - { value: "react", label: "React" }
      - { value: "angular", label: "Angular" }
      - { value: "nodejs", label: "Node.js" }
      - { value: "typescript", label: "TypeScript" }
      - { value: "python", label: "Python" }
      - { value: "system-design", label: "System Design" }
      - { value: "dsa", label: "DSA" }
      - { value: "devops", label: "DevOps" }
      - { value: "databases", label: "Databases" }
      - { value: "apis", label: "APIs" }
      - { value: "testing", label: "Testing" }
    layout: grid-3-columns
    validation:
      - rule: min_selections
        value: 1
        message: "Select at least one topic"
      - rule: max_selections
        value: 5
        message: "Maximum 5 topics allowed"
    responsive:
      mobile: grid-2-columns
      desktop: grid-3-columns

  - id: comp-avoid-topics
    type: text-input
    label: "Topics to Avoid"
    placeholder: "e.g., recursion, binary trees"
    required: false
    helper_text: "Comma separated, optional"

  - id: comp-duration
    type: select
    label: "Interview Duration"
    options:
      - { value: "15", label: "15 minutes (5 questions)" }
      - { value: "30", label: "30 minutes (10 questions)" }
      - { value: "45", label: "45 minutes (15 questions)" }
    default: "30"

  - id: comp-difficulty
    type: range-slider
    label: "Difficulty Preference"
    min: 1
    max: 3
    step: 1
    default: 2
    labels:
      1: "Easy"
      2: "Medium"
      3: "Hard"
    display_value: true

  - id: comp-start-btn
    type: button
    label: "Start Interview"
    variant: primary
    icon: arrow-right
    icon_position: right
    size: large
    full_width_mobile: true

interactions:
  - trigger: form_submit
    action: api_call
    endpoint: POST /api/interview/create
    payload:
      targetRole: "{{formValues.targetRole}}"
      experienceLevel: "{{formValues.experienceLevel}}"
      focusTopics: "{{formValues.focusTopics}}"
      avoidTopics: "{{formValues.avoidTopics.split(',').map(trim)}}"
      duration: "{{formValues.duration}}"
      difficulty: "{{formValues.difficulty}}"
    loading_state: "Setting up your interview... AI is generating questions"
    loading_duration_hint: "5-10 seconds"
    success: navigate_to("/interview/{{sessionId}}/question/1")
    error: show_toast_error

  - trigger: topic_selection_change
    action: validate_max_selections
    max: 5
    exceeded_action: disable_unchecked_options
    message: "Maximum 5 topics selected"

states:
  default: "Form with defaults pre-selected (Junior, Medium difficulty, 30 min)"
  selecting_topics: "Counter shows 'X of 5 selected', disables rest at max"
  submitting: "Full-page loading overlay with AI generation animation"
  error: "Inline errors on invalid fields, toast for server errors"

navigation:
  from: SCR-005
  transitions:
    - to: SCR-007 (first question)
      trigger: interview_created_successfully
      type: redirect
    - to: SCR-003
      trigger: click_back
      type: navigate
```

---

## Output Checklist

For each wireframe, ensure:
- [ ] All interactive elements have defined behavior
- [ ] Validation rules are specified for all inputs
- [ ] Loading/error/success states are defined
- [ ] Navigation targets are identified
- [ ] Responsive behavior is noted
- [ ] Accessibility requirements are listed (labels, ARIA, focus order)
- [ ] API endpoints are mapped to interactions
- [ ] Conditional rendering logic is specified
- [ ] Auto-save / draft behavior defined where applicable
- [ ] Timer or time-sensitive behavior documented
- [ ] Mobile-specific layout adaptations noted
