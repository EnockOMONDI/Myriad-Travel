# Explore Kenya day trips

The command `python manage.py seed_kenya_day_trips` creates four **draft** packages from the Myriad copy supplied on 14 November 2026. Run migrations first. The command is repeatable: it leaves existing package records untouched, and it requires an existing Kenya country destination. It creates the four specific place destinations, a Day Trips category, and an Explore Kenya Day Trips collection only when absent.

| Trip | Proposed from rate, Kenyan citizen adult in shared transport | Basis | Information still to confirm |
| --- | ---: | --- | --- |
| Nairobi National Park Half-Day Safari | KSh 4,700 | Six guests sharing a safari van | Approved image, child rate, price validity, whether six is the minimum group size |
| Mount Longonot Crater Hike | KSh 3,500 | Scheduled shared group departure | Approved image, child rate, price validity, scheduled dates and group minimum |
| Wasini Island & Kisite Marine Park Day Trip | KSh 9,500 | Six guests sharing Diani/Ukunda transfers | Approved image, child rate, price validity, dates and six-person rate confirmation |
| Lake Naivasha & Hell’s Gate Day Trip | KSh 5,500 | Four guests sharing transport | Approved image, child rate, price validity, four-person rate confirmation |

Each draft contains the supplied overview, timed schedule, inclusions, exclusions, pickup area, duration, and an approximate-timings/final-quote notice. Park entry is included in the rate. No child rate was supplied, so the required legacy `child_price` field is set to zero **only on these unpublished drafts**. Zero is not a child offer. Do not publish until a genuine child rate or a child-price-on-request product rule is entered and verified.

Before publication, confirm the rates and operating dates with Myriad, supply approved images, review the exact category/destination placement, and set each day trip's price status to confirmed. The public page labels these as Kenyan-citizen adult shared-transport rates; it does not present an automatic USD conversion for the day-trip cards. Enquiries remain requests for a final quote, not reservations.
