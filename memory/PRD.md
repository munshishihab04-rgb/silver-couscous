# LicenzPol — Product Requirements Document

## Original problem statement
Build a premium European e-commerce for LicenzPol selling digital software licenses
(operating systems, Office, creative suites, CAD, cybersecurity, business tools).
Vision: make software simple. Feel: Linear + Apple + Stripe + Vercel. Full site
with hero-led homepage, catalog with rich filters, complete product pages,
compare, persistent cart, guest checkout demo, support, transparency pages,
IT + EN bilingual. Avoid fake reviews, fake timers, fake scarcity, stock photos,
copyrighted software box imagery.

## User choices (locked)
- Simulated checkout only (no real payments; explicit "Demo Mode" state).
- Guest checkout only (no login/registration).
- No AI assistant — static filters and comparisons only.
- Wide realistic catalog (real product names + plausible market prices).
- Italian + English (default Italian).

## Architecture
- **Backend** — FastAPI (`/api/*`) with a static catalog module (`catalog.py`),
  MongoDB for orders & support messages, no auth. Endpoints:
  `/api/categories`, `/api/needs`, `/api/products` (rich query params),
  `/api/products/{slug}`, `/api/related/{slug}`, `/api/orders`, `/api/orders/{ref}`,
  `/api/support`.
- **Frontend** — React 19 + React Router + Tailwind + Shadcn UI (accordion, sheet,
  sonner toasts). Two contexts (Lang, Cart). Cart & compare persisted in localStorage.
- **Design system** — dark theme (#050505), Cabinet Grotesk + Outfit + IBM Plex + JetBrains Mono,
  category color meshes, grain overlays, glass nav, pill CTAs, editorial layouts.

## Implemented (Feb 2026)
- 31-product realistic catalog across 7 categories (OS, Office, Security, Creative, CAD, Business, Utility)
- Home with 7 sections: hero → needs → categories → curated → how-it-works → why → transparency → FAQ → CTA
- Catalog with sidebar filters (category / platform / brand / license type), sort, mobile filter drawer
- Product detail with variant selector (edition / duration / devices), what-you-get, features,
  compatibility, activation steps, product-level FAQ, related products
- Compare page (up to 3 products, side-by-side table)
- Cart drawer (persistent, qty controls, subtotal, remove)
- 3-step checkout (details → payment demo notice → confirmation with LP-XXXX reference)
- Support page (form → `/api/support`)
- Transparency + Legal placeholder pages
- IT / EN language toggle everywhere
- Full mobile experience (mobile nav, mobile filter drawer, thumb-friendly CTAs)

## Backlog / P1
- Order lookup page (GET by reference) for order status
- Real payment integration (Stripe) when going live
- Newsletter capture + email delivery of demo confirmations
- Volume-licence / B2B quote request flow
- Real product screenshots when officially licensed

## Backlog / P2
- Blog / knowledge base (SEO)
- Wishlist / saved lists
- Bundles ("Casa", "Studio", "PMI")
- AI assistant integration for guided discovery
- Admin dashboard for support tickets and orders
