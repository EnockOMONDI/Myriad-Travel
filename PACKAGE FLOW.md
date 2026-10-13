# Myriad Package and Destination Flow

## Purpose

Improve the way Myriad packages, collections, destinations, regions, deals, and client feedback are managed and discovered. The work must preserve the existing Supabase data and use the records already in the database as the source of truth.

## Current production facts

- Supabase contains 57 destinations.
- Supabase contains 68 published packages.
- Supabase currently contains no `TravelCollection` records.
- `Package.region` is a single collection value today.
- `Package.categories` already supports multiple categories.
- `Destination` already has parent, region, destination type, image, active, and navigation fields.
- Private trip feedback already exists as a client-facing token link and an admin record.
- Current data must be routed and corrected carefully; no existing package, destination, category, or collection data may be deleted.

## Product rules

### Geographic hierarchy

```text
Region
  Country
    Destination
      Optional child destination
```

The public hierarchy is geographic. A destination's region and parent country must be derived from its stored records, not guessed from a package title.

### Package classification

Geography and marketing classification remain separate:

- A package has one main destination.
- A package may belong to multiple existing collections.
- A package may have one primary category and multiple additional categories.
- A package may appear as a deal when it has an active campaign.
- A package may appear in the general package listing as well as destination, country, region, collection, category, and campaign pages.

Existing collection and category records remain in place. Do not invent or bulk-create destination, country, category, or collection content during this implementation.

## Public routes

1. `/explore-the-world/` shows up to six existing region cards.
2. `/explore-the-world/<region>/` shows the region, country filters, destination cards, collection/category filters, packages, and useful empty states.
3. `/destinations/<country>/` shows the country overview, child destinations, filters, and packages assigned to the country or descendants.
4. `/destinations/<destination>/` shows breadcrumbs, the destination, related children, descendant packages, filters, and a quote action.
5. `/deals/` shows active campaign packages with campaign labels and closing-soon states.
6. Existing route names remain compatible and links are generated with Django `reverse()`.

## Homepage region cards

Each card must show:

- Region name
- Short description
- Existing suitable image, where available
- Count of active destinations with published packages
- Count of published packages
- Explore-region link

Until a dedicated editable region-content model is approved, region labels and descriptions must be derived from the current destination records and existing site copy. Do not create fictional counts or destinations.

## Admin experience

### Destination admin

- Make region, destination type, and parent easy to select.
- Add clear helper text, for example:
  - `Region: Africa, Europe, Asia, Middle East, Indian Ocean Islands, or Americas.`
  - `Country: Kenya, Tanzania, Rwanda, South Africa, or another existing country record.`
  - `Destination: Maasai Mara, Diani, Mombasa, or another existing destination record.`
  - `Optional child destination: use only for a more specific place inside this destination.`
- Show a readable hierarchy preview.
- Show published package count and children count.
- Add filters for missing region, missing parent, destination type, active state, and package availability.
- Preserve the six-card homepage limit without changing existing featured data unexpectedly.

### Package admin

- Replace the confusing single collection selector with a clear multi-select for existing collections.
- Keep primary category and additional categories distinct.
- Add helper text explaining that a package can belong to more than one collection.
- Group fields into Content, Location, Collections and Categories, Pricing, Media, Publishing, and SEO.
- Show the package's public destination, country, region, collection, category, and deal links after saving.
- Add warnings for missing destination, missing collection/category, missing image, and published package without a usable public route.
- Provide list filters for collection, category, region, destination, active campaign, deal status, image status, and publication status.

### Campaign/deal admin

- Make campaign start/end dates easy to edit.
- Add campaign type/label support using existing campaign records and labels where possible.
- Surface statuses: `New`, `Active`, `Closing soon`, `Expired`, and `Scheduled`.
- Allow a package to be promoted as a deal without duplicating the package.
- Keep at least 10 deal slots available on the public deals page when the database contains enough active or scheduled campaigns; do not manufacture deals.
- Support seasonal campaign labels such as Madaraka, Christmas, Valentines, staycations, weekend getaways, and monthly deals through campaign data rather than hardcoded package copies.

### Feedback admin

- Add a clear `Copy private feedback link` action to the feedback admin list and change page.
- Keep the existing token-based private form.
- Show client name, package, destination, status, rating, permission, visibility, and link status in the list.
- Make the private link easy to copy and open in a new tab.
- Keep publication approval separate from client submission.

## Data handling and migration

1. Audit current Supabase destination hierarchy and package assignments.
2. Keep all existing records and IDs.
3. Route existing packages using stored `main_destination`, parent, region, collection, and category data.
4. Correct only demonstrable mismatches, such as a package assigned to the wrong geographic parent or collection.
5. Do not infer new destinations from package names without an explicit existing destination match.
6. Keep a report of every data correction made.
7. Verify package counts before and after changes.
8. Add future enrichment as a separate follow-up: region descriptions, region images, stronger country records, richer child destinations, and plug-and-go admin defaults.

## Implementation sequence

1. Add this plan and create the feature branch.
2. Add reusable hierarchy and descendant-package query helpers.
3. Add region, country, and destination public views and named URLs.
4. Update homepage cards to regions and calculate counts from published Supabase-backed records.
5. Update destination detail pages to include descendants and inherited packages.
6. Add country and region filters that preserve shareable query strings.
7. Improve package collection handling without deleting current collection/category records.
8. Improve admin forms, fieldsets, filters, list displays, helpers, warnings, and public-link previews.
9. Improve campaign/deal statuses and seasonal campaign presentation.
10. Add admin copy-link feedback action.
11. Run read-only Supabase audits and apply only approved routing corrections.
12. Run focused model, view, admin, route, and template tests.
13. Run production-settings checks and verify the public route matrix locally against the Supabase-backed configuration.
14. Review the diff, document remaining data enrichment, and push the branch.

## Required verification

### Data and hierarchy

- Every active destination with a published package has a region or is explicitly reported as incomplete.
- A country page includes packages assigned directly to the country and all active descendants.
- A destination page includes packages assigned to itself and descendants, without duplicates.
- A region page includes only destinations belonging to that region.
- Existing packages remain present after migrations.
- Existing package IDs and destination IDs are unchanged.

### Filters and links

- Region cards resolve through named URLs.
- Country pills filter only the selected country.
- Collection and category filters can be combined without losing the destination/region context.
- Package cards link to the correct package detail page.
- Breadcrumbs point to valid region, country, and destination pages.
- Empty states appear when a valid filter has no published packages.

### Admin workflows

- Destination creation/editing has readable helpers and parent validation.
- Package creation/editing supports multiple existing collections and categories.
- Published packages show a clear warning when destination data is incomplete.
- Campaigns display New, Active, Closing soon, Scheduled, or Expired correctly from dates.
- Deals page does not show expired campaigns.
- Feedback admin can copy a private link and the copied link opens the correct token form.
- Feedback submission does not automatically publish a review.

### Regression checks

- Existing homepage, package detail, destinations, explore Kenya, explore World, themed packages, deals, and feedback routes return successfully.
- Existing admin package, destination, campaign, and feedback pages return successfully.
- Existing Supabase-backed records are readable after migrations.
- Mobile layouts do not hide region cards, filter controls, package links, or admin actions.
- No local SQLite file, secrets, or unrelated generated files are committed.

## Deferred enrichment

After this implementation is stable, enrich the admin with curated region records, region images, reusable helper presets, destination descriptions, country summaries, package templates, and better onboarding defaults so future admins can manage the site with minimal technical knowledge.

## Branch implementation status

Implemented on `feature/region-package-flow-admin`:

- Homepage region cards built from the existing destination/package data.
- Region routes, country filters, destination breadcrumbs, child links, and inherited package queries.
- Existing collection relationship exposed as an admin multi-select without deleting or replacing current data.
- Package cards can show existing collection labels when assigned.
- Campaign status labels for New, Active, Closing soon, Scheduled, and Expired.
- Deals page includes active and scheduled non-expired campaigns and supports up to ten visible offer links.
- Admin copy button for private trip feedback links.
- Destination and package admin helper text, public-link previews, and parent-cycle validation.
- Focused tests for hierarchy, inherited packages, region counts, collections, and campaign states.

Still requiring a production-data review before any Supabase write:

- Decide which existing destination records need parent/type/region correction.
- Decide which existing packages should receive multiple `TravelCollection` assignments; production currently has no `TravelCollection` rows.
- Enrich region imagery/descriptions and add seasonal campaigns only from approved Myriad offers.
