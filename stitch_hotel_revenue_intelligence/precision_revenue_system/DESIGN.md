---
name: Precision Revenue System
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  data-mono:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 24px
  gutter: 16px
---

## Brand & Style

The design system is engineered for high-stakes financial decision-making within the hospitality sector. The brand personality is **analytical, authoritative, and frictionless**, prioritizing data clarity over decorative elements. 

The aesthetic follows a **refined Corporate Minimalism** approach. It leverages heavy whitespace to reduce cognitive load while maintaining a dense information architecture. The goal is to evoke a sense of "command and control," providing revenue managers with a high-contrast environment where critical trends and anomalies are immediately visible through purposeful color application and rigorous alignment.

## Colors

The palette is anchored by **Deep Navy (#0F172A)**, used for primary navigation and core brand elements to establish trust. **Accent Blue (#3B82F6)** serves as the primary action color, guiding the eye to interactive elements and primary CTAs.

**Functional Color Logic:**
- **Slate (#64748B):** Used for secondary text and icons to create a clear hierarchy against primary data.
- **Success Green (#10B981):** Reserved exclusively for positive revenue growth, occupancy increases, and system "active" states.
- **Danger Red (#EF4444):** Used for declining RevPAR, budget overruns, or critical system alerts.
- **Surface Tiers:** Uses a background of `#F8FAFC` with pure white (`#FFFFFF`) containers to subtly separate data modules.

## Typography

This design system utilizes **Inter** for its exceptional legibility in data-dense environments. The type scale is optimized for tabular data and complex dashboards.

**Implementation Rules:**
- **Tabular Figures:** For all numerical data, enable `tnum` (tabular numbers) to ensure columns of figures align vertically for quick scanning.
- **Hierarchy:** Use `label-caps` for table headers and section overlines to distinguish labels from interactive data.
- **Mobile Adaptation:** Large display titles scale down to `headline-md` on mobile devices. Body text remains at `14px` (body-md) to maintain legibility without excessive scrolling.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for dashboard views and a **fixed-width centered container (1280px)** for settings and administrative pages. 

- **Density:** To accommodate high information density, the design system employs a strict 4px baseline grid. 
- **Margins:** Standard page margins are set to `24px` on desktop, scaling down to `16px` on mobile.
- **Alignment:** Data points in tables should be right-aligned for numbers and left-aligned for text to facilitate rapid comparison.
- **Reflow:** On tablet, the 12-column grid collapses to 6 columns. On mobile, elements stack vertically into a single column with cards representing what were previously table rows.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layering** rather than heavy shadows. This maintains the clean, professional aesthetic required for enterprise software.

- **Level 0 (Canvas):** `#F8FAFC` – The base background.
- **Level 1 (Cards/Modules):** White surface with a `1px` border in `#E2E8F0`. 
- **Level 2 (Hover/Active states):** A subtle, highly-diffused shadow (`0 4px 6px -1px rgb(0 0 0 / 0.1)`) to indicate interactivity.
- **Overlays (Modals):** A backdrop blur (8px) with a semi-transparent dark overlay (`#0F172A` at 40% opacity) to focus user attention on critical inputs.

## Shapes

The design system uses a **Rounded** strategy to soften the corporate environment without appearing overly casual.

- **Standard Elements:** Buttons, input fields, and small cards use a `0.5rem` (8px) corner radius.
- **Large Containers:** Dashboard widgets and modal windows use `1rem` (16px) to clearly define major functional areas.
- **Data Indicators:** Status chips and badges use a fully rounded "pill" shape to contrast against the structured rectangular grid of the dashboard.

## Components

**Buttons:**
- **Primary:** Solid `#3B82F6` with white text. High-contrast, 8px radius.
- **Secondary:** Transparent background with `#0F172A` border and text. Used for less critical actions.

**Data Tables:**
- **Header:** Background `#F1F5F9`, `label-caps` typography, sticky on scroll.
- **Rows:** Alternating "zebra" stripes are avoided; instead, use a subtle bottom border (`1px solid #F1F5F9`).

**Input Fields:**
- Minimalist design with a `1px` border. On focus, the border transitions to Primary Blue with a subtle outer glow (2px).

**Data Visualization:**
- Charts should use the primary blue for main data trends, with secondary data in slate. Success/Danger colors are strictly reserved for variance indicators (e.g., +5.2% in Green).

**Key Metric Cards (KPIs):**
- Features a large `display-lg` value, a `label-caps` title, and a small trend sparkline to provide immediate context without navigating deeper into reports.