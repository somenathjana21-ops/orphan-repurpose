# Modern Frontend Redesign Specification (Asklepios Glassmorphic Design)

**Date**: 2026-10-10  
**Status**: Pending Review  
**Reference**: Asklepios Healthcare AI Design (Uploaded Mockup)  

---

## 1. Overview & Purpose

The OrphanRepurpose frontend currently displays functional research data but relies on a standard boxed layout with a traditional sidebar, dark indigo hero gradient, and conventional HTML/Tailwind form elements.

This specification details a complete architectural overhaul of the frontend user interface to adopt the modern, clean, frosted-glass healthcare aesthetic inspired by **Asklepios**:
1. **Framed Floating Canvas**: The entire platform resides inside a rounded white card container (`rounded-[32px]`, `shadow-2xl`) suspended on a neutral soft-slate backdrop (`#eef2f6`).
2. **Minimalist Top Navigation**: Replacing the rigid left sidebar with a spacious top navigation bar featuring a minimalist geometric mark (`+ orphan repurpose`), active pill links, benchmark disease quick-switchers, backend health telemetry, and an interactive slide-over `Main Menu`.
3. **Signature Frosted 3D Glass Hero**: A hero banner replicating the reference design:
   - High-impact display typography (*"Precision Orphan Disease AI Therapeutics"*).
   - Clean secondary description with disease & molecule metrics.
   - Dual action CTAs: rounded neutral pill button (*"Explore Benchmarks"*) and an electric cobalt-blue squircle `+` action button (`bg-blue-600 rounded-2xl`).
   - Pure CSS/SVG layered frosted 3D glass slabs stacked diagonally with cyan/ice-blue linear gradients, soft highlights, and live platform telemetry chips.
4. **Cohesive Glassmorphism Across All Pages**: Unified glass cards, refined badges, modern search bar, and elevated tables across the Dashboard, Disease Explorer, Candidate Rankings, Cytoscape Knowledge Graph Browser, Case Studies, and Dossier Builder.

---

## 2. Visual Identity & Design System

### 2.1 Color Palette
- **Canvas Backdrop**: `bg-slate-100/80` (`#f1f5f9` to `#e2e8f0`) — creates floating contrast for the framed application.
- **Card Surfaces**:
  - `bg-white/95 backdrop-blur-xl border border-slate-200/60 shadow-xs`
  - `bg-white/80 backdrop-blur-lg border border-white/60 shadow-glass`
- **Primary / Accent**:
  - **Electric Cobalt**: `#2563eb` (Tailwind `blue-600`), hover `#1d4ed8` (`blue-700`), focus ring `#3b82f6` (`blue-500`).
  - **Ice Blue / Cyan Gradient**: `from-sky-400/20 via-blue-500/15 to-indigo-500/25` for frosted glass slabs.
- **Text & Contrast**:
  - Primary Headlines: `text-slate-900` (`#0f172a`), font weight 700/800, `tracking-tight`.
  - Subtitles / Secondary: `text-slate-500` (`#64748b`), font weight 400/500.
  - Micro-labels: `text-slate-400` (`#94a3b8`), font weight 600, uppercase `tracking-wider text-[11px]`.
- **Status Badges**:
  - Validated / Success: Emerald (`bg-emerald-50 text-emerald-700 border-emerald-200/60`)
  - Caution / Low Evidence: Amber (`bg-amber-50 text-amber-700 border-amber-200/60`)
  - Warning / Adverse: Rose (`bg-rose-50 text-rose-700 border-rose-200/60`)
  - GNN / AI: Cobalt / Sky (`bg-blue-50 text-blue-700 border-blue-200/60`)

### 2.2 Typography
- Primary Font: Geometric sans-serif (`Inter`, system-ui, -apple-system, sans-serif) with tight letter spacing.
- Font Sizes:
  - Hero Title: `text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight`
  - Section Headings: `text-xl sm:text-2xl font-bold tracking-tight text-slate-900`
  - Card Titles: `text-base sm:text-lg font-semibold text-slate-900`
  - Body: `text-sm leading-relaxed text-slate-600`
  - Monospace: `"JetBrains Mono", monospace` for ORPHA codes and SMILES strings.

---

## 3. Component Architecture & Structural Changes

### 3.1 App Shell & Container Layout (`App.tsx` & `Layout.tsx`)
- **Structure**:
  ```tsx
  <div className="min-h-screen bg-slate-100/90 p-2 sm:p-4 lg:p-6 flex flex-col items-center justify-start">
    <div className="w-full max-w-[1536px] bg-white rounded-[28px] sm:rounded-[36px] shadow-2xl shadow-slate-300/40 border border-slate-200/60 flex flex-col min-h-[calc(100vh-2rem)] overflow-hidden">
      <DisclaimerBanner />
      <Navbar onOpenMenu={() => setMenuOpen(true)} />
      <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 sm:py-8 space-y-8 scrollbar-thin">
        <Routes>...</Routes>
      </main>
      <MainMenuDrawer isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  </div>
  ```
- **Top Navbar Elements**:
  1. **Brand Mark**: Stylized geometric cross `+` icon (`w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-lg`) + `orphan repurpose` in crisp lowercase typography with a subtle badge `asklepios biotech`.
  2. **Navigation Links**:
     - `Diseases` (`/`)
     - `Drug Candidates` (`/diseases/ORPHA:635/candidates`)
     - `Knowledge Graph` (`/kg`)
     - `Case Studies` (`/case-studies`)
     - `Dossier Builder` (`/dossier`)
     - Styled as clean pill links: active state gets `bg-slate-100 text-slate-900 font-semibold shadow-xs`, inactive gets `text-slate-500 hover:text-slate-900 hover:bg-slate-50`.
  3. **Benchmark Disease Chips**: Quick pills in the top bar for instant switching to benchmark conditions:
     - `NPC (ORPHA:635)`
     - `Cystic Fibrosis (ORPHA:793)`
  4. **System Health Status**: Minimalist live pulse dot (`emerald-500` for online backend, `amber-500` for connecting).
  5. **Main Menu Trigger**: Button styled as `Main Menu` with a sleek horizontal indicator pill, matching the top-right of the reference mockup. Clicking opens `MainMenuDrawer`.

### 3.2 Slide-Over Main Menu (`MainMenuDrawer.tsx`)
- Triggered by clicking `Main Menu` in the top bar.
- Sliding drawer from the right with frosted glass overlay:
  - Platform overview and quick links to all 6 modules.
  - Quick benchmark switchers (Niemann-Pick Type C, Cystic Fibrosis, Huntington Disease).
  - Model pipeline telemetry (DualEncoder GNN, RGCN embeddings, FAERS disproportionality).
  - Direct links to FastAPI Swagger docs (`/docs`), GitHub repository, and data citations.

### 3.3 The Signature Glass Hero (`Dashboard.tsx` & `GlassHero.tsx`)
The Hero card directly mirrors the uploaded design:
- **Left Column (Content & CTAs)**:
  - Micro-badge: `Personalized Therapeutics · AI Platform`
  - Headline:
    ```
    Precision
    Orphan Disease
    AI Therapeutics
    ```
  - Subtitle: *"OrphanRepurpose provides high-confidence AI drug candidate discovery, graph neural reasoning, and safety analytics across 4,357 rare diseases."*
  - Dual CTAs:
    - Primary Pill: `Try Benchmark (NPC)` (pill button, `bg-slate-100 hover:bg-slate-200 text-slate-900 font-medium px-5 py-2.5 rounded-full`)
    - Squircle Action Button: Royal-blue button (`w-11 h-11 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl flex items-center justify-center shadow-md shadow-blue-500/30 transition-transform active:scale-95`) with a bold `+` icon.
  - Interactive Benchmark Chips: Quick clickable tags for `Niemann-Pick Type C (ORPHA:635)`, `Cystic Fibrosis (ORPHA:793)`, and `Huntington Disease (ORPHA:98065)`.
- **Right Column (Layered 3D Glass Slabs Visual)**:
  - Multi-layered composition of stacked, angled, frosted glass slabs created with pure CSS 3D transforms (`rotate-[-12deg]`, `rotate-[-6deg]`, `rotate-[0deg]`).
  - Layer styling:
    - Layer 1 (Bottom): Frosted cyan gradient `bg-gradient-to-tr from-sky-400/20 to-blue-600/30 backdrop-blur-md rounded-2xl border border-white/40 shadow-xl`.
    - Layer 2 (Middle): Translucent azure gradient `bg-gradient-to-tr from-cyan-300/25 to-blue-500/25 backdrop-blur-lg rounded-2xl border border-white/60 shadow-2xl`.
    - Layer 3 (Foreground): Clean glass card showing real-time AI metrics:
      - `98.2% AUROC` (Model Efficacy)
      - `4,357 Rare Diseases`
      - `GNN + Cross Attention Engine`
    - Specular highlights and edge reflection lines using CSS linear gradients.

### 3.4 Key Platform Views Overhaul

#### A. Dashboard (`Dashboard.tsx`)
- **Metric Cards**: 4 modern cards with clean numbers, soft rounded icons, and micro-labels:
  1. *Curated Diseases*: `4,357` (Orphanet verified)
  2. *Approved Drugs*: `1,645` (DrugCentral bioactive)
  3. *Inference Engine*: `DualEncoder` (GNN + Attention)
  4. *Safety Screen*: `FAERS + ADMET` (Post-market reporting)
- **Search & Filter Bar**:
  - Spacious rounded search input (`rounded-2xl`, glass border, clean search icon, clear button).
  - Refined `Advanced Filters` toggle with expandable glass drawer (Prevalence threshold slider, Target Gene filter, Pathway search).
- **Disease Directory Table**:
  - Clean elevated card container with soft header styling.
  - Interactive rows with hover lift, unmet need score progress pills, gene tag badges, and chevron links to candidate predictions.

#### B. Disease Detail (`DiseaseDetail.tsx`)
- Clean header banner with ORPHA code badge, disease category, and prevalence metrics.
- Phenotype ontology tags and target gene cards styled in frosted-glass panels.
- Direct CTA button leading to candidate prediction engine with the cobalt-blue `+` accent.

#### C. Drug Candidate Rankings (`CandidateList.tsx`)
- High-contrast candidate table featuring:
  - Candidate rank and drug name with bioactive compound badges.
  - Efficacy probability bar with calibrated percentile scores.
  - GNN Graph distance and attention weight metrics.
  - ADMET safety rating (Favorable / Moderate / High Risk).
  - Inline Clinician Validation modal trigger with instant feedback.

#### D. Candidate Detail & Explanations (`CandidateDetail.tsx` & `ExplanationPanel.tsx`)
- Multi-column layout featuring:
  - Molecule card with chemical properties (MW, LogP, TPSA, HBD, HBA).
  - Graph Neural Network explanation subgraph.
  - Literature rationale and PubMed citations in clean glass panels.
  - ADMET safety radar chart.

#### E. Knowledge Graph Browser (`KGBrowser.tsx`)
- Framed Cytoscape viewport inside a sleek glass panel with interactive zoom, reset, and layout controls.
- Clean floating node inspector drawer showing entity properties and connected edges.

#### F. Case Studies & Dossier Builder (`CaseStudies.tsx` & `DossierBuilder.tsx`)
- Polished report layout with structured clinical sections, tab navigation, and one-click PDF generation preview.

---

## 4. Technical Implementation Strategy

### 4.1 Dependency Impact
- **No new heavyweight dependencies**: Zero external 3D libraries (no Three.js). Pure modern CSS3 3D transforms, gradients, and backdrop-filter utilities natively supported by Tailwind CSS.
- Continues using `lucide-react`, `@tanstack/react-query`, `react-router-dom`, `recharts`, and `cytoscape`.

### 4.2 Tailwind Configuration Enhancements (`tailwind.config.js`)
- Add custom color tokens:
  - `cobalt`: `{ 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' }`
  - `ice`: `{ 50: '#f0f9ff', 100: '#e0f2fe', 200: '#bae6fd' }`
- Add custom box shadows:
  - `glass-sm`: `0 4px 16px 0 rgba(31, 38, 135, 0.05)`
  - `glass-lg`: `0 12px 40px 0 rgba(31, 38, 135, 0.10)`
  - `glow-cobalt`: `0 0 25px -5px rgba(37, 99, 235, 0.35)`
- Add custom border-radius:
  - `'3xl'`: `1.75rem`
  - `'4xl'`: `2.25rem`

### 4.3 Global CSS Refinements (`index.css`)
- Update base canvas background: `bg-slate-100/90 text-slate-900`.
- Modernize `.btn-primary` to cobalt blue gradient with soft glow.
- Define `.glass-card` and `.glass-panel` component classes for reusability.
- Update custom scrollbars to ultra-thin unobtrusive style.

---

## 5. Verification & Test Plan

1. **Compilation & Build**:
   - Run `npm run build` inside `prototype/frontend` to verify TypeScript compilation and Vite bundling with zero errors.
2. **Linting**:
   - Run `npm run lint` inside `prototype/frontend` to ensure code style compliance.
3. **Visual & Responsive Verification**:
   - Validate on desktop (wide framed card view) and mobile (fluid full-width responsive layout).
   - Ensure all routes (`/`, `/diseases/:orphaId`, `/diseases/:orphaId/candidates`, `/candidates/:candidateId`, `/kg`, `/case-studies`, `/dossier`) render cleanly without layout overflow or visual glitches.
4. **Backend Health & Interactions**:
   - Verify search filtering, pagination, benchmark switching, and drawer toggles function seamlessly.
