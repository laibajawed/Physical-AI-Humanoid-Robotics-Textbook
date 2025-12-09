---
id: 1
title: Create Futuristic Homepage Spec
stage: spec
date: 2025-12-08
surface: agent
model: claude-sonnet-4-5-20250929
feature: futuristic-homepage
branch: 001-futuristic-homepage
user: user
command: /sp.specify
labels: [specification,ui,homepage,robotics]
links:
  spec: specs/001-futuristic-homepage/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-futuristic-homepage/spec.md
 - specs/001-futuristic-homepage/checklists/requirements.md
tests:
 - specs/001-futuristic-homepage/checklists/requirements.md
---

## Prompt

```text
Physical AI & Humanoid Robotics Textbook (current live Docusaurus v3 site)
Goal: Upgrade ONLY the homepage UI to the exact premium dark futuristic style shown in the Sentient Machines screenshots, while keeping every existing page, sidebar, module, and content 100% unchanged.

Files to modify/create:
1. src/pages/index.js     ← completely replace with new homepage (or index.mdx if you use MDX)
2. src/css/custom.css    ← add any required extra styles / particle background
3. src/theme/Navbar/Logo.js or static/img/logo.svg ← (optional) update logo

Exact design requirements (must match Sentient Machines aesthetic 1:1):

• Background: #0F0F1A with very subtle animated floating particles (low-performance canvas or CSS solution)
• Hero section (desktop: text left 55%, image right 45% | mobile: stacked)
  Title (exact text and styling):
  Think      ← purple → pink gradient (#A78BFA → #F472B6), huge and bold
  → Move     ← same gradient on "Move", arrow large and white
  → Learn    ← same gradient on "Learn"

  Subtitle (white, clean):
  The Complete Handbook for Humanoid Intelligence
  Master ROS 2, NVIDIA Isaac Sim, Vision-Language-Action models, and embodied foundation models — all open-source and production-ready.

  CTA button: pill-shaped gradient (same purple→pink), white bold text "Start Building →", soft glow + hover scale

• Hero image (right side in center ):
  Use this exact high-quality humanoid robot photo:
  robottt.jpeg inside this folder

• Navbar logo update:
  Replace current green cartoon robot with sleek minimalist humanoid robot head.
Use the images.png picture in this folder

 • Module cards section (2×2 grid, exactly like Sentient Machines):
  Dark cards (#1A1A2E), subtle purple border on hover, 16px radius, hover lift
  Content:
  1. The Nervous System (ROS 2) → Foundations of modern robot operating systems
  2. Digital Twins (Simulation) → Photorealistic simulation with Gazebo, Unity & Isaac Sim
  3. The AI Brain (NVIDIA Isaac) → End-to-end GPU-accelerated robotics development
  4. Vision-Language-Action (VLA) → Embodied foundation models that see, reason, and act
  Each card ends with white pill button "Explore Module"

Technical rules:
• Use existing Tailwind setup + custom CSS only where needed
• 100% responsive
• Keep current sidebar, all docs, footer, GitHub link untouched
• Dark mode only
• Output only the modified/added files with full code
```

## Response snapshot

Created comprehensive feature specification for the futuristic homepage UI upgrade, including user scenarios, functional requirements, and success criteria. The specification details the visual requirements for the dark futuristic design, particle background, hero section layout, module cards, and navbar logo update while maintaining all existing documentation pages and navigation unchanged.

## Outcome

- ✅ Impact: Specification created for futuristic homepage redesign with detailed requirements
- 🧪 Tests: Created quality checklist to validate spec completeness
- 📁 Files: Created spec.md and requirements checklist in feature directory
- 🔁 Next prompts: Ready for planning phase with `/sp.plan`
- 🧠 Reflection: Successfully captured all visual and functional requirements without implementation details

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All specification requirements met
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to planning phase