# Handoff: Graye Market (graye.market)

## Overview
Graye Market is a private marketplace for high-value heavy equipment. Buyers browse anonymized listings for free, then pay a flat fee to unlock a verified seller's contact details. The platform only makes the introduction. It never processes sale payments or takes a commission. `BRIEF.md` holds the full product brief.

## About the design files
The files here are **design references built in HTML**. They show the intended look and content. They are not production code to copy. Rebuild these screens in the target codebase using its existing framework and patterns. If there's no codebase yet, use Next.js (App Router) + TypeScript + Tailwind or CSS modules, with Stripe Checkout and Postgres.

Open `Graye Market.dc.html` in a browser to see every screen side by side. Each frame has a badge id (1a–1l) and a `data-screen-label`. Mock data lives in the `class Component` block at the bottom of the file.

## Fidelity
**High fidelity.** Final colors, type, spacing, copy and layout. Match them exactly. The only placeholders are the striped photo boxes, where real grayscale equipment photography will go.

## Product decisions (already made)
- Listing location is shown as a **region** (Midwest, Gulf Coast, Mountain West…), never a state or address.
- Verification is shown to buyers as a **badge plus a list of the checks that passed**. The documents themselves stay private.
- **No buyer subscription in v1.** Leave it out of the UI and pricing.
- Out of scope: sale payments, escrow, commissions, in-app messaging, shipping, inspections.

## Pricing (unlock fee by listing price)
| Listing price | Fee |
|---|---|
| Under $100K | $99 |
| $100K–$500K | $249 |
| $500K–$2M | $499 |
| $2M+ | $999 |

Refund rule: if the seller doesn't respond within **72 hours** of an unlock, the fee is refunded automatically through the Stripe refund API.

## Global layout
- Desktop frame is 1280px wide with 72px side gutters. Mobile frame is 390px wide with 20px gutters. The real build must be fully responsive, since many buyers browse on phones at job sites.
- Header: `.nav` bar with the wordmark on the left, then links (Browse, How it works, Pricing, Sell equipment, Sign in) and a primary "List equipment" button. On mobile it's the wordmark plus a 44px menu icon button.
- **Wordmark:** "Graye Market" in Archivo 800 at 22px (20px mobile), letter-spacing -0.01em. The **"e" in Graye is the accent red** (#ec3013) so people read the spelling correctly.
- Sections are separated by **2px rules** (`--color-divider`). Cards have a 2px solid ink top border. **Zero border radius everywhere.** Everything is flush left, including button labels.
- Photos: always grayscale (CSS `filter: grayscale(1)`). They use a 4:3 aspect on cards, 16:10 on the detail hero and 4:5 on the home hero.

## Screens

### 1a — Home / landing (desktop), 1i (mobile)
- Hero is a 7fr/5fr grid. On the left, the H1 "Browse free." / "Unlock verified sellers." is set one sentence per line in Archivo 800 at 80px (44px mobile), line-height 1.04, letter-spacing -0.025em. Under it, an 18px/28px sub (max 52ch): "A private marketplace for heavy equipment. Every seller is checked as the owner and ready to sell. Pay one flat fee to get their contact, then deal directly. No commission on the sale." The right column holds a 4:5 hero photo.
- Search bar: a 4-column grid (220px / 1fr / 180px / auto) inside a 2px ink border. The columns are Category, Make or model, Region and a primary "Search" button with a search icon. Each field has a 12px uppercase label (letter-spacing 0.08em) above its value. Below the bar: "1,284 verified listings · Excavators · Cranes …" at 14px.
- How it works: 3 equal columns with 2px dividers between them. Each has a number (01/02/03, 15px, 800, accent-700), a 26px 800 title and 16px/26px copy.
- Recently listed: a 3-column grid of listing cards (see component below).
- Pricing: a 5fr/7fr grid. The left side is the heading "One flat fee per seller" plus the refund copy. The right side is `.table` with the fee tiers.
- Red close band: a full-width `--color-accent` background, 72px padding, the H3 "Sell without broadcasting your fleet." at 56px 800 in `--color-bg` color, and a ghost button with a paper-colored border.
- Footer: "graye.market · Introductions only…" on the left, Terms · Privacy · Refund policy on the right, all 13px neutral-800.

### 1b — Search and results (desktop), 1j (mobile)
- Page header: kicker (category), H2 "214 verified listings" at 48px, and on the right the "Save this search" (secondary) and "Sort: Newest" (ghost) buttons.
- Active filter chips use `.tag.tag-neutral` with ×.
- Body grid is 240px / 1fr. The left filter rail has a 2px right rule and holds Category, Make, Model, Year from/to, Max hours, Price min/max, Region and a full-width primary "Show 214 results".
- Results sit in a 3-column grid of listing cards with a 24px gap. On mobile they're a single column with a "Filters · 4" button that opens a sheet (not drawn; build it as a bottom sheet).

### Listing card (shared component)
- `--color-surface` background, 2px ink top border, 4:3 grayscale photo.
- Body padding is 16px, with elements 6px apart. From top to bottom:
  - 12px uppercase meta line "Category · Region" (neutral-800)
  - 19–20px Archivo 800 title
  - 14px "Year · Hours" line
  - a row with the price (18px 800, tabular numbers) and a `.tag.tag-accent` "✓ Verified seller", above a 2px divider
  - on results only, a 13px line: "Seller contact · $249 to unlock"
- Hover state: background changes to neutral-200. The whole card links to the listing detail page.

### 1c — Listing detail, seller locked (desktop), 1k (mobile)
- Breadcrumb, then a 7fr/5fr grid.
- The left column has, in order:
  - a 16:10 hero photo and a 5-up thumbnail strip (the selected thumbnail gets a 2px ink inset outline)
  - a "Specifications" `.table` of key/value rows
  - a "Condition" paragraph
- Right column (sticky):
  - Meta kicker, the H2 title at 40px and the price at 44px 800.
  - **Locked seller block** in a 2px ink border. The header reads "Seller contact locked" with a lock icon. The Name, Company, Phone and Email rows show gray bars (neutral-400) in place of the values.
  - A full-width primary button, 52px tall, with "Unlock seller contact" on the left and the fee on the right (space-between).
  - Under the button: "One-time fee for this listing. If the seller doesn't reply within 72 hours, you're refunded automatically."
  - **Verification panel** on a surface background. The header "Verified seller" sits next to a tag "✓ Verified {date}". Below that are 4 check rows, separated by 2px dividers: Ownership confirmed, Identity checked, Ready to sell, and Response record ("Replied to 9 of 9 unlocks, median 5 hrs").
- Mobile: a sticky bottom bar with a 2px ink top border, the full-width "Unlock seller $249" button and a 12px refund line.

### 1d — Unlock checkout
- A slim header with only the wordmark and "Secure checkout".
- 6fr/5fr grid. The left side has:
  - the step kicker and the H2 "Unlock this seller"
  - a listing summary row (160px thumbnail)
  - "What you get", a numbered list of 4 items
- The right side is a summary panel on a surface background with a 2px ink top border:
  - Rows: the fee with its tier, "Commission on sale: None" and "Due today" at 36px.
  - The **72-hour guarantee** box: accent-100 background, accent-900 text.
  - A required checkbox acknowledging that Graye only makes the introduction.
  - The primary "Continue to payment →" button, which redirects to Stripe Checkout.
  - A note that Stripe handles the card.

### 1e — Unlocked listing (desktop), 1l (mobile)
- A tag "Unlocked {date time}", the H2 title and a meta line.
- Contact block in a 2px ink border with key/value rows: Name, Company, Phone, Email and Best time. Actions: Call seller (primary, `tel:`), Email seller (secondary, `mailto:`) and Copy details (ghost).
- Response status panel on the right:
  - The state title: Waiting for seller, Seller responded or Refunded.
  - Hours remaining, plus an 8px progress bar with the accent fill growing as time elapses.
  - An event timeline with 10px square dots: ink for past events, accent for the current one, neutral-400 for future ones.
  - "Seller responded" and "Report a problem" buttons.

### 1f — Seller onboarding and verification
- 4fr/8fr grid. The left side holds the intro and a 4-step list: Account, Business and identity, Proof of ownership, Review by Graye. Status tags: Done uses neutral, In progress uses accent, Up next uses outline.
- The right side is the active step, "Proof of ownership". It has:
  - a `.seg` document type picker (Bill of sale / Title or registration / Dealer invoice / Lien release)
  - a dashed dropzone and the uploaded file row
  - "Name on document" and "Machine make and model" fields
  - a footer with "Most reviews finish within one business day" and Back / Submit for review buttons

### 1g — Create or edit listing, photos step
- A 5-step tab strip (Machine, Specs, Photos, Price, Preview). The active tab has a 4px accent underline and completed tabs have an ink underline.
- The left side has:
  - a **privacy guidance box** (accent-100): don't show decals or signage, plates, serial/PIN plates, yard buildings or phone numbers
  - a 4-column photo grid; a flagged photo gets a 3px accent outline and an accent-700 caption
  - a warning row with a 2px accent border: "Photo 3 may show a fleet number…" with "Blur area" / "It's fine" buttons
- The right side shows a live **public preview** card plus a list of what's hidden: Seller name, Company, Serial/PIN, and the exact location, which buyers see only as a region.
- Suggested extra: run automatic OCR/plate detection on upload to raise these flags.

### 1h — Buyer dashboard
- H2 "My unlocks", then 4 stats (40px 800 numbers, 13px uppercase labels) separated by 2px vertical rules.
- `.table` with the columns Listing (title + id · region), Unlocked, Fee, Seller status (tag) and a View contact link.
- Saved searches: 3 `.card`s showing the kicker, criteria and "N new this week · Email cadence".

### Not yet designed
Seller dashboard (listings, unlock requests, plan). Build it in the same grammar as 1h.

## Interactions and behavior
- Unlock flow: listing → checkout → Stripe Checkout → webhook `checkout.session.completed` → create the unlock record, notify the seller by email and SMS, and redirect to the unlocked view.
- 72h timer: a scheduled job refunds any unlock with no `seller_responded_at` after 72h, then sets its status to `refunded`. A seller response can come from either the seller clicking a link in the notification or the buyer marking "Seller responded".
- Listing pages never expose seller identity, exact location or serials in HTML, API responses or image EXIF. Strip EXIF on upload.
- Hover/pressed/focus states come from the design system: hover tint, pressed accent-600, and focus `outline: 2px solid var(--color-accent); outline-offset: 2px`. Disabled controls are at 45% opacity.
- Mobile touch targets are at least 44px.

## Data model (suggested)
- `users` (role: buyer/seller/both)
- `sellers` (business, verification_status, checks jsonb)
- `listings` (category, make, model, year, hours, price_cents, region, condition, specs jsonb, status, featured)
- `listing_photos`
- `unlocks` (buyer_id, listing_id, fee_cents, stripe_session_id, paid_at, seller_responded_at, refunded_at, status)
- `saved_searches` (buyer_id, filters jsonb, cadence)
- `ownership_documents` (private storage)

## Design tokens (Modernist, from `_ds/.../styles.css`)
- Ground `--color-bg` #f3f2f2 · surface #eae9e9 · text #201e1d · accent #ec3013 · divider = text at 40% alpha.
- Neutral ramp 100–900: #f8f4f4 #eae7e7 #d7d3d3 #bab6b6 #9b9797 #7d7979 #605d5d #444141 #2d2b2b.
- Accent ramp 100–900: #fff2ef #ffe0d9 #ffc4b8 #ff9783 #ff563c #dd2b0f #ae1800 #7c1405 #4d170e. Use accent-700 for small red text, since the base accent is for large type and UI chrome only.
- Font: Archivo. Headings are weight 800, body 400/600/700. Sizes used: 80, 56, 48, 44, 40, 36, 32, 28, 26, 24, 20, 19, 18, 17, 16, 15, 14, 13, 12. Use tabular numbers for prices and ids.
- Spacing: 4, 8, 12, 16, 24, 32 (plus 40/48/56/72/88 for section padding).
- Radius: 0 everywhere.
- Shadows: sm `0 1px 2px #2d2b2b24`, md `0 3px 10px #2d2b2b29`, lg `0 12px 32px #2d2b2b38`.
- Component classes worth porting: `.btn` (primary/secondary/ghost/icon/block), `.tag` (accent/neutral/outline), `.field`/`.input`, `.seg`, `.card`, `.nav`, `.table`, `.hr`, `.grayscale`.

## Assets
- Icons: Lucide (search, lock, upload, arrow-right, menu, check).
- Photos: none are supplied yet. Replace the striped boxes with real equipment photos and always render them in grayscale.

## Files
- `Graye Market.dc.html`: all screens (open it in a browser).
- `_ds/modernist-…/styles.css`: the token sheet and component CSS. It's the source of truth for tokens.
- `_ds/modernist-…/_ds_bundle.js`: the design-system runtime the HTML needs to render.
- `BRIEF.md`: the original product brief.
