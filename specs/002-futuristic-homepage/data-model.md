# Data Model: Futuristic Homepage UI

## Entities

### Homepage Layout
- **Type**: UI Component
- **Fields**:
  - background: string (color code, e.g. #0F0F1A)
  - layout: object (desktop: 55%/45% split, mobile: stacked)
  - darkModeOnly: boolean (true)

### Module Card
- **Type**: UI Component
- **Fields**:
  - id: string (unique identifier)
  - title: string (card title text)
  - description: string (card description text)
  - backgroundColor: string (default #1A1A2E)
  - hoverBorderColor: string (purple border on hover)
  - borderRadius: number (16px radius)
  - hoverEffect: string (lift effect on hover)

### Hero Section
- **Type**: UI Component
- **Fields**:
  - title: string (gradient text "Think → Move → Learn")
  - subtitle: string (description text)
  - ctaButton: object (pill-shaped gradient button)
  - heroImage: string (path to robotttt.jpeg)
  - gradientColors: object (from #A78BFA to #F472B6)

### Navbar Logo
- **Type**: UI Component
- **Fields**:
  - imageSource: string (path to images.png)
  - altText: string (accessible name)
  - style: string (sleek minimalist humanoid robot head)

## Relationships
- Homepage Layout contains Hero Section
- Homepage Layout contains 4 Module Cards arranged in 2×2 grid
- Navbar Logo exists independently in site header

## State Transitions
- Module Card: normal → hover (border and lift effect)
- CTA Button: normal → hover (glow and scale effect)