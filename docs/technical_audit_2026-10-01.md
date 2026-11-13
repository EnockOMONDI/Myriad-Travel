# Myriad Travel: Technical and Workflow Audit

Date: 1 October 2026. Repository: `/Users/djsean/Desktop/APPS2026/MYRIAD_TRAVEL_MAIN`.
Branch: `client-presentation-polish`. Audited commit: `933de55` (`Polish collection and destination pages`).

## Executive Assessment

The application has a working catalog and enquiry foundation, but it is not consistently production-ready. The most urgent confirmed problems are public exposure of customer information, insufficient dashboard authorization, discarded contact-form submissions, inconsistent checkout behavior, and credential-handling risks. Several polished interfaces imply capabilities that the backend does not provide.

This was an investigation, not a repair. Application source, environment files, production data, and deployment configuration were not changed. This report is the only intentionally created repository artifact. Nothing was committed, pushed, or deployed.

The existing business direction is an enquiry-led travel website with offline confirmation and no online payments. Do not introduce payment collection, automatic booking confirmation, refund rules, capacity promises, or customer account requirements as assumptions.

### Evidence and Limits

- Inspected first-party settings, routes, models, views, forms, admin configuration, context processors, email services, JavaScript, templates, migrations, management commands, and deployment entry points.
- Compiled all 111 first-party HTML templates and scanned their form, link, inheritance, unsafe-rendering, placeholder, and script patterns. Compilation is not proof that every variable or button works.
- Exercised anonymous, authenticated, and staff requests using disposable in-memory SQLite data. External HTTP and socket connection helpers were blocked during workflow checks. No real emails were sent.
- Ran 59 explicitly selected existing tests: 53 passed and 6 failed. Normal app-level discovery initially failed because `adminside/tests.py` and `adminside/tests/` conflict.
- Applied the actual migrations to a fresh in-memory SQLite database successfully. Migration graph conflicts: none. Model-to-migration drift: none.
- Rendered 28 registered admin change lists successfully and a populated package change page successfully. This does not certify Uploadcare uploads or production admin behavior.
- Read only aggregate counts from the already-tracked development SQLite file, opened in read-only mode. No customer names, addresses, password hashes, or credential values are reproduced here.
- Did not connect to production Supabase, inspect production credentials, send live enquiries, upload files, or inspect Render/Resend dashboards. Prior statements about 68 published packages are historical context, not a fresh database verification.
- Did not perform a desktop/mobile browser rendering audit, accessibility certification, load test, provider deliverability test, dependency vulnerability scan, or full Git-history secret scan. Findings below distinguish source evidence from runtime reproduction.
- `render.yaml` was not treated as the deployed source of truth, consistent with the earlier instruction to ignore it. Actual Render service settings remain an external verification item.

## Architecture

| Component | Actual Responsibility | Dependencies / Caveats |
| --- | --- | --- |
| `tours_travels` | Settings, URL root, middleware, global context, error handlers, health endpoints | Environment-dependent settings imports; Django sessions/auth/CSRF; WhiteNoise; Uploadcare; CKEditor; external HTTP email |
| `adminside` | Catalog: packages, destinations, categories, itineraries, accommodations, transport, galleries, hero slides | Despite its name, `/adminside/` exposes public catalog pages and JSON endpoints; it is not the staff admin |
| `users` | Public site, quotes, service enquiries, registration/profile, checkout, feedback, careers, newsletter, follow-ups | Mix of newer enquiry flow and older booking/cart/account flow; most orchestration stays in views |
| `blog` | Published articles, categories, search, RSS, sitemap, hidden comment submission backend | Cached lists; view counts write on GET; comment UI absent |
| `owner_dashboard` | Staff operational summaries and links to ModelAdmin | Reads shared models; ignores per-model permissions in its context service |
| `status` | Operational statistics and infrastructure checks | Public route exposes recent users/bookings; SMTP check does not represent Resend |
| Django `/admin/` | CRUD, inline gallery and itinerary editing, status/visibility actions | Unfold installed, but first-party admins inherit Django's base ModelAdmin rather than Unfold's ModelAdmin |

Runtime dependencies include Django, PostgreSQL driver/dj-database-url, Uploadcare, CKEditor 5, Unfold, taggit, crispy forms, requests/Mailtrap SDK, WhiteNoise, Gunicorn, optional Sentry, CORS middleware, and externally loaded Tailwind/Lucide/fonts. DRF and Google API packages are present in requirements, but no corresponding first-party REST or Google workflow was established. Installed dependencies alone do not establish a business capability.

### Settings and Deployment

`manage.py` and `tours_travels/wsgi.py` default to base settings. Base settings load dotenv and select development/production overrides through `DJANGO_ENV`. Production sets PostgreSQL SSL, secure cookies, HTTPS redirect, HSTS, database cache, and environment-provided integrations. Local settings select `myriad_local.sqlite3`; development settings select a different SQLite database. Test settings use memory SQLite and normally disable migrations.

`build.sh` installs requirements, collects static files, applies production migrations, and creates the cache table. Therefore a deployment running this build script can migrate the database selected by its production environment. This audit did not run that script.

`Procfile` still declares a `qcluster` worker although Django-Q is absent. The separate root `wsgi.py` uses the obsolete `DjangoWhiteNoise` wrapper and references `application` without creating it. The package WSGI module is the coherent entry point; confirm the actual Render command before changing deployment files.

### Data and Media

- Production database: configured PostgreSQL/Supabase; deployment state unverified in this audit.
- Package, destination, accommodation, blog, hero, and gallery image fields store Uploadcare references; image binaries normally live at the provider, not in PostgreSQL.
- Job resumes, job images, and CKEditor uploads use local filesystem media. Production URL configuration serves media only when DEBUG is true; no production private-file endpoint or durable storage integration was established.
- Static brand assets live under `static/`; public templates also reference Unsplash and third-party scripts/fonts.
- There is no NotificationOutbox, verified provider-event ledger, notification worker, or implemented follow-up reminder scheduler.
- There is no implemented online payment system. Booking amounts and a legacy `paid` flag are not payment evidence.

## Feature Flow Map

Notation: P = public; U = authenticated user; S = active staff; M = Django model permissions. Templates below are under `users/templates/` unless otherwise stated. Empty/invalid/missing behavior is included because a 200 response alone does not prove completion.

| Feature / Intent | URL -> View -> Form -> Records | UI / JS / Email / Side Effects | Completion, Failure, Empty State, Access |
| --- | --- | --- | --- |
| Homepage selling showcase | `/` -> `users.views.home` + `_public_page_context` -> Package/Destination/TripFeedback | `users/pages/home.html` and components; main.js filters four ranked packages | P; 4 packages sorted by home_rank; empty grid exists; fallback repeats failing DB dependency; hero/guides still static |
| All packages | `/packages/`, `/holidays/` -> packages/holidays -> published Package | `users/pages/packages.html`, shared cards; client filters | P; no purchase or record write; empty state exists; listing/filter scalability limited |
| Collections | `/explore-kenya/`, `/explore-the-world/`, `/tours-safaris/`, `/signature-experiences/` -> corresponding views -> categories/regions/packages | collection/signature templates; category pills; shared cards | P; DB catalog, but hard-coded membership rules; Signature pills scroll rather than filter |
| Destination pages | `/destinations/`, `/destinations/<slug>/` -> destinations/destination_detail -> Destination/Package | destination templates; pills; no email/write | P; missing/inactive slug 404; only primary-destination packages shown; descendants and itinerary stops omitted |
| Package details | `/packages/<slug>/` -> package_detail -> published Package/Itinerary/Day | generic or Chalbi template; quote POST; WhatsApp link | P; missing/draft 404; DB images supported; generic and Chalbi commercial behavior differs |
| Past-trip galleries | `/packages/<slug>/gallery/` -> package_gallery -> visible PackageGalleryImage | gallery template; admin inline supplies photos | P; empty state exists; button currently Chalbi-only, route supports all published packages; actual upload untested |
| General/package quote | `/quote/?package_id=...` -> quote_request_view -> QuoteRequestForm -> QuoteRequest | detail/modal/quote_form -> synchronous customer+admin email -> quote_success | P; valid records persist even if mail fails; invalid form redisplays; malformed ID 500; no idempotency |
| Chalbi quote | detail controls -> hidden pax/notes -> same quote endpoint | inline JS captures adults/children/room choice in notes; emails receive saved notes | P; quote, not Booking; dates/single rate hard-coded; JS-off extra notes lost; supplier terms need confirmation |
| WhatsApp enquiry | detail/card link -> external wa.me | JS pre-fills text on Chalbi; generic detail sends package title | P; leaving site does not save a DB lead or send an email; actual send cannot be inferred from a click |
| Contact submission | `/contact/`, `/contactus/` -> contactus | contact template has POST form; no form object, model write, email or redirect | P; POST returns unchanged page; incomplete and silently discards the request |
| MICE/student/NGO | `/mice/`, `/student-travel/`, `/ngo-travel/` -> `_service_inquiry` -> respective ModelForm -> respective Inquiry | form.as_p renders errors; DB save -> escaped email tables -> redirect | P; save survives mail failure with honest warning; no persistent notification retry/status workflow |
| About/services/corporate | `/aboutus/`, `/services/`, `/corporate/` -> render views | static content and service links; quote modal for requests | P; informational pages work; actual operational claims require business evidence |
| Registration/activation | `/register/` -> UserRegisterForm -> inactive User + profile signals -> verification_mail -> `/success/`; `/activate/<uid>/<token>` -> activation | register/success templates; synchronous email | P; ignores mail boolean; no resend flow; hard-coded HTTP link; token not explicitly invalidated by activation |
| Login/logout/password | `/login/`, `/logout/` Django auth; `/profile/change-password/` -> PasswordChangeForm | login/change_password templates | Login P, change password U; logout GET correctly 405; public password-reset routes missing |
| Profile/history | `/profile/`, `/profile/edit/`, `/profile/bookings/`, `/profile/booking/<reference>/` | User/Profile/Booking; own-record lookup on private booking detail | U; edit lacks ModelForm validation/atomicity; display says spend although amounts are bookings, not receipts |
| Saved ideas | `/profile/bucket-list/`, add/remove endpoints -> BucketList | list renders; no useful add/remove UI found in active public templates | U; removal ownership checked but accepts GET; invalid type can save empty relation; duplicates partly constrained |
| Legacy booking | `/bookings/<id>/` -> UserBookingsForm -> UserBookings -> admin email -> `/booking_success/<id>/` | UserBookingsForm/booking_success templates | Creation U; success P with no owner check; special_requests omitted from explicit save; draft packages not blocked |
| Cart / customization | `/book/<id>/`, `/checkout/customize/<id>/`, cart endpoints -> Cart + session | add_to_cart/customize templates; options selected by POST | P guest; quantities parsed with int rather than form; add-on IDs not scoped; GET can mutate session/cart |
| Checkout details | `/checkout/details/` -> CheckoutForm -> session and FormDataManager | details template | P; no cart redirects; form errors rendered; consent collected but not fully persisted into resulting records |
| Checkout confirmation | `/checkout/summary/` -> create_booking_from_cart -> User?/Booking/M2M -> email -> `/booking/confirmation/<reference>/` | summary/confirmation templates | P; first cart item only; no atomic boundary/idempotency; duplicate customer email; pending record shown as confirmed |
| Trip feedback | private UUID URL -> TripFeedbackForm -> existing TripFeedback | trip_feedback template -> redirect same token; admin visibility moderation | P bearer token; absent token 404; repeat edits possible after review/archive; no automatic invite email |
| Blog | `/blog/`, category/search/detail/PID redirects -> Post/Category/tags | blog templates; RSS/sitemap endpoints | P; only published detail; session-deduplicated view count; empty lists supported; comments backend not exposed in template |
| Blog comments | POST article -> manual fields -> inactive Comment | no active comment form/list on current detail | P; no ModelForm email/length validation; moderated default is good; UI feature incomplete |
| Careers | `/careers/`, `/careers/job/<slug>/` -> JobApplicationForm -> JobApplication/file | careers/job templates; notification emails | P; closed detail page exists; POST not bound to actual job/deadline; files local; incomplete |
| Newsletter | `/newsletter/subscribe/` -> simple form -> NewsletterSubscription -> email | no current footer subscription form found; JSON or referrer redirect | P; no confirmation/unsubscribe URL; false confirmation instruction; no-referrer fallback fails |
| Owner operations | `/admin-dashboard/` -> build_dashboard_context -> shared models | owner_dashboard/dashboard.html; admin workflow links | S only; no per-model scope; manual follow-ups; metrics are queries, not hard-coded numbers |
| Record CRUD | `/admin/` -> registered ModelAdmin | 28 registered model lists; forms/inlines/actions | M; lists/package edit render locally; role setup and external uploads unverified |
| Status/docs/diagnostics | `/system-status/`, `/docs/`, `/metrics/`, `/health/*`, `/version/` | counts, recent records, health checks | P; private data/internal metadata exposed; detailed health DB check broken |
| Legacy public catalog/API | `/adminside/...`, `/adminside/ajax/...`, `/destination/<id>/`, `/search/` | alternate views/templates/JSON; no email | P by implementation, not staff tools; duplicated routes; malformed filters and missing object handling inconsistent |

## Findings Register

Priority definitions: P0 = serious security/data exposure; P1 = broken core workflow or major incomplete feature; P2 = important correctness, maintainability, or UX issue; P3 = minor cleanup. B = REQUIRES REAL BUSINESS INPUT. Each issue includes current/expected behavior, cause, impact, recommendation, dependencies, and whether clarification is needed.

### Security and Privacy

**S01 - P0: Public system-status page exposes customer information.**

- Location: `status/views.py:16`, `:123`; `status/templates/status/dashboard.html:572`; `tours_travels/urls.py`.
- Current: anonymous GET renders recent usernames/emails and booking customer names/status/value. Reproduced with synthetic data. Expected: internal operational data visible only to authorized staff.
- Cause/impact: no authentication or permission decorator; customer privacy exposure.
- Fix/dependencies: gate status with explicit monitoring/owner permission and minimize data. Review public `/docs/`, `/metrics/`, detailed health and version output too. Safe to restrict public exposure without new business rules; exact internal audience needs role input.

**S02 - P1: Legacy booking success has an object-level authorization gap.**

- Location: `users/views.py:1064`; `users/templates/users/booking_success.html`.
- Current: anonymous sequential-ID URL reveals a customer's full name. Reproduced. Modern confirmation also accepts a reference without session/ownership checks, but its current template displays the reference rather than full customer details.
- Expected: private record access requires ownership or a scoped, unguessable guest access token. Cause: unrestricted get_object_or_404.
- Fix/dependencies: owner filter for legacy; signed guest access for modern flow, coordinated with email URLs. Safe for legacy; guest token lifetime/recovery requires a decision.

**S03 - P1: Owner dashboard bypasses model-level permissions.**

- Location: `owner_dashboard/views.py:8`; `owner_dashboard/services.py:25`.
- Current: staff with zero model permissions see customer names and broad operations data; reproduced. The service accepts `user` but does not use it.
- Expected: dashboard datasets and actions respect the same permissions as admin. Impact: content-only staff can see sales/HR information.
- Fix/dependencies: permission-filter each dataset/action or explicitly restrict owner dashboard to owners. Immediate restriction safe; final sales/content/operations/HR role matrix is B.

**S04 - P0 if credentials remain valid: Unsafe credential defaults and log output.**

- Location: `tours_travels/settings.py:197` (literal Uploadcare secret); `settings_prod.py:18` (prints beginning of database URL); `users/management/commands/createsu.py` (fixed fallback superuser password).
- Current: credential-like material exists in source and DB URL logging may include credentials. Validity was not tested. Expected: secret values only in deployment configuration and never logs.
- Fix/dependencies: remove literals/logging, require explicit credentials, review repository history/log access and rotate affected credentials if active. Code changes safe; rotation requires coordinated deployment access. Do not rewrite Git history or delete logs automatically.
- Important distinction: tracked `.env.secrets` has blank secret/database values in this checkout; its filename alone is not evidence of a leaked key. Do not claim otherwise.

**S05 - P1: A development database is tracked.**

- Location: `mbugani_development.sqlite3`, `.gitignore`.
- Current read-only counts: 1 auth user, 1 profile, 8 quote requests, 10 packages, 3 posts, 0 modern bookings. Whether these are real customer records was not established.
- Expected: database snapshots with account or enquiry data excluded from source control. Cause: ignore rules cover different SQLite names; `.env.secrets` also remains tracked.
- Fix/dependencies: preserve a private backup, classify data, stop tracking databases and broaden appropriate ignore rules. Removing from history needs explicit coordinated approval; do not delete working data. Treat potential account-hash exposure seriously without printing hashes.

**S06 - P1: Public input is trusted as HTML in quote emails.**

- Location: `users/forms.py:211`; email `quote_request_admin.html:62`, `quote_request_confirmation.html:41`; `users/views.py:1037`.
- Current: submitted `<b>...</b>` survives into quote email HTML; reproduced. Legacy booking email interpolates names/phones directly. No first-party bleach/sanitization use found despite dependency.
- Expected: public text escaped; intentionally rich content sanitized with an approved allowlist. Impact: deceptive email HTML/content injection. Script execution in a particular email client was not tested or asserted.
- Fix/dependencies: escape public text, use templates instead of interpolated HTML, define sanitization at rich-content boundaries. Safe; retaining specific rich-text features needs editor requirements.

**S07 - P2: Mutations and errors lack consistent protection.**

- Location: `users/views.py:1327`, `checkout_views.py:290`, `users/views.py:1321`, `:934`; health endpoints.
- Current: bucket removal and cart removal work via GET; some exception text reaches users. No application throttling found on registration, quotes, comments, newsletter, careers or report endpoint.
- Expected: POST+CSRF for mutations, safe errors, bounded anonymous submissions. CSRF middleware and tokens in scanned POST forms are present; this is not a blanket missing-CSRF finding.
- Fix/dependencies: method decorators, generic responses with private logs, appropriate abuse controls. Safe mechanical fixes; rate thresholds require operational judgment.

### Core Enquiry, Booking and Account Workflows

**W01 - P1: Contact form discards submissions.**

- Location: `users/views.py:411`; `users/templates/users/pages/contact.html:125`.
- Current: POST returns 200 with unchanged form, no save, notification or success state; reproduced. Expected: validated, persisted enquiry with accurate outcome.
- Cause: render-only view paired with submit form. Impact: silent lost leads.
- Fix/dependencies: choose a contact record or deliberately extend QuoteRequest to support a general message without invented trip dates. Wiring is required; record mapping needs a small business decision. Do not fabricate required quote fields to force a save.

**W02 - P1: Checkout accepts invalid quantities and unrelated add-ons.**

- Location: `users/checkout_views.py:28`, `:66`, `:308`; `users/cart.py:139`; unused `TravelerDetailsForm`.
- Current: non-numeric adults POST produces 500; zero/negative/out-of-policy quantities are not validated by the existing form. Submitted add-on IDs are retrieved globally, not through the package's allowed active options. Cart reads do not recheck publication.
- Expected: validate counts and selected objects before modifying cart or creating records. Impact: invalid enquiries/prices and unwanted options.
- Fix/dependencies: use validated forms, scope choices, revalidate at final submission. Safe; actual age, occupancy and maximum-group rules must be approved.

**W03 - P1: Multiple inconsistent pricing implementations.**

- Location: `users/cart.py:139`, `:180`; `checkout_views.py:347`; `users/models.py:342`; `_package_presenter`.
- Current: cart/checkout use 70% adult price for children, ignoring Package.child_price. A synthetic 58,000 adult / 43,500 child package produces 98,600 for one of each instead of the stored-rate 101,500. Accommodation is multiplied by duration_days, not nights. Self-drive excludes transport in summary but creation adds it again.
- Expected: one server-side calculation with explicit package/add-on rules. Impact: quote/record discrepancies.
- Fix/dependencies: one pricing service and snapshot at submission. Self-drive inconsistency safely fixable; child ages, optional versus inclusive accommodation/transport, and occupancy pricing are B. No online payment should be introduced.

**W04 - P1: Multi-item summary only saves one package; partial writes can survive failure.**

- Location: `checkout_views.py:217`, `:347` (`cart_items[0]`).
- Current: summary lists/sums every cart package; booking creation uses first, then entire cart cleared. User creation, booking, M2M writes and emails lack one transaction/idempotency contract.
- Expected: every accepted item preserved, or UI/server deliberately limited to one; retried submit must not duplicate bookings.
- Fix/dependencies: settle single versus multiple package requests; transaction, idempotency key and post-commit notification queue. Safe integrity protections; cart scope is B.

**W05 - P1: Guest checkout silently creates accounts and associates by unverified email.**

- Location: `checkout_views.py:375` onward; `users/templates/users/emails/welcome.html`.
- Current: latest User matching typed email selected; otherwise account created with generated password sent by email. Request authentication is not the ownership source.
- Expected: guest flow works without automatic password account; verified identity needed to claim records. Impact: unwanted accounts, misleading ownership, insecure password handling.
- Fix/dependencies: guest booking with nullable owner; attach only authenticated/verified identity; invitation/magic-link path only if requested. Existing requirement already favors guest/passwordless, so removing automatic password creation is supported; recovery/claim policy still needs specification.

**W06 - P1: UI falsely confirms a pending booking.**

- Location: `users/models.py:211`; checkout confirmation template; `users/templates/users/emails/admin_notification.html`.
- Current: new Booking defaults pending, while page says Booking Confirmed and admin email says booked. Expected: booking request received until staff confirms availability.
- Cause/impact: copy not tied to real status; misleading commercial commitment.
- Fix/dependencies: status-driven copy and a defined staff confirmation transition. Correcting pending copy is safe; actual confirmation prerequisites are B.

**W07 - P2: Generic package enquiry loses group details and can reject long package names.**

- Location: `users/templates/users/pages/package_detail.html:338`; `users/forms.py:211`; `users/models.py:794`.
- Current: hidden traveler count always 1; WhatsApp does not capture group/date/notes. Hidden destination concatenates title and place but QuoteRequest.destination allows 100 characters. A 101-character value is rejected even though no destination field is visible on package page.
- Expected: real group inputs and stable package reference; valid package names should not break enquiry.
- Fix/dependencies: shared detail enquiry form with package FK, deliberate destination label, structured adult/child/room fields where required. Safe to correct loss; field requirements follow established enquiry needs.

**W08 - P2: Bad IDs, search and fallback redirects fail inconsistently.**

- Location: `users/views.py:1388`, `:979`, `:941`, `:771`; legacy catalog filters.
- Current: `/quote/?package_id=abc` returns 500; newsletter endpoint without Referer returns 500 due nonexistent `users:home`; search reverses unnamespaced `users-destination`, catches all failures, redirects to unvalidated Referer; missing legacy destination uses `.get()` instead of 404.
- Expected: validation/404 or usable empty results, known local fallback. Fix: validate IDs, named URLs, allowed-host redirect checks, targeted exceptions. Safe; no business clarification required.

**W09 - P2: Legacy booking form omits entered notes and permits unpublished packages.**

- Location: `users/views.py:1000`; `users/forms.py:33`.
- Current: special_requests is a form field but omitted from explicit create; package lookup lacks published filter. Form includes `paid` although view does not save it, so this is misleading UI rather than a proven paid-flag exploit.
- Expected: preserve accepted fields, expose only appropriate public packages, remove customer payment-status control.
- Fix/dependencies: align form and save; decide whether to retain this route or redirect to canonical enquiry. Mechanical validation safe; retiring route requires usage review.

**W10 - P1: Profile edits can partially corrupt data.**

- Location: `users/views.py:1157`; `users/templates/users/edit_profile.html`.
- Current: invalid email is saved on User before invalid birth date raises 500; reproduced. Missing notification checkboxes in template are interpreted as false on every save.
- Expected: ModelForm validation and atomic user/profile update; preserve fields not exposed.
- Fix/dependencies: two bound forms, validated choices/email/date, atomic save, intentional preference controls. Safe. Passport/emergency-contact necessity and retention are B.

**W11 - P2: Saved-ideas backend is incomplete and accepts malformed records.**

- Location: `users/views.py:1277`; `users/models.py:489`; bucket-list template.
- Current: invalid item_type saves a success record with no related object; reproduced. Create then update can leave incomplete rows. Active UI lacks useful add/remove controls.
- Expected: exactly one valid published/active target, matching type; usable UI if retained.
- Fix/dependencies: validate before create, conditional constraints after data audit, POST removal and links. Validation safe; feature priority and existing-record remediation need review.

**W12 - P2: Feedback moderation can be bypassed by editing an already-visible submission.**

- Location: `users/views.py:1480`; `users/models.py:180`; public feedback queryset.
- Current: token holder can resubmit reviewed/archived feedback; visibility stays true; submitted status qualifies for public display. Reproduced: changed review stayed publicly eligible without new moderation.
- Expected: edits re-enter moderation or submitted feedback is locked; archived links should have defined behavior.
- Fix/dependencies: clear visibility/review metadata on edit or make form single-use. Re-review is safe privacy protection; editing period and expiry are B. No automatic invitation/reminder email exists.

**W13 - P2: Careers applications are not tied reliably to available jobs.**

- Location: `users/views.py:651`, `:731`; JobApplicationForm and JobListing.is_application_open.
- Current: job_id only pre-fills fixed position choices on GET; POST saves no job_listing relationship and does not enforce deadline/status. Generic applications are explicitly invited by current UI.
- Expected: distinguish open-job application from general interest; validate job availability and associate the right record.
- Fix/dependencies: bind/validate optional job, use is_application_open, preserve form/file errors. B: whether unsolicited applications and which roles are accepted.

### Email, Notifications and Follow-Ups

**E01 - P1: No durable delivery, retries, or provider analytics.**

- Location: `users/tasks.py`, inquiry_email, checkout_views, migrations/commands.
- Current: email sends synchronously; provider acceptance reduced to boolean; no persisted provider message ID, webhook, outbox, retry schedule or stale-processing recovery. No dashboard opens/deliveries/bounces metrics.
- Expected: saved business event and traceable notification delivery; provider acceptance is not delivery/open proof.
- Fix/dependencies: NotificationOutbox with deduplication, states, attempts, next retry and provider ID; queue after commit; worker/cron processor; signed webhook event handling if analytics needed. Retry mechanics safe; provider tracking consent/visibility and worker deployment need decisions.

**E02 - P1: Duplicate checkout confirmation and misleading mail-status behavior.**

- Location: `checkout_views.py:242`, `:465`, `:472`; `users/views.py:314`, `:771`.
- Current: customer confirmation called in creation and again in summary. Some wrappers swallow errors, so outer handlers do not observe failures. Registration/newsletter ignore false return and say check email. Checkout promises later delivery without retry infrastructure.
- Expected: one notification per event, truthful saved-versus-sent outcomes.
- Fix/dependencies: single service owner, typed result, idempotency, outbox; activation resend. Safe.

**E03 - P2: Central HTTP provider is not a Django email backend.**

- Location: `users/tasks.py:80`, settings email configuration, `status/views.py:194`.
- Current: most application send paths use the HTTP helper, but Django backend remains SMTP in base/production. Console/locmem backends do not intercept direct requests. Local settings don't make Resend the universal backend. Misspelled provider falls into Mailtrap branch. Status checks SMTP, not transactional provider.
- Expected: explicit provider validation, fail-safe local/test transport, coherent health signal and environment routing.
- Fix/dependencies: central backend/service abstraction used everywhere; no-network default in local/tests; validate required sender/admin values. Safe. Live mailbox values and domain verification require deployment verification, not guesses.

**E04 - P2: Email content/routing and persistence drift.**

- Location: `users/tasks.py:293`, `:413`; `checkout_views.py:480`; email templates.
- Current: job task writes `confirmation_email_sent`, but model has `applicant_confirmation_sent`; assigned attribute does not persist that status. Career recipients may duplicate when jobs/admin address equal. Alternate booking helper named confirmation sends to ADMIN_EMAIL. Checkout WhatsApp number differs from central company number. Resend payload lacks text fallback/reply-to.
- Expected: correct persisted flags, distinct recipients, common contact config, useful customer/admin trip detail. The quote email has 2-hour/24-hour language and next actions; not every other email does.
- Fix/dependencies: correct field, deduplicate routing, central contact settings, plain text/reply-to and consistent request details. Safe; SLA wording beyond established request and reply-to policy require confirmation.

**E05 - P1 if newsletter is offered: Confirmation and unsubscribe journeys do not exist.**

- Location: NewsletterSubscription methods; users URLs; newsletter_confirmation template; subscribe view.
- Current: subscriber prompted to confirm, but email contains no confirmation link and no corresponding routes exist. Unsubscribe token exists but no user endpoint. Inactive subscriber uniqueness can still conflict on re-subscribe.
- Expected: clear consent/confirmation and revocation paths, or do not present an operational marketing subscription.
- Fix/dependencies: define opt-in process, token routes and reactivation behavior before campaigns. No current public footer form found, so distinguish latent backend from active CTA. B: marketing ownership/consent policy.

**E06 - P2 / deferred feature: Follow-ups are manual tasks only.**

- Location: FollowUp model/admin, dashboard services, quote_request_admin email.
- Current: admin creates/assigns/updates tasks; dashboard lists overdue items. No scheduled 24h/2d/5d/10d/15d/30d notifications. Email instructions to create reminders do not implement them. Reopen action leaves completed_at; manual completed status does not use mark_completed; priority sort is alphabetical.
- Expected: honest manual-task labeling now; planned reminder schedule later.
- Fix/dependencies: normalize transitions and priority ordering; scheduler after outbox. Previously requested cadence is known. B: anchor event, stop conditions, business-hours handling, timezone and recipient/assignment escalation. Do not invent these.

## Model Integrity Review

| Models | Real Entity / Current Use | Integrity and CRUD Assessment |
| --- | --- | --- |
| PackageCategory | Catalog category; admin-managed; nav/collections | Unique slug and order useful. Hard-coded membership prevents arbitrary admin-added categories joining a collection. No Collection model. |
| Destination | Country/city/place hierarchy; admin + public catalog | clean validates hierarchy in forms, save does not call full_clean; direct ORM writes can bypass it. Duplicate get_all_children method. Parent CASCADE can delete an entire catalog branch. |
| Package | Published travel offer; admin + public enquiries | home_rank supports ordering. No structured departure dates, single rate, price-estimate flag, rate validity or source. Prices/counts/durations need semantic constraints; total_bookings/total_reviews not maintained by public flow. |
| Accommodation / TravelMode | Optional catalog services | Active flags and capacity fields exist; no real date inventory/allocation workflow. Discount can exceed sensible range without explicit validation. Do not describe these fields as live availability. |
| Itinerary / ItineraryDay | Package day plan | One-to-one itinerary and unique day number are good. No check matching duration, positive day, or destination/accommodation compatibility. |
| PackageGalleryImage | Visible past-trip image and metadata | Admin inline and public query wired; ordering useful. Actual provider upload/persistence untested. |
| HeroSlider | Admin hero content | CRUD exists; active homepage template uses static slides, so edits need not affect public hero. |
| PackageBooking | Older authenticated booking representation | Admin and package inline; not the model populated by modern checkout. Separate from UserBookings and Booking; no silent consolidation recommended. |
| UserBookings | Legacy authenticated request | Public create/admin edit; notes omitted in view; success ID leak; paid flag not financial ledger. Package/User CASCADE risks historical loss. |
| Booking | Current cart result | Public create/admin edit; nullable user supports guests but creation ignores that opportunity. Package CASCADE removes historical requests; stored amounts have no currency/source snapshot. |
| GuestBooking | Intended temporary guest cart | Imported by Cart but actual cart writes session dictionaries. No active creation/use established; model has another price formula. Do not delete without production inventory. |
| QuoteRequest | Main package/general sales lead | Form save/admin status; package SET_NULL preserves lead if catalog removed. Email flags only; no automatic conversion to Booking or follow-up. |
| MICEInquiry / StudentTravelInquiry / NGOTravelInquiry | Service leads | Forms save, admin CRUD, email service; no lifecycle/assignment/status fields beyond manual linked follow-up. Confirm desired processing states before adding them. |
| UserProfile | Customer details/preferences | Auto-created through two post_save receivers; edit manually assigns fields; privacy/retention and preference gaps described above. |
| BucketList | Saved customer ideas | Nullable polymorphic targets; uniqueness helps duplicate objects but no exactly-one/type constraint; malformed rows reproducible. |
| FollowUp | Assigned staff task | Nullable links let several or no source objects coexist. Generic task may legitimately have none; rules need definition. Useful indexes exist; transition history incomplete. |
| TripFeedback | Private invited review plus visibility approval | UUID and publish consent useful. No expiry/edit lock/re-review enforcement. Optional rating/text permits weak submissions. |
| JobListing / JobApplication | Vacancy and candidate record | Job FK SET_NULL retains applications; UI POST does not set it; resumes local; status/routing issue. |
| NewsletterSubscription | Marketing preference and token | Unique email and token; no public confirmation/unsubscribe; normalize address and lifecycle deliberately. |
| Blog Category / Post / Comment | Publishing and moderated responses | Draft visibility checks and comment inactive default good. Rich content sanitation missing; post slug race possible; comments bypass ModelForm. |
| Django User / Group / Permission / LogEntry | Authentication, access, admin audit | Django admin has baseline checks. Dashboard bypasses model scope; public email identity not unique/verified for booking linkage. |

**D01 - P1: Catalog deletion can cascade into historical bookings.**

- Location: `adminside/models.py:71`, `:362`; `users/models.py:189`, `:211`; PackageBooking.
- Expected: historical enquiries/bookings survive routine catalog retirement. Fix: use archive first, review PROTECT/SET_NULL and snapshots after actual data inventory. Dependencies: retention and reporting policy. B: never change deletion semantics or remove data blindly.

**D02 - P2: Commercial truth is not fully modeled.**

- Location: Package fields, CHALBI_SPECIAL_OFFER/CHALBI_DAY_META, multiple price calculations.
- Current: estimated seeded prices indistinguishable structurally from verified rates; dates/single occupancy live in code; status changes do not automatically set published_at.
- Expected: approved price basis, source, validity, departure and offer metadata editable in admin. Fix: add minimal explicit fields after agreeing semantics, migrate without fabricating values. B: supplier validation and display rules.

**D03 - P2: Useful constraints exist, but application invariants are missing.**

- Current: slug uniqueness, itinerary day uniqueness, several catalog/follow-up indexes exist. Missing cross-field validation lets direct ORM writes produce invalid relationships, counts or statuses. Many inquiry status/date query paths have no purpose-specific index.
- Fix: validate writes first; profile representative PostgreSQL queries before adding indexes; inspect existing bad rows before introducing constraints. Dependencies: real data inventory, agreed invariants. Do not add constraints based solely on assumptions.

## Content, Templates and Frontend/Backend Alignment

**C01 - P1: False fallback ratings and prices.**

- Location: `components/package_card.html:49`, `users/pages/package_detail.html:71`, `:92`; duplicate components.
- Current: Django default filter replaces legitimate zero rating with 5.0/4.9, zero review count with 45 on cards, zero price with 68,500 on detail. Expected: no reviews / request price rather than invented figures.
- Fix/dependencies: explicit presence/zero handling; display only substantiated ratings/prices. Safe to remove fabricated fallback values; actual ratings are B.

**C02 - P2/B: Trust claims and testimonials lack a confirmed source in this audit.**

- Location: testimonials_section, accreditation_bar, footer, aboutus, services_section, base social metadata.
- Current: static named testimonials appear if no approved DB feedback; fixed 5.0, 100% positive, authority/partner claims and 24/7 emergency/concierge copy. Existence of logos or text is not verification.
- Expected: approved evidence or neutral omission. Fix: request dated review source/permission, valid accreditation details and actual support hours. Preserve SafariBookings integration as requested; do not invent ratings or conclude existing testimonials are fake without evidence.

**C03 - P2: Admin-controlled content and public content diverge.**

- Location: `users/views.py:825`, hero_section, travel_guides_section, navigation_collections, collection views.
- Current: HeroSlider is queried but ignored by static homepage hero; homepage guides are static modal articles instead of Blog Post records. Admin edits can appear ineffective. Navigation category membership is hard-coded despite DB labels/order.
- Expected: approved content and campaign navigation controlled through supported admin records. Fix: wire existing records; add explicit collection membership only after taxonomy decision. Safe wiring, B for content selection.

**C04 - P2: Filter identifiers and navigation identifiers can disagree.**

- Location: `_collection_context`, collection/destination templates, navbar, signature_experiences template.
- Current: filters use slugify(category.name), navbar uses stored category.slug; renaming a label can break selection. Signature section IDs likewise use name slug rather than stored slug. Query filters depend on JS and do not update URL; Signature pills only anchors.
- Expected: stable category IDs/slugs and accessible shareable filtering. Fix: use stored slug throughout and define server-side query filtering with progressive JS enhancement. Safe.

**C05 - P2: Discovery is incomplete beyond the first showcase items.**

- Location: `_public_page_context`, destination_detail, navbar search link, `static/js/main.js:230`.
- Current: destination listing capped at 12; homepage filters only inspect four featured cards; destination page ignores descendant/itinerary places; navbar search links to missing `#search-interface`. Older hero search code only scrolls/filters and is not a real catalog search.
- Expected: showcase distinguished from all-catalog search; meaningful destination scope. Fix: wire search to actual filtered queryset, pagination, stable links. B for whether itinerary stops count as destination packages.

**C06 - P2: Customer-facing copy exposes implementation notes and unapproved promises.**

- Location: package_detail empty itinerary/highlights, collection/destination empty states, signature group notice, aboutus Admin Follow-Up section, featured_packages empty result.
- Current: public text tells staff to upload images/update admin; empty filter promises a custom itinerary in under 2 hours. Expected: useful customer-facing availability wording and approved response window.
- Fix: replace with simple factual empty states; keep staff guidance in admin. No invented company history/team/statistics. Existing requested response target is 2 hours where possible, up to 24 hours, not guaranteed completed itinerary in 2 hours.

**C07 - P2: Several backend features have no effective current UI.**

- Location: blog detail/template; profile/bucket-list templates; newsletter endpoint; legacy package modal.
- Current: comments/related-post/pagination context is partly unused; saved-idea actions not exposed; newsletter has no active footer form; old package modal contains a static itinerary/rating but current cards link to real detail and no active modal trigger was found.
- Expected: either a complete intentional user flow or clearly retired code. Fix/dependencies: first inventory runtime usage and product intent, then wire or archive. Do not call every unused function a customer bug or delete it automatically.

**C08 - P2: SEO data is prepared but not fully rendered.**

- Location: blog views, `users/templates/base.html`, blogdetail; Package.meta_title/meta_description.
- Current: blog computes canonical_url/meta_description but active base uses blocks with generic defaults and no corresponding canonical output; social image uses relative static URL; package SEO fields not consistently mapped.
- Expected: per-record metadata and canonical URLs; sitemap covers intended public catalog. Fix: connect existing context and template blocks, absolute share images, decide full-site sitemap scope. Safe technical wiring; wording B where absent.

**C09 - P3: Duplicate template trees and styling sources encourage drift.**

- Location: `users/templates/components/` and `users/templates/users/components/`, two bases, adminside public templates, main.css plus runtime Tailwind CDN.
- Current: active primary base includes `components/...`; duplicate files and legacy brand comments remain. CSS frameworks/classes in old status/catalog templates do not necessarily match the active base; browser verification pending. Lucide loads unpinned latest.
- Expected: one intentional inheritance/component system and reproducible asset build. Fix after workflows: map references, consolidate with render checks, pin/build dependencies. Safe only after usage audit; do not remove files based on name alone.

### Configuration, Reliability and Operations

**O01 - P1 for monitoring: Detailed health always fails its database check.**

- Location: `tours_travels/health_check.py:30`.
- Current: later `connection = get_connection()` assignment makes connection local, so earlier DB cursor raises UnboundLocalError. Reproduced. `/health/ready/` succeeds in same test.
- Expected: actual DB check, separate mail connection variable, safe public response. Fix is mechanical and safe. Basic `/health/` is only liveness, not database readiness.

**O02 - P1 for careers/editor uploads: Production media persistence/serving unresolved.**

- Location: JobApplication.resume, JobListing.job_image, settings CKEDITOR_5_FILE_STORAGE, root URLs.
- Current: local media storage with DEBUG-only serving; no durable/private serving configuration in inspected app. Uploadcare catalog images use a separate path and should not be conflated.
- Expected: durable private resumes, permission-checked download, persistent approved public images. Fix/dependencies: storage selection and Render infrastructure verification. B/external: retention/access policy, existing disk/bucket configuration. Do not claim Render currently loses files without checking actual service setup.

**O03 - P2: Deployment artifacts and settings can mislead operators.**

- Location: Procfile, root wsgi.py, settings import chain, settings_dev, build.sh.
- Current: obsolete worker, broken root entry, environment-dependent circular import pattern; ignored development settings create a fresh-clone reproducibility risk. Development context processors omit navigation_collections. Cache-table creation errors suppressed.
- Expected: explicit production entry/settings, reproducible local/test setup, observable build failures. Fix/dependencies: confirm actual Render configuration first, then remove obsolete configuration through reviewed changes. No deployment performed.

**O04 - P2: Security-looking settings are not necessarily active controls.**

- Location: production CSP settings/middleware list; requirements; HTTPS configuration.
- Current: CSP variables exist without CSP middleware in inspected configuration. No explicit SECURE_PROXY_SSL_HEADER found; actual upstream behavior not checked. Dependency ranges broad; lockfile absent.
- Expected: verify effective response headers and proxy handling, not only variable names. Fix: test headers in staging, configure a CSP compatible with required assets, pin dependencies/scan advisories. Do not weaken CSRF or HTTPS to bypass failures.

**O05 - P2: Destructive/demo commands remain operationally dangerous.**

- Location: `blog/management/commands/populate_luxury_blogs.py:38`; production-sync/sample itinerary/category/hero commands; migration 0007.
- Current: populate_luxury_blogs deletes every Post before seeding; createsu has unsafe defaults; historical hero migration seeds Mbugani content; sample/sync commands can introduce old business assumptions.
- Expected: explicit environment guards, dry runs and clear production restrictions. Fix safe guardrails; never run these against live data as a repair. Historical migrations applied successfully; do not casually rewrite applied history.

**O06 - P2: Query and error behavior degrade with catalog growth.**

- Location: `_itinerary_presenter` calls ordered relation queries; destination ancestor traversal; `_collection_context`; legacy category counts; homepage broad exception fallback.
- Current: full catalog presentation without pagination, repeated presentation/context queries, potential N+1 day/accommodation/ancestor lookups, duplicate homepage fetching. Broad catches hide root cause or show raw error text.
- Expected: measured query budgets and truthful safe failure. Fix: query-count tests, targeted select/prefetch, reuse prepared objects and pagination, remove duplicate work after regressions are covered. No load-performance claims made.

**O07 - P2: Existing tests do not establish production readiness.**

- Location: conflicting adminside test module/package, test_settings, existing test suites, test_production_comprehensive.py.
- Current: default discovery fails; 6 failures in explicit run. Test settings skip migrations. Production test script contains a real email send and was deliberately not run.
- Expected: deterministic isolated tests plus separate safe migration/provider smoke checks. Fix: resolve discovery, correct invalid fixtures and brand assertions, add boundary tests for confirmed findings. Never broadly run production-named scripts without checking their side effects.

## Email Routing Map

These are source-level destinations, not a confirmation of live Render values or DNS.

| Trigger | Recipient Source | Template / Result |
| --- | --- | --- |
| Quote | QuoteRequest.email + ADMIN_EMAIL | quote_request_confirmation/admin; both flags saved; synchronous |
| MICE/student/NGO | inquiry.email + ADMIN_EMAIL | service_inquiry_confirmation/admin; boolean result only |
| Legacy booking | ADMIN_EMAIL | interpolated HTML; caller ignores false |
| Modern checkout | Booking.email + ADMIN_EMAIL | booking_confirmation/admin_notification; duplicate customer send exists |
| New auto-created checkout account | User.email | welcome includes generated password; needs removal |
| Registration | User.email | verification_mail inline HTML; delivery boolean ignored |
| Job application | applicant email + JOBS_EMAIL + ADMIN_EMAIL | job templates; incorrect applicant flag assignment |
| Newsletter | subscription email + NEWSLETTER_EMAIL | newsletter templates; confirmation/unsubscribe not wired |
| Follow-up/feedback invite | None automatically | manual admin workflow only |
| Django framework/system mail | Django EMAIL_BACKEND | still SMTP configuration, separate from HTTP helper |

Base defaults route sender/admin/jobs/newsletter toward the info mailbox; local overrides have careers/marketing addresses; production os.getenv calls can produce None if unset. A getattr fallback does not replace an existing None value. Sender/admin/jobs/newsletter values need startup validation. User-submitted recipient addresses go through Forms in quote/service/career/newsletter flows; profile's raw email edit is an exception.

## Hard-Coded Value Decisions

| Value Family | Decision | Evidence / Boundary |
| --- | --- | --- |
| Brand name/logo; established Parklands address | Keep approved identity, centralize repetition in configuration | Address explicitly supplied by user; no reason to invent replacement |
| Business phones, WhatsApp, sender/reply-to/inboxes | Configuration with validated overrides | Current hard-coded checkout number conflicts with central contact |
| Price, dates, room/single rate, departure, campaign order | Database structured commercial fields | home_rank already works; Chalbi metadata still code-bound |
| KES/USD factor 130 | Explicit approved conversion policy/configuration, with estimate label | Do not silently present a fixed divisor as a live exchange rate |
| Ratings/counts/testimonials | Verified records/source or omit | Never use default numeric credibility claims |
| Category/collection/nav membership | Explicit DB relationships/order where needed | Current limited slug lists are not fully admin-managed |
| UI icons, labels, layout constants | Leave in code unless actual configurability needed | Not every literal is a defect |
| Permission/status identifiers | Keep typed model choices; enforce transitions | Do not turn access-control rules into arbitrary template text |
| Guidance, FAQs, service claims, accreditations | REQUIRES REAL BUSINESS INPUT | Existing text alone does not substantiate operational promises |
| Placeholders for missing images | Keep clear branded placeholders | User explicitly plans to upload real photos; do not substitute misleading destination photography |
| Historic sample commands/data | Quarantine/guard, classify before removal | Existing record legitimacy cannot be inferred from filenames |

## Verification Results

### Existing Tests

59 selected tests executed; 53 passed; 6 failed, all in admin interface tests:

1. test_admin_change_history: preceding edit payload is incomplete, so expected change entry absent.
2. test_admin_destination_add: place fixture omits required parent relationship.
3. test_admin_destination_edit: submitted hierarchy payload incomplete.
4. test_admin_login_success: asserts old Django administration wording instead of current branding.
5. test_admin_package_add: stale payload omits current required fields/inline management forms.
6. test_admin_permissions: expects standalone UserProfile admin although profile is handled inline on User.

These failures should be corrected, but they do not prove real browser admin saves are all broken. Package edit GET and all 28 registered admin lists passed local rendering. Actual upload success remains untested.

### Reproduced Behavioral Checks

| Check | Observed |
| --- | --- |
| Contact POST | 200; no quote created; view contains no persistence or notification |
| Malformed quote package ID | 500 |
| Invalid adults string on cart POST | 500 |
| Legacy booking success anonymously | 200; synthetic customer's name visible |
| Status dashboard anonymously | 200; synthetic private customer information visible |
| Owner dashboard staff without permissions | 200; synthetic customer visible |
| Valid quote with provider returning false | 302; saved and linked correctly; both email flags false |
| Quote special-request HTML | Raw submitted HTML rendered in email |
| Long hidden destination | Form rejects >100 characters |
| Invalid profile date and email | 500 after invalid email already saved |
| Invalid bucket-list type | 200 success and malformed row created |
| Feedback edit after review | Remains publicly eligible; status becomes submitted |
| Cart child rate | 98,600 instead of stored-rate 101,500 for test package |
| Package and Destination get_absolute_url | NoReverseMatch |
| Detailed health | 503; database check raises local-variable error |
| Newsletter GET without Referer | 500 |
| Root unknown URL | 404 |
| Custom 400/403/404/500 handler calls | Correct corresponding status codes |
| All first-party template compilation | 111 pass; no scanned POST form missing csrf_token |
| Real migration graph/fresh memory DB | No conflicts, no model drift; apply succeeds |

The route sweep also rendered home, catalog collections, destination index, about/contact/services/corporate, enquiry forms, register/login, careers, quote, blog lists/search/RSS/sitemap and legacy catalog lists with empty data. Populated generic detail, gallery and destination pages returned 200. This verifies basic server rendering, not client-side JS, photo loading, provider callbacks or business correctness.

### Additional URL Defect

Package, Destination and Accommodation `get_absolute_url()` reverse unnamespaced names absent from root URL configuration (`adminside/models.py:132`, `:246`, `:447`). Package/Destination failures reproduced. This can break Django admin View on site or any future model URL usage even though manually constructed public links work. Fix with canonical namespaced routes. This is safe and should precede further URL cleanup.

## Business Input Required

1. Confirm owner, sales, operations, content and HR access boundaries. Staff status alone must not imply all-data access.
2. Is the modern multi-step cart a supported journey, or should public requests consistently use enquiry forms? Existing no-online-payments requirement remains in force.
3. Confirm supplier-approved package rates, child age brackets, occupancy, included accommodation/transport, estimate labels, validity dates and currencies. Historical estimates must not become guarantees.
4. Confirm how contact messages are classified and who handles them; do not force nonexistent trip dates into a quote.
5. Verify accreditations, SafariBookings profile/rating source, testimonial reuse permission, office hours and emergency support scope. Retain SafariBookings as requested.
6. Confirm reminder anchor and stop rules for the already-requested 24 hours, 2, 5, 10, 15 and 30 days; assignment/escalation and business-hours behavior.
7. Confirm feedback editing/expiry policy, marketing opt-in/unsubscribe ownership, general careers applications and resume retention.
8. Confirm package collection membership and destination descendant/itinerary discovery behavior; whether seasonal Deals need a separate object remains deferred.
9. Supply approved privacy, terms and booking conditions. Current footer hash links are not policies. These require real business/legal content, not generated assumptions.
10. Confirm actual Render branch/start command/media persistence and live sender/admin configuration through an authorized deployment review. No environment values should be pasted into reports.

## Implementation Plan in Dependency Order

Each stage should be a small reviewable change set. This plan is not authorization to execute changes during the audit.

### 1. Contain Security and Privacy Exposure

Restrict status/docs/metrics and booking access; restrict owner dashboard until role-aware queries are in place. Remove literal secrets, credential logging and fallback admin passwords. Coordinate necessary rotations and database snapshot handling. Preserve data and history until an approved retention/remediation process exists.

Acceptance: anonymous and insufficiently privileged staff cannot access private records; normal authorized admin/public catalog still work; no credentials printed.

### 2. Repair Lost and Misleading Core Requests

Resolve contact record mapping, then implement validated save -> notification result -> redirect. Correct bad-ID handling, canonical URL reversals and safe redirects. Remove fabricated rating/price fallbacks; say request received for pending bookings. Preserve the working quote/service enquiry behavior.

Acceptance: every supported form persists exactly one valid record or shows actionable errors; no silent success; missing/unpublished objects handled deliberately.

### 3. Establish Data Integrity and Booking Scope

Choose one supported enquiry/cart contract. Correct quantity/add-on validation, child/self-drive calculations and multi-item behavior; consolidate pricing after supplier rules are approved. Use transactions and idempotency. Preserve legacy records; decide schema changes and historical deletion policy before migrations.

Acceptance: displayed summary equals persisted request, duplicates do not occur on retry, and invalid submissions cannot create partial records.

### 4. Complete Backend and Database Contracts

Add only justified structured offer fields, source/estimate metadata and collection membership. Add model validation/constraints after inspecting real data. Normalize follow-up state changes and feedback re-review; wire job relationships. Keep PostgreSQL migration rehearsal separate from local tests.

Acceptance: migrations are additive/reviewed; no fabricated backfills; admin can manage the agreed commercial data; existing home_rank ordering preserved.

### 5. Make Email and Notifications Reliable

Centralize provider transport; default local/test sending to a blocked or capture backend. Implement outbox/deduplication/post-commit queue, processor/retries and admin failure visibility. Correct flags, duplicate sends, recipients, text fallback and reply-to. Add provider events only after authenticated webhook design. Implement reminder cadence after anchor/stop rules are settled.

Acceptance: saved enquiry survives outages, failed notification is visible/retryable, retry does not duplicate accepted messages, no false delivery/open metrics.

### 6. Finish Identity and Permissions

Remove automatic password accounts from guest booking. Validate profile edits atomically, protect ownership and preferences, decide verified invitation/recovery journey. Apply model permissions to dashboard datasets/actions; confirm role groups. Implement reset/resend only as an intentional complete flow.

Acceptance: guest requests work, unauthorized cross-user access fails, role permissions match both surfaces, invalid profile data makes no partial change.

### 7. Align UI, Dynamic Data and Error Handling

Wire hero/blog guide/navigation records, stable filter slugs, searchable/paginated discovery and clear empty states. Preserve server-side behavior without JS where practical. Complete or deliberately retire unused comments/newsletter/saved-idea UI. Connect SEO metadata. Replace implementation notes with approved customer wording.

Acceptance: each visible action maps to a supported backend capability; staff edits change intended public content; empty or failed states do not imply fake availability.

### 8. Verify Uploads, Deployment and Monitoring

Choose durable media storage and private resume downloads; verify Uploadcare widget/save/render without touching unrelated fields. Confirm Render entry/build settings; repair health checks; verify effective headers. Guard destructive commands and remove obsolete deployment paths only after confirming they are unused.

Acceptance: package image survives deployment, private documents require permission, health reflects actual DB/provider readiness, build cannot silently skip required setup.

### 9. UX, Visual Polish and Cleanup

Only after workflow acceptance, consolidate duplicate templates/JS/styles and legacy names, use a reproducible asset build, verify desktop/mobile menus, filters, form focus/errors, poster/gallery framing, and accessibility. Retain current brand and working functionality.

Acceptance: screenshots/browser checks of real data, zero broken interactive controls on supported paths, meaningful regression coverage. No generic replacement pages.

## Required Follow-Up Verification Before a Production-Ready Claim

- Read-only live schema/content inventory: migration state, published counts, missing images/itineraries, estimate/source provenance, malformed relationships, group permissions and legacy model usage.
- Approved staging end-to-end requests: anonymous quote/contact/services, authenticated profile, optional cart, feedback moderation, admin image upload, private document access, provider failure/retry and redirects.
- Provider verification: correct verified sender, final inbox routing, accepted/delivered distinction, duplicate handling, webhook signatures and secrets management.
- PostgreSQL transaction/constraint tests, deploy rehearsal, backup/recovery check and role matrix tests.
- Browser verification for desktop/mobile, JS-disabled core forms, keyboard navigation, filter URL behavior and real media loading.

Until those checks and the confirmed blockers are addressed, the accurate description is: a functioning catalog and partial enquiry platform with significant security, workflow and operational gaps, not a fully verified production system.
