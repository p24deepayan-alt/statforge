---
name: Analytical Precision
colors:
  surface: '#f8faf9'
  surface-dim: '#d8dad9'
  surface-bright: '#f8faf9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f3'
  surface-container: '#eceeed'
  surface-container-high: '#e6e9e8'
  surface-container-highest: '#e1e3e2'
  on-surface: '#191c1c'
  on-surface-variant: '#454650'
  inverse-surface: '#2e3131'
  inverse-on-surface: '#eff1f0'
  outline: '#757681'
  outline-variant: '#c5c5d2'
  surface-tint: '#495b9c'
  primary: '#001857'
  on-primary: '#ffffff'
  primary-container: '#1b2f6e'
  on-primary-container: '#8799df'
  inverse-primary: '#b6c4ff'
  secondary: '#5e5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e1dfdf'
  on-secondary-container: '#626262'
  tertiary: '#002424'
  on-tertiary: '#ffffff'
  tertiary-container: '#003b3b'
  on-tertiary-container: '#3dacac'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b6c4ff'
  on-primary-fixed: '#001550'
  on-primary-fixed-variant: '#304382'
  secondary-fixed: '#e4e2e2'
  secondary-fixed-dim: '#c7c6c6'
  on-secondary-fixed: '#1b1c1c'
  on-secondary-fixed-variant: '#464747'
  tertiary-fixed: '#8bf3f3'
  tertiary-fixed-dim: '#6ed7d7'
  on-tertiary-fixed: '#002020'
  on-tertiary-fixed-variant: '#004f50'
  background: '#f8faf9'
  on-background: '#191c1c'
  surface-variant: '#e1e3e2'
typography:
  h1:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  data-mono:
    fontFamily: Space Grotesk
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 12px
  sidebar_width: 260px
---

## Brand & Style

This design system is engineered for professional environments where data integrity and clarity are paramount. The brand personality is rooted in scientific reliability and industrial precision, targeting data scientists and researchers who require an efficient, distraction-free environment.

The visual style is **Corporate / Modern** with a lean toward **Minimalism**. It prioritizes information density without sacrificing legibility. The UI relies on a systematic arrangement of "containers" to categorize complex workflows, using a high-contrast relationship between the workspace and the peripheral controls to guide the user's focus toward the data.

## Colors

The palette is anchored by **Biscay Blue**, used strategically for primary actions, headers, and active states to denote importance and stability. **Black Haze** serves as the primary canvas color for the application shell, while a crisp **White** is reserved exclusively for the "Sheet" or "Workspace" area where data entry and analysis occur.

**Dove Gray** provides a neutral framework for borders and secondary metadata, ensuring that the interface remains structural but unobtrusive. For data visualization and status indicators, a **Soft Teal** represents growth or positive trends, while **Coral** is used for outliers, errors, or critical data points.

## Typography

This design system utilizes **Inter** for the vast majority of interface elements. Its high x-height and systematic weights ensure legibility even at the small sizes required for dense data tables. 

For numerical values, coordinates, and code snippets, **Space Grotesk** is employed. This provides a clear visual distinction between "UI Text" and "Data Values," allowing users to scan statistical outputs quickly. Labels for axes and table headers should use the `label-caps` style to provide a rigid, organized structure to the information hierarchy.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model. The primary navigation and property panels are fixed-width sidebars, while the central workspace expands to fill the available viewport. This ensures that analytical tools remain in consistent positions while data visualizations have maximum room to breathe.

A strict **4px baseline grid** governs all spacing. For data-heavy tables, use "Compact" spacing (8px cell padding) to maximize information density. For general interface forms, use "Standard" spacing (16px) to maintain user-friendliness and prevent cognitive overload.

## Elevation & Depth

Hierarchy is established primarily through **Tonal Layering** rather than heavy shadows. The background shell (Black Haze) sits at the lowest level. Workspace surfaces (White) are elevated slightly through a 1px Dove Gray border.

Subtle, ambient shadows are reserved for floating elements like dropdown menus, tooltips, or modals. These shadows should have a wide blur radius (12px - 16px) and very low opacity (8-10%) to feel integrated rather than "pasted on." This approach maintains the "flat" professional aesthetic while providing necessary depth cues for interactive overlays.

## Shapes

The design system employs **Soft** roundedness (4px radius). This slight rounding softens the technical nature of the application without making it appear "toy-like." 

- **Buttons & Inputs:** 4px radius.
- **Data Cards & Workspace Sheets:** 4px radius.
- **Contextual Chips:** 12px (Semi-pill) to distinguish them from actionable buttons.
- **Selection Indicators:** Sharp corners on vertical indicators (e.g., active tab markers) to emphasize alignment with the grid.

## Components

### Buttons
Primary buttons use the Biscay Blue background with White text. Secondary buttons utilize a White background with a 1px Dove Gray border. In data-heavy views, "Ghost" buttons (text only until hover) are preferred to reduce visual noise.

### Inputs
Input fields must have a clear 1px border. When focused, the border transitions to Biscay Blue with a subtle 2px outer glow of the same color at 20% opacity. Labels should always be visible (never placeholder-only) to maintain accessibility during complex data entry.

### Data Tables
Tables are the core of this design system. Headers use a Black Haze background to distinguish them from the data rows. Use alternating row stripes (Zebra striping) only when tables exceed 10 columns. The "Data-Mono" typography style is mandatory for all numerical cells.

### Chips & Tags
Use chips for "Variable" tokens (e.g., [Mean], [Standard Deviation]). These should have the Soft Teal background at 15% opacity with dark teal text to appear distinct from the primary UI buttons.

### Cards
Cards are used to group related statistical charts or summaries. They should feature a 1px Dove Gray border and no shadow, unless the user is actively dragging or reordering them.