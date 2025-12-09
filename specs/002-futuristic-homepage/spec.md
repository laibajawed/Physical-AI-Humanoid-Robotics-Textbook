# Feature Specification: Futuristic Homepage UI Upgrade

**Feature Branch**: `002-futuristic-homepage`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "Physical AI & Humanoid Robotics Textbook (current live Docusaurus v3 site)
Goal: Upgrade ONLY the homepage UI to the exact premium dark futuristic style shown in the Sentient Machines screenshots, while keeping every existing page, sidebar, module, and content 100% unchanged.

Files to modify/create:
1. src/pages/index.js     ← completely replace with new homepage (or index.mdx if you use MDX)
2. src/css/custom.css    ← add any required extra styles / particle background
3. src/theme/Navbar/Logo.js or static/img/logo.svg ← (optional) update logo

Exact design requirements (must match Sentient Machines aesthetic 1:1):

• Background: #0F0F1A
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
• Maintain existing light/dark mode toggle with new futuristic styling
• Output only the modified/added files with full code"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Homepage Visual Upgrade (Priority: P1)

As a visitor to the Physical AI & Humanoid Robotics textbook website, I want to see a premium futuristic dark-themed homepage that creates a compelling first impression and clearly communicates the value proposition of the content.

**Why this priority**: This is the primary goal of the feature - to upgrade the homepage UI to match the futuristic aesthetic, which is the first interaction users have with the site and significantly impacts their perception of the content quality.

**Independent Test**: The homepage can be viewed independently and should showcase the new dark futuristic design with gradient text and module cards, delivering an immediate premium feel to visitors.

**Acceptance Scenarios**:

1. **Given** I am a new visitor to the website, **When** I land on the homepage, **Then** I see a dark futuristic design with gradient text ("Think → Move → Learn"), and the specified module cards.

2. **Given** I am viewing the homepage on desktop, **When** I look at the layout, **Then** I see the hero text on the left 55% and the robot image on the right 45%.

3. **Given** I am viewing the homepage on mobile, **When** I look at the layout, **Then** I see the content stacked vertically in a responsive manner.

4. **Given** I am using a screen reader, **When** I navigate the homepage, **Then** all elements have appropriate ARIA labels and semantic HTML structure.

---

### User Story 2 - Enhanced Navigation Experience (Priority: P2)

As a visitor to the website, I want to see an updated navbar logo that matches the futuristic theme, so that the entire header area feels cohesive with the new design aesthetic.

**Why this priority**: The navbar logo is a key visual element that should align with the overall futuristic theme to maintain visual consistency across the site.

**Independent Test**: The navbar can be viewed independently and should display the new sleek minimalist humanoid robot head logo instead of the previous green cartoon robot.

**Acceptance Scenarios**:

1. **Given** I am viewing any page on the website, **When** I look at the navbar, **Then** I see the updated sleek minimalist humanoid robot head logo.

2. **Given** I am on any internal page of the site, **When** I view the navbar, **Then** the logo remains consistent with the homepage design.

3. **Given** I am using a screen reader, **When** I navigate to the logo, **Then** it has an appropriate accessible name that describes it as the site logo.

---

### User Story 3 - Module Discovery (Priority: P3)

As a visitor interested in robotics education, I want to easily discover the different learning modules through visually appealing cards with clear call-to-action buttons, so I can navigate to the content that interests me most.

**Why this priority**: The module cards are a key navigation element that helps users explore the content structure and find relevant information.

**Independent Test**: The module cards section can be viewed independently and should display 4 cards in a 2×2 grid with the specified content and styling.

**Acceptance Scenarios**:

1. **Given** I am on the homepage, **When** I view the module cards section, **Then** I see 4 dark cards (#1A1A2E) with 16px radius, hover effects, and "Explore Module" buttons.

2. **Given** I am hovering over a module card, **When** I move my cursor over it, **Then** I see the subtle purple border and lift effect as specified.

3. **Given** I am using a keyboard to navigate, **When** I tab to the module cards, **Then** I can access all interactive elements using keyboard navigation.

4. **Given** I am using a screen reader, **When** I navigate to the module cards, **Then** each card's content and purpose is clearly announced.

## Edge Cases

- What happens when the robottt.jpeg image fails to load? The page should display a fallback image or placeholder.
- How does the layout adapt for various screen sizes beyond standard desktop/mobile? The design should remain responsive across all device sizes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display the homepage with a dark background color of #0F0F1A
- **FR-002**: System MUST display the hero section with "Think → Move → Learn" text in purple→pink gradient (#A78BFA → #F472B6)
- **FR-003**: System MUST show the subtitle "The Complete Handbook for Humanoid Intelligence..." in clean white text
- **FR-004**: System MUST display a pill-shaped CTA button with purple→pink gradient and text "Start Building →" with hover effects
- **FR-005**: System MUST show the robottt.jpeg image on the right side of the hero section on desktop
- **FR-006**: System MUST update the navbar logo to show a sleek minimalist humanoid robot head from images.png
- **FR-007**: System MUST display 4 module cards in a 2×2 grid layout with dark background (#1A1A2E)
- **FR-008**: System MUST show hover effects on cards with subtle purple border and lift effect
- **FR-009**: System MUST display "Explore Module" white pill buttons on each card
- **FR-010**: System MUST maintain all existing sidebar navigation, documentation pages, and footer links unchanged
- **FR-011**: System MUST be fully responsive and adapt layout for mobile devices (stacked content)
- **FR-012**: System MUST maintain existing light/dark mode toggle functionality with new futuristic styling
- **FR-013**: System MUST maintain WCAG 2.1 AA contrast ratios for all text elements against the dark background
- **FR-014**: System MUST provide appropriate ARIA labels for all interactive elements and visual components
- **FR-015**: System MUST display the existing module content from the project with the new futuristic styling, preserving all current educational content and structure
- **FR-016**: System MUST ensure all existing content remains accurate and maintains the educational tone of the textbook
- **FR-017**: System MUST be compatible with modern browsers including Chrome, Firefox, Safari, and Edge (latest 2 versions)
- **FR-018**: System MUST gracefully degrade on older browsers that don't support advanced CSS features

### Key Entities

- **Homepage Layout**: The visual structure containing hero section and module cards
- **Module Cards**: Four distinct learning modules (ROS 2, Simulation, NVIDIA Isaac, Vision-Language-Action) with descriptive text
- **Navbar Logo**: Updated branding element featuring a sleek humanoid robot head

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users spend at least 20% more time on the homepage compared to the previous design
- **SC-002**: The homepage loads within 3 seconds on standard broadband connections with all visual elements displayed
- **SC-003**: At least 85% of users can identify the main value proposition of the textbook within 10 seconds of viewing the homepage
- **SC-004**: All module cards are clearly visible and accessible on both desktop and mobile devices without layout issues
- **SC-005**: The updated navbar logo is clearly visible and maintains visual consistency with the futuristic theme
- **SC-006**: The homepage achieves a Core Web Vitals score of "Good" in all categories (LCP, FID, CLS) on desktop and mobile
- **SC-007**: All text elements maintain WCAG 2.1 AA contrast ratios (minimum 4.5:1) against the dark background
- **SC-008**: The homepage functions correctly and displays properly on Chrome, Firefox, Safari, and Edge (latest 2 versions)