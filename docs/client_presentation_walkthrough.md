# Myriad Travel Website Client Presentation Walkthrough

## Purpose of the platform

The website is designed to help Myriad Travel turn campaign traffic, social media interest, referrals, and direct search visitors into qualified travel enquiries. It gives clients a polished way to explore packages, understand current offers, submit booking requests, and reach the team quickly by WhatsApp.

The business goal is simple: make Myriad Travel easier to discover, easier to trust, and easier to contact, while giving the internal team better structure for handling enquiries, package updates, content, and follow ups.

## Presentation flow for the client

Start with the public website, then move into the package experience, then show the enquiry and admin workflow.

1. Home page overview

   Explain that the home page introduces the brand, current offers, key package collections, service areas, reviews, and contact channels. The top navigation organizes travel by customer intent: Explore Kenya, Explore The World, Tours and Safaris, Signature Experiences, Blogs, About Us, and Contact Us.

2. Featured packages section

   The “Signature Safaris, Coastal Escapes and Holidays” section highlights the four most important home packages. The first item can be controlled by admin ranking, so the current campaign package, such as Twende Chalbi, can stay first when it is the priority offer.

3. Package card journey

   A user sees the destination, package title, price, duration, image, category, and quick actions. The package cards are clickable, so users can move from the home page directly into the full package detail page.

4. Package detail journey

   The detail page gives the client enough information to decide whether to enquire. It shows the destination, hero image, price, duration, highlights, itinerary, inclusions, exclusions, travel notes, and booking request options.

5. Twende Chalbi campaign journey

   The Chalbi page is treated as a special current offer. It has a campaign style layout, full itinerary, pricing, room preference, adult and child selectors, WhatsApp booking message, and website booking request. When a user changes adults, children, or room preference, the WhatsApp message captures those details automatically.

6. Enquiry and booking request flow

   A user can submit a website quote request or send a WhatsApp enquiry. Website submissions are saved as quote requests and trigger emails to the client and admin. The client receives a confirmation with their trip details and a response timeline. The admin receives the client details, trip summary, captured notes, and recommended follow up actions.

7. Admin workflow

   The Django admin remains the structured back office for managing packages, images, itinerary content, blogs, quote requests, follow ups, customer feedback, and operational records. The owner dashboard gives the business team a more practical daily view of what needs attention.

## Key user flows

### Visitor exploring a package

Home page -> Featured package card -> Package detail page -> Review itinerary and inclusions -> Submit booking request or WhatsApp the team.

### Campaign visitor for Twende Chalbi

Campaign website or social link -> Twende Chalbi detail page -> Select adults, children, and room preference -> WhatsApp with captured details or submit booking request -> Admin receives enquiry -> Team follows up.

### Blog or content visitor

Home page or navigation -> Blogs -> Read travel content -> Move to package or contact flow. This supports organic discovery and gives the brand authority beyond package listings.

### Admin updating an offer

Admin login -> Package list -> Edit package details, price, itinerary, rank, image, or status -> Published package appears on the site -> Home rank controls whether it appears in the four featured home slots.

### Admin handling a lead

Admin receives email -> Opens quote request in admin -> Confirms dates, pax, child ages, rooming, and availability -> Updates status and follow up record -> Sends quote or WhatsApp response.

## Current features to highlight

- Branded public website for Myriad Travel.
- Responsive navigation for Kenya, international, safaris, signature experiences, blogs, about, and contact.
- Four featured home packages controlled through admin ranking.
- Clickable package cards with direct package detail pages.
- Special Twende Chalbi campaign page with full 5 day itinerary.
- WhatsApp enquiry links that carry package and traveller details.
- Website quote request forms connected to the database.
- Client and admin email notifications through the configured email provider.
- Resend email provider support for delivery and analytics.
- Uploadcare image support for package images.
- Blogs and content pages for destination storytelling.
- Trip feedback form for post trip reviews.
- Owner dashboard and Django admin for operations.
- Admin controls for packages, content, quote requests, follow ups, and visibility.

## Business goals supported

1. Increase qualified enquiries

   The site reduces friction by letting users enquire from package cards, package detail pages, WhatsApp, and quote forms.

2. Promote current campaigns

   Home ranking and special package pages allow the business to push the latest campaign first, such as Twende Chalbi.

3. Improve client confidence

   Rich package pages, itineraries, inclusions, images, and clear contact options make the business look organized and trustworthy.

4. Support faster response times

   Email notifications and admin records help the team respond quickly, with a target of 2 hours where possible and up to 24 hours.

5. Reduce manual confusion

   Enquiries capture package, dates, travellers, children, rooming notes, and contact details, giving the team a cleaner starting point.

6. Build a reusable sales engine

   New packages, offers, blogs, and campaigns can be added from admin without rebuilding the website.

## Admin section talking points

The admin side is the control center. It is not only for editing pages; it supports daily operations.

- Packages: create, edit, publish, rank, price, image, and manage package details.
- Itineraries: maintain day by day package plans.
- Quote requests: view new enquiries, contact clients, and update status.
- Follow ups: track reminders after client enquiries.
- Blogs: publish destination and travel content.
- Trip feedback: collect client feedback and decide which reviews appear publicly.
- Images: upload package visuals through admin and Uploadcare.
- Users and access: support staff access and controlled back office work.

## Suggested demo script

1. “This is the home page. It quickly positions Myriad Travel and shows the main travel categories.”
2. “This section is the sales priority area. The four packages here are controlled by admin ranking.”
3. “When I open Twende Chalbi, it feels like a special current campaign, not just a generic package.”
4. “A client can select adults, children, and room preference, then WhatsApp the team with those details already captured.”
5. “If they submit the website form, the request is saved and both the client and admin receive email notifications.”
6. “Inside admin, the team can manage packages, content, enquiries, follow ups, and feedback.”
7. “The business value is a cleaner sales pipeline: traffic comes in, packages are clear, enquiries are captured, and the team knows what to do next.”

## Details updated for presentation

Company location shown on the website:

Parklands, Crescent Business Center, 6th Floor, Nairobi, Kenya

## Recommended next phase

- Add more package inventory and classify offers into Explore Kenya, Explore The World, Tours and Safaris, and Signature Experiences.
- Improve the owner dashboard metrics after more enquiries are collected.
- Add deal poster pages for offer lines such as coast, Dubai, Zanzibar, and seasonal campaigns.
- Set up Resend tracking fully so the team can review email opens, clicks, and delivery performance.
- Train the admin team on package ranking, quote handling, image uploads, and follow up status updates.
