# Implementation Tasks: Futuristic Homepage UI Upgrade

**Feature**: Futuristic Homepage UI Upgrade
**Branch**: `002-futuristic-homepage`
**Created**: 2025-12-08
**Input**: Feature specification from `/specs/002-futuristic-homepage/spec.md`

## Implementation Strategy

**MVP Scope**: Complete User Story 1 (Homepage Visual Upgrade) with basic functionality, then enhance with User Stories 2 and 3.

**Delivery Approach**: Incremental delivery with each user story building on the previous, ensuring working functionality at each phase.

## Dependencies

- User Story 1 (P1) must be completed before User Story 2 (P2) and User Story 3 (P3)
- User Story 2 and User Story 3 can be developed in parallel after User Story 1 completion
- All stories depend on foundational setup tasks

## Parallel Execution Opportunities

- [US2] and [US3] tasks can be developed in parallel after [US1] completion
- CSS styling tasks can be developed in parallel with React component tasks when they affect different components

---

## Phase 1: Setup

- [ ] T001 Create backup of current src/pages/index.tsx file
- [ ] T002 Verify Tailwind CSS v4 is properly configured in the project
- [ ] T003 Confirm required images (robotttt.jpeg, images.png) exist in static directory
- [ ] T004 Set up development environment for Docusaurus site

## Phase 2: Foundational Tasks

- [ ] T005 [P] Update src/css/custom.css with dark background color (#0F0F1A) and gradient definitions
- [ ] T006 [P] Create responsive layout utilities for 55%/45% desktop split and mobile stacking
- [ ] T007 [P] Add accessibility utilities for screen reader support
- [ ] T008 [P] Maintain existing light/dark mode toggle with new futuristic styling

## Phase 3: User Story 1 - Homepage Visual Upgrade (Priority: P1)

**Goal**: Implement the core homepage with dark futuristic design, gradient text, and module cards.

**Independent Test**: The homepage can be viewed independently and should showcase the new dark futuristic design with gradient text ("Think → Move → Learn"), and the specified module cards, delivering an immediate premium feel to visitors.

- [ ] T009 [US1] Create new homepage component in src/pages/index.tsx with dark background (#0F0F1A)
- [ ] T010 [US1] Implement hero section with left 55% text and right 45% image layout for desktop
- [ ] T011 [US1] Implement responsive stacking for mobile devices
- [ ] T012 [US1] Create "Think → Move → Learn" gradient text using #A78BFA → #F472B6
- [ ] T013 [US1] Add subtitle text: "The Complete Handbook for Humanoid Intelligence"
- [ ] T014 [US1] Add subtitle description: "Master ROS 2, NVIDIA Isaac Sim, Vision-Language-Action models, and embodied foundation models — all open-source and production-ready."
- [ ] T015 [US1] Implement pill-shaped CTA button with purple→pink gradient and text "Start Building →"
- [ ] T016 [US1] Add hover effects (soft glow + scale) to CTA button
- [ ] T017 [US1] Add hero image (robotttt.jpeg) to right side of hero section
- [ ] T018 [US1] Create 2×2 grid layout for module cards
- [ ] T019 [US1] Style module cards with dark background (#1A1A2E) and 16px border radius
- [ ] T020 [US1] Add hover effects to cards (subtle purple border and lift effect)
- [ ] T021 [US1] Add "Explore Module" white pill buttons to each card
- [ ] T022 [US1] Add ARIA labels and semantic HTML structure for screen reader support
- [ ] T023 [US1] Test homepage on desktop to verify 55%/45% layout
- [ ] T024 [US1] Test homepage on mobile to verify stacked layout
- [ ] T025 [US1] Verify all text elements maintain WCAG 2.1 AA contrast ratios

## Phase 4: User Story 2 - Enhanced Navigation Experience (Priority: P2)

**Goal**: Update the navbar logo to match the futuristic theme for visual consistency.

**Independent Test**: The navbar can be viewed independently and should display the new sleek minimalist humanoid robot head logo instead of the previous green cartoon robot.

- [ ] T026 [US2] Create new Navbar Logo component in src/theme/Navbar/Logo.js
- [ ] T027 [US2] Implement sleek minimalist humanoid robot head using images.png
- [ ] T028 [US2] Add appropriate accessible name for screen readers
- [ ] T029 [US2] Ensure logo appears consistently across all pages
- [ ] T030 [US2] Test logo visibility and accessibility on different screen sizes
- [ ] T031 [US2] Verify logo maintains visual consistency with homepage design

## Phase 5: User Story 3 - Module Discovery (Priority: P3)

**Goal**: Ensure module cards are easily discoverable with visually appealing design and clear navigation.

**Independent Test**: The module cards section can be viewed independently and should display 4 cards in a 2×2 grid with the specified content and styling.

- [ ] T032 [US3] Add content to first module card: "The Nervous System (ROS 2) → Foundations of modern robot operating systems"
- [ ] T033 [US3] Add content to second module card: "Digital Twins (Simulation) → Photorealistic simulation with Gazebo, Unity & Isaac Sim"
- [ ] T034 [US3] Add content to third module card: "The AI Brain (NVIDIA Isaac) → End-to-end GPU-accelerated robotics development"
- [ ] T035 [US3] Add content to fourth module card: "Vision-Language-Action (VLA) → Embodied foundation models that see, reason, and act"
- [ ] T036 [US3] Implement keyboard navigation support for module cards
- [ ] T037 [US3] Add screen reader announcements for each card's content and purpose
- [ ] T038 [US3] Test hover effects on module cards (subtle purple border and lift)
- [ ] T039 [US3] Verify all module cards are visible and accessible on desktop and mobile
- [ ] T040 [US3] Ensure "Explore Module" buttons are functional and accessible

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T041 Verify all existing sidebar navigation, documentation pages, and footer links remain unchanged
- [ ] T042 Test responsive behavior across various screen sizes beyond standard desktop/mobile
- [ ] T043 Implement image fallback for robotttt.jpeg in case it fails to load
- [ ] T044 Optimize homepage for Core Web Vitals (LCP, FID, CLS) on desktop and mobile
- [ ] T045 Test browser compatibility on Chrome, Firefox, Safari, and Edge (latest 2 versions)
- [ ] T046 Verify graceful degradation on older browsers that don't support advanced CSS features
- [ ] T047 Perform final accessibility audit to ensure WCAG 2.1 AA compliance
- [ ] T048 Test light/dark mode toggle functionality continues to work with new styling
- [ ] T049 Verify all interactive elements work with keyboard navigation
- [ ] T050 Run final site build to ensure all changes work correctly in production build