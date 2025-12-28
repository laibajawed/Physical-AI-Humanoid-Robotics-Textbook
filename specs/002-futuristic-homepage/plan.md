# Implementation Plan: Futuristic Homepage UI Upgrade

**Branch**: `002-futuristic-homepage` | **Date**: 2025-12-08 | **Spec**: specs/002-futuristic-homepage/spec.md
**Input**: Feature specification from `/specs/002-futuristic-homepage/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Upgrade the Docusaurus homepage UI to a premium dark futuristic style with gradient text ("Think → Move → Learn"), a 2×2 grid of module cards, and an updated navbar logo. The implementation will replace the current src/pages/index.tsx file with a new React component using Tailwind CSS v4 and custom CSS for the specified design elements. The existing sidebar, documentation pages, and footer will remain completely unchanged. The design will follow the exact specifications: background #0F0F1A, purple→pink gradient (#A78BFA → #F472B6), responsive layout (55%/45% desktop split, stacked mobile), while maintaining existing light/dark mode toggle functionality.

## Technical Context

**Language/Version**: TypeScript 5.0+, React 18+, Docusaurus 3.x
**Primary Dependencies**: Tailwind CSS v4, @docusaurus/core, React, Node.js
**Storage**: N/A (static site generation)
**Testing**: Jest for unit tests, Cypress for e2e tests (NEEDS CLARIFICATION)
**Target Platform**: Web (modern browsers: Chrome, Firefox, Safari, Edge latest 2 versions)
**Project Type**: Web documentation site with Docusaurus framework
**Performance Goals**: <3s page load time, Core Web Vitals "Good" scores, 100% responsive
**Constraints**: Must maintain existing sidebar, docs, footer, GitHub link; WCAG 2.1 AA compliance; maintain existing light/dark mode toggle

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **CODE QUALITY**: PASS - Using Docusaurus 3.x for documentation structure, Markdown-first architecture, TypeScript strict mode, Component-based design with React best practices, minimal external dependencies
2. **USER EXPERIENCE**: PASS - Creating beautiful, modern design inspired by premium tech documentation, mobile-first responsive design, fast page loads with optimized images, clear visual hierarchy, dark mode implementation
3. **CONTENT ORGANIZATION**: PASS - Maintaining existing physical AI fundamentals, robotics engineering topics, and humanoid robotics as advanced applications with modular structure
4. **DESIGN STANDARDS**: PASS - Using consistent color palette (purple→pink gradient #A78BFA → #F472B6), 2 font families maximum, Tailwind CSS v4 for styling as required

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
physical-ai-robotics-book/
├── src/
│   ├── components/
│   ├── css/
│   │   └── custom.css
│   ├── pages/
│   │   ├── index.tsx          # New futuristic homepage
│   │   └── index.module.css   # Homepage-specific styles
│   └── theme/
│       └── Navbar/
│           └── Logo.js         # Updated navbar logo component
├── static/
│   ├── img/
│   │   ├── logo.svg           # Current logo (to be replaced)
│   │   ├── robotttt.jpeg      # Hero image for homepage
│   │   └── images.png         # New navbar logo
│   └── .nojekyll
├── docusaurus.config.ts       # Site configuration
└── package.json
```

**Structure Decision**: Web documentation site using Docusaurus framework with React components. The new homepage will replace src/pages/index.tsx completely while maintaining all other site functionality. Custom CSS will be added to src/css/custom.css for specific styling needs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
