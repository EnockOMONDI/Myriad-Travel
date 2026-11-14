# Explore Kenya day trips

The command `python manage.py seed_kenya_day_trips` creates the seven supplied Explore Kenya day trips as drafts. Run migrations first. To seed Supabase and publish immediately, run `python manage.py seed_kenya_day_trips --publish --settings=tours_travels.settings_prod` in the deployed app's shell. The command is repeatable: it leaves existing package content untouched, and `--publish` promotes existing matching drafts. It requires an existing Kenya country destination. It creates the specific place destinations, including Suswa, a Day Trips category, and an Explore Kenya Day Trips collection only when absent.

| Trip | From rate, adult | Basis | Information still to confirm |
| --- | ---: | --- | --- |
| Nairobi National Park Half-Day Safari | KSh 4,700 | Six guests sharing a safari van | Approved image, child rate, price validity, whether six is the minimum group size |
| Mount Longonot Crater Hike | KSh 3,500 | Scheduled shared group departure | Approved image, child rate, price validity, scheduled dates and group minimum |
| Wasini Island & Kisite Marine Park Day Trip | KSh 9,500 | Six guests sharing Diani/Ukunda transfers | Approved image, child rate, price validity, dates and six-person rate confirmation |
| Lake Naivasha & Hell’s Gate Day Trip | KSh 5,500 | Four guests sharing transport | Approved image, child rate, price validity, four-person rate confirmation |
| Sagana White-Water Rafting Day Trip | KSh 8,950 | Adult in shared transport from Nairobi | Approved image, rafting participation requirements, river/operator availability |
| Suswa SGR Day Trip | KSh 3,250 | Friday–Sunday group departure | Approved image, train/ticket and resort availability |
| Machakos Day Trip | KSh 4,950 | Group-joining departure from Nairobi | Approved image, attraction access and optional activity availability |

Each record contains the supplied overview, timed schedule, inclusions, exclusions, pickup area, duration, and an approximate-timings/final-quote notice. No child rate was supplied, so the required legacy `child_price` field remains zero and is not advertised as a child offer. Rafting, train departures, resort access and optional activities remain subject to availability and operator confirmation.

Before accepting bookings, confirm the rates and operating dates with Myriad, supply approved images, and verify the operator and attraction availability. The public page does not present an automatic USD conversion for the day-trip cards. Enquiries remain requests for a final quote, not reservations.
