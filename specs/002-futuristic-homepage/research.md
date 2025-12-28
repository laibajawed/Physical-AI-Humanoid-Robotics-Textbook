# Research: Futuristic Homepage UI Upgrade

## Decision: Homepage Structure and Technology Stack
**Rationale**: Based on analysis of the existing Docusaurus 3.x project structure, the implementation will leverage the current tech stack (TypeScript, React, Tailwind CSS) to maintain consistency with the project constitution and existing codebase. The new homepage will be implemented as a complete replacement of the existing `src/pages/index.tsx` file.

**Alternatives considered**:
- Creating a new page instead of replacing: Rejected because the requirement is to upgrade the homepage, not create an additional page
- Using different styling approach: Rejected because Tailwind CSS is already established in the project and aligns with the constitution

## Decision: Component Structure
**Rationale**: The new homepage will be built with React components following Docusaurus conventions. The layout will include a hero section with gradient text and image, and a 2×2 grid of module cards, all implemented as part of the main index.tsx file or supporting components.

**Alternatives considered**:
- Breaking into multiple components: Considered but rejected for initial implementation to keep the homepage self-contained, with potential refactoring later if needed

## Decision: Styling Approach
**Rationale**: The design will use Tailwind CSS v4 for most styling needs as required by the project constitution, with additional custom CSS in `src/css/custom.css` for specific requirements like the exact gradient colors and hover animations that may not be easily achievable with Tailwind alone.

**Alternatives considered**:
- Pure Tailwind: Insufficient for exact gradient specifications and complex animations
- CSS Modules: Would create additional files, custom.css approach is simpler for this focused change

## Decision: Image Handling
**Rationale**: The robotttt.jpeg image will be placed in the static/img directory and referenced directly. The new logo from images.png will be processed and placed in the appropriate location for the navbar.

**Alternatives considered**:
- Using dynamic imports: Unnecessary complexity for static assets
- Inline SVG for logo: The requirement specifies using the images.png file directly

## Decision: Responsive Design Implementation
**Rationale**: Will use Tailwind's responsive utility classes (e.g., md:, lg:) to achieve the required desktop (55%/45% split) and mobile (stacked) layouts as specified in the requirements.

**Alternatives considered**:
- Custom media queries: Unnecessary when Tailwind provides responsive utilities
- JavaScript-based responsive logic: CSS-based approach is more performant and appropriate

## Decision: Gradient Implementation
**Rationale**: The purple→pink gradient (#A78BFA → #F472B6) will be implemented using Tailwind's gradient utilities or custom CSS as needed, applied to the "Think → Move → Learn" text elements.

**Alternatives considered**:
- Background-clip method: Will use standard Tailwind gradient classes where possible, custom CSS if needed

## Decision: Module Cards Implementation
**Rationale**: The 4 module cards will be implemented using a CSS Grid or Flexbox layout with Tailwind classes to achieve the 2×2 grid on desktop and responsive stacking on mobile. Each card will have the specified dark background (#1A1A2E), hover effects, and "Explore Module" buttons.

**Alternatives considered**:
- Different layout systems: CSS Grid and Flexbox are standard and well-supported approaches