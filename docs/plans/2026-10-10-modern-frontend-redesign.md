# Modern Frontend Redesign (Asklepios Glassmorphic) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline execution or subagent-driven development to implement this plan task-by-task. Track progress using checkbox (`- [ ]`) syntax.

**Goal:** Overhaul the OrphanRepurpose frontend into a modern, clinical-grade biotech AI portal matching the uploaded Asklepios reference design (floating framed canvas, sleek top navigation, signature 3D frosted-glass hero, and cohesive glassmorphic styling across all views).

**Architecture:** Extend Tailwind tokens with glass surfaces and cobalt/ice-blue accents; replace the left sidebar with a floating `AppShell` and responsive `Navbar` + `MainMenuDrawer`; create the signature pure-CSS `GlassHero` with stacked 3D frosted glass slabs; modernize all view components with elevated cards and refined typography.

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3.4, Lucide React, Vite, TanStack Query.

**Spec:** [docs/specs/2026-10-10-modern-frontend-redesign.md](file:///c:/dev/orphan-repurpose/docs/specs/2026-10-10-modern-frontend-redesign.md)

---

## Global Constraints

- **No New Heavy Dependencies**: Do not install Three.js or WebGL engines; use pure CSS transforms, gradients, and backdrop filters for glass rendering.
- **Maintain API & State Contracts**: Do not break existing API calls (`diseasesApi`, `candidatesApi`, `kgApi`, `dossierApi`), query keys, or URL route structures.
- **Strict Verification**: Every task must compile clean with `npm run build` (`tsc && vite build`) and pass `npm run lint`.
- **Responsive Floor**: Must cleanly scale from mobile viewports (stacked layout) to ultra-wide displays (framed floating card).

## Review Focus

- **Hero Glassmorphic Fidelity**: Translucent layering, cyan/ice-blue gradients, and specular highlights must look crisp without causing scrollbar or layout overflow.
- **Navigation Usability**: The top bar and `Main Menu` drawer must provide immediate access to all existing routes (`/`, `/diseases/:orphaId`, `/diseases/:orphaId/candidates`, `/candidates/:candidateId`, `/kg`, `/case-studies`, `/dossier`).
- **Interactive States**: Buttons, benchmark chips, search filters, and table rows must provide smooth micro-interactions (hover, active scale, focus rings).

---

### Task 1: Tailwind Design Tokens & Base Glassmorphic Styles

**Files:**
- Modify: `prototype/frontend/tailwind.config.js`
- Modify: `prototype/frontend/src/index.css`

**Interfaces & Tokens:**
- Add colors: `cobalt` (`500: #3b82f6`, `600: #2563eb`, `700: #1d4ed8`), `ice` (`50: #f0f9ff`, `100: #e0f2fe`, `200: #bae6fd`, `400: #38bdf8`)
- Add shadows: `glass-sm`, `glass-md`, `glass-lg`, `glow-cobalt`
- Add border-radius: `'3xl': '1.75rem'`, `'4xl': '2.25rem'`
- CSS utility classes: `.glass-panel`, `.glass-card`, `.glass-slab`, `.btn-cobalt`, `.btn-pill`

- [x] **Step 1: Update `tailwind.config.js` with new tokens**
- [x] **Step 2: Update `src/index.css` with canvas background, glass utilities, and button classes**
- [x] **Step 3: Run build verification**  
  Run: `cd prototype/frontend && npm run build`  
  Expected: PASS (`tsc && vite build`)
- [x] **Step 4: Commit**
  ```bash
  git add prototype/frontend/tailwind.config.js prototype/frontend/src/index.css
  git commit -m "feat(frontend): add asklepios glassmorphic tailwind tokens and utilities"
  ```

---

### Task 2: Floating App Shell, Modern Navbar & Main Menu Drawer

**Files:**
- Create: `prototype/frontend/src/components/Navbar.tsx`
- Create: `prototype/frontend/src/components/MainMenuDrawer.tsx`
- Modify: `prototype/frontend/src/components/Layout.tsx`
- Modify: `prototype/frontend/src/App.tsx`

**Interfaces:**
- `Navbar({ onOpenMenu: () => void }): JSX.Element`
- `MainMenuDrawer({ isOpen: boolean, onClose: () => void }): JSX.Element`
- `Layout({ children }: { children?: ReactNode }): JSX.Element` (wraps content in framed floating canvas)

- [x] **Step 1: Create `prototype/frontend/src/components/MainMenuDrawer.tsx`**  
  Implements slide-over drawer with platform modules, model info, benchmark shortcuts, and API docs.
- [x] **Step 2: Create `prototype/frontend/src/components/Navbar.tsx`**  
  Implements top bar with minimalist geometric logo `+`, lowercase typography, active route pills, benchmark disease chips, live status dot, and `Main Menu` trigger.
- [x] **Step 3: Update `prototype/frontend/src/components/Layout.tsx` and `prototype/frontend/src/App.tsx`**  
  Replaces sidebar with floating framed container (`rounded-[32px]`, `shadow-2xl`) and top navbar.
- [x] **Step 4: Run build & lint verification**  
  Run: `cd prototype/frontend && npm run build && npm run lint`  
  Expected: PASS with 0 warnings/errors.
- [x] **Step 5: Commit**
  ```bash
  git add prototype/frontend/src/components/Navbar.tsx prototype/frontend/src/components/MainMenuDrawer.tsx prototype/frontend/src/components/Layout.tsx prototype/frontend/src/App.tsx
  git commit -m "feat(frontend): implement framed canvas shell, top navbar, and main menu drawer"
  ```

---

### Task 3: Signature 3D Frosted-Glass Hero Component

**Files:**
- Create: `prototype/frontend/src/components/GlassHero.tsx`
- Modify: `prototype/frontend/src/components/Dashboard.tsx`

**Interfaces:**
- `GlassHero({ onSelectBenchmark: (orphaId: string) => void }): JSX.Element`

- [x] **Step 1: Implement `GlassHero.tsx`**  
  - Left column: "Precision Orphan Disease AI Therapeutics", clean copy, dual CTAs ("Try Benchmark (NPC)" pill + royal-blue squircle `+` button), benchmark disease chips.
  - Right column: Stacked 3D angled frosted glass slabs with cyan/ice-blue gradients (`from-sky-400/20 to-blue-600/30`), reflection lines, and live model telemetry chips (`98.2% AUROC`, `4,357 Diseases`, `GNN + Attention`).
- [x] **Step 2: Integrate `GlassHero` into `Dashboard.tsx` replacing the old dark indigo hero**
- [x] **Step 3: Run build & lint verification**  
  Run: `cd prototype/frontend && npm run build && npm run lint`  
  Expected: PASS
- [x] **Step 4: Commit**
  ```bash
  git add prototype/frontend/src/components/GlassHero.tsx prototype/frontend/src/components/Dashboard.tsx
  git commit -m "feat(frontend): implement signature 3D frosted-glass hero component"
  ```

---

### Task 4: Modernized Stat Metric Cards & Disease Search Table

**Files:**
- Modify: `prototype/frontend/src/components/Dashboard.tsx`

- [x] **Step 1: Modernize the 4 metric cards**  
  Clean typography, soft icon containers, refined labels for Diseases (4,357), Approved Drugs (1,645), Prediction Engine (DualEncoder), and Safety Engine (FAERS).
- [x] **Step 2: Restyle the search input and collapsible advanced filters tray**  
  Modern rounded search bar with glass borders, active filter indicator, and clean sliders/dropdowns.
- [x] **Step 3: Redesign the disease directory table**  
  Elevated card container, clean column headers, unmet need progress bars, gene tag badges, and chevron links.
- [x] **Step 4: Run build & lint verification**  
  Run: `cd prototype/frontend && npm run build && npm run lint`  
  Expected: PASS
- [x] **Step 5: Commit**
  ```bash
  git add prototype/frontend/src/components/Dashboard.tsx
  git commit -m "feat(frontend): modernize dashboard metrics, search filter, and disease table"
  ```

---

### Task 5: Glassmorphic Styling for Disease & Candidate Exploration

**Files:**
- Modify: `prototype/frontend/src/components/DiseaseDetail.tsx`
- Modify: `prototype/frontend/src/components/CandidateList.tsx`
- Modify: `prototype/frontend/src/components/CandidateDetail.tsx`

- [x] **Step 1: Update `DiseaseDetail.tsx`**  
  Clean hero card, phenotype ontology badges, gene targets, and CTA to candidate rankings.
- [x] **Step 2: Update `CandidateList.tsx`**  
  Refined candidate rankings table with GNN score pills, ADMET safety rating meters, and modern inline clinician validation modal.
- [x] **Step 3: Update `CandidateDetail.tsx`**  
  Sleek multi-column layout for molecule chemical properties, GNN explanation subgraphs, literature rationale, and ADMET radar.
- [x] **Step 4: Run build & lint verification**  
  Run: `cd prototype/frontend && npm run build && npm run lint`  
  Expected: PASS
- [x] **Step 5: Commit**
  ```bash
  git add prototype/frontend/src/components/DiseaseDetail.tsx prototype/frontend/src/components/CandidateList.tsx prototype/frontend/src/components/CandidateDetail.tsx
  git commit -m "feat(frontend): modernize disease detail and candidate exploration views"
  ```

---

### Task 6: Modern Polish for KGBrowser, CaseStudies & DossierBuilder

**Files:**
- Modify: `prototype/frontend/src/components/KGBrowser.tsx`
- Modify: `prototype/frontend/src/components/CaseStudies.tsx`
- Modify: `prototype/frontend/src/components/DossierBuilder.tsx`

- [x] **Step 1: Polish `KGBrowser.tsx`**  
  Framed Cytoscape canvas inside sleek glass panels, modern floating controls and node inspector.
- [x] **Step 2: Polish `CaseStudies.tsx`**  
  Elevated clinical case study presentation (Niemann-Pick Type C & Cystic Fibrosis).
- [x] **Step 3: Polish `DossierBuilder.tsx`**  
  Clean IND regulatory dossier generator layout with PDF export buttons.
- [x] **Step 4: Run build & lint verification**  
  Run: `cd prototype/frontend && npm run build && npm run lint`  
  Expected: PASS
- [x] **Step 5: Commit**
  ```bash
  git add prototype/frontend/src/components/KGBrowser.tsx prototype/frontend/src/components/CaseStudies.tsx prototype/frontend/src/components/DossierBuilder.tsx
  git commit -m "feat(frontend): modernize kg browser, case studies, and dossier builder"
  ```

---

### Task 7: Full Frontend End-to-End Build & Lint Verification

**Files:**
- Full frontend repository

- [x] **Step 1: Run full production build**  
  Run: `cd prototype/frontend && npm run build`
- [x] **Step 2: Run ESLint**  
  Run: `cd prototype/frontend && npm run lint`
- [x] **Step 3: Final git status check and verification**
