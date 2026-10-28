from django.core.management.base import BaseCommand
from adminside.models import Destination


DESTINATIONS = (
    ('Kilifi', 'kilifi', 'Kilifi coast stays, beaches and dhow-lined shoreline escapes.', 30),
    ('Malindi', 'malindi', 'Malindi beaches, marine experiences and coastal holidays.', 31),
    ('Watamu', 'watamu', 'Watamu beaches, marine conservation and relaxed coastal stays.', 32),
    ('Kisumu', 'kisumu', 'Kisumu on Lake Victoria, with lakeside culture and western Kenya escapes.', 33),
    ('Longonot', 'longonot', 'Mount Longonot day hikes and Rift Valley outdoor escapes.', 34),
    ('Machakos', 'machakos', 'Machakos day trips, hills and short escapes from Nairobi.', 35),
    ('Kajiado / Suswa', 'kajiado-suswa', 'Kajiado and Suswa landscapes for day trips and countryside escapes.', 36),
    ('Sagana', 'sagana', 'Sagana river activities, outdoor adventures and weekend escapes.', 37),
)


WORLD_DESTINATIONS = (
    ('Tanzania', 'tanzania', 'Tanzania combines classic northern safari circuits, mountain landscapes and Indian Ocean culture.', ['Serengeti game drives', 'Ngorongoro Crater visit', 'Kilimanjaro foothill views', 'Zanzibar Stone Town and beach time']),
    ('Uganda', 'uganda', 'Uganda brings together rainforest primates, broad savannah and the source of the Nile.', ['Gorilla trekking', 'Chimpanzee tracking', 'Murchison Falls game drive', 'Nile boat safari']),
    ('Rwanda', 'rwanda', 'Rwanda is a compact, well-connected destination for mountain gorillas, lakes and thoughtful city stays.', ['Volcanoes gorilla trekking', 'Akagera game drive', 'Kigali city tour', 'Nyungwe canopy walk']),
    ('Egypt', 'egypt', 'Egypt pairs ancient monuments and Nile history with Red Sea relaxation.', ['Pyramids of Giza', 'Nile cruise', 'Karnak Temple visit', 'Red Sea snorkelling']),
    ('South Africa', 'south-africa', 'South Africa offers city culture, wine country, dramatic coastlines and varied safari routes.', ['Cape Town city tour', 'Table Mountain cableway', 'Winelands tasting', 'Kruger safari']),
    ('Morocco', 'morocco', 'Morocco moves from imperial cities and souks to Atlas mountain villages and Atlantic coast.', ['Marrakech medina walk', 'Atlas Mountains excursion', 'Sahara desert camp', 'Essaouira coastal visit']),
    ('Namibia', 'namibia', 'Namibia is a wide-open journey through desert dunes, rugged coast and exceptional wildlife.', ['Sossusvlei dunes', 'Etosha game drive', 'Swakopmund desert activities', 'Skeleton Coast viewpoints']),
    ('Zimbabwe', 'zimbabwe', 'Zimbabwe combines Victoria Falls, wildlife-rich parks and warm river-country experiences.', ['Victoria Falls tour', 'Hwange game drive', 'Zambezi sunset cruise', 'Mana Pools canoe safari']),
    ('USA', 'united-states', 'The USA combines major city experiences, national parks, coastlines and flexible multi-state journeys.', ['New York city landmarks', 'Grand Canyon visit', 'California coast drive', 'Alaska or national parks']),
    ('Canada', 'canada', 'Canada offers big landscapes, polished cities and outdoor journeys across every season.', ['Banff and Lake Louise', 'Niagara Falls visit', 'Vancouver city and coast', 'Northern lights experience']),
    ('Brazil', 'brazil', 'Brazil brings together Atlantic beaches, music-filled cities, rainforest and iconic natural landmarks.', ['Rio city tour', 'Christ the Redeemer', 'Iguazu Falls', 'Amazon river experience']),
    ('Caribbean Islands', 'caribbean-islands', 'The Caribbean is a collection of warm-water islands for beach time, sailing and easygoing escapes.', ['Island beach day', 'Snorkelling or diving', 'Catamaran sailing', 'Local food and culture tour']),
    ('Germany', 'germany', 'Germany blends historic cities, cultural collections, scenic rivers and seasonal celebrations.', ['Berlin history tour', 'Munich old town', 'Rhine Valley cruise', 'Bavarian Alps excursion']),
    ('England', 'england', 'England combines London landmarks, historic towns, countryside and coastal heritage.', ['London city landmarks', 'Stonehenge visit', 'Cotswolds villages', 'Lake District walk']),
    ('Italy', 'italy', 'Italy brings art cities, regional food, ancient sites and Mediterranean coastlines into one journey.', ['Rome ancient sites', 'Florence art walk', 'Venice canal cruise', 'Amalfi Coast drive']),
    ('France', 'france', 'France offers celebrated art, food, architecture, wine regions and varied landscapes.', ['Paris city landmarks', 'Loire Valley chateaux', 'French Riviera coast', 'Provence food and villages']),
    ('Spain', 'spain', 'Spain pairs historic cities and rich food culture with Mediterranean beaches and island escapes.', ['Barcelona architecture', 'Madrid art museums', 'Seville old town', 'Costa del Sol beach time']),
    ('Greece', 'greece', 'Greece combines ancient history, island beaches, Mediterranean food and relaxed coastal days.', ['Athens Acropolis', 'Santorini caldera views', 'Crete villages and beaches', 'Island boat day']),
    ('Turkey', 'turkey', 'Turkey connects Istanbul heritage, Aegean coast, Cappadocia landscapes and generous food culture.', ['Istanbul old city', 'Cappadocia hot-air balloon', 'Ephesus ruins', 'Turquoise Coast cruise']),
    ('China', 'china', 'China offers immense variety, from imperial landmarks and modern cities to mountain and river scenery.', ['Great Wall visit', 'Beijing heritage tour', 'Shanghai city experience', 'Li River scenery']),
    ('Thailand', 'thailand', 'Thailand combines welcoming city energy, temples, food culture and tropical beaches.', ['Bangkok temple tour', 'Chiang Mai cultural visit', 'Thai cooking class', 'Island boat trip']),
    ('India', 'india', 'India is a layered journey of heritage, food, colour, wildlife and diverse regional landscapes.', ['Taj Mahal visit', 'Rajasthan heritage route', 'Kerala backwaters', 'Ranthambore safari']),
    ('Singapore', 'singapore', 'Singapore is a polished city break with gardens, neighbourhood food and easy regional connections.', ['Gardens by the Bay', 'Marina Bay city walk', 'Hawker food tour', 'Sentosa island day']),
    ('Dubai', 'dubai', 'Dubai combines modern city experiences, desert landscapes, shopping and warm Gulf coast stays.', ['Burj Khalifa and Downtown', 'Desert safari', 'Old Dubai and creek tour', 'Beach or Palm Jumeirah day']),
    ('Abu Dhabi', 'abu-dhabi', 'Abu Dhabi pairs grand architecture, desert landscapes, museums and calm Gulf coast experiences.', ['Sheikh Zayed Grand Mosque', 'Louvre Abu Dhabi', 'Desert safari', 'Yas Island visit']),
    ('Israel', 'israel', 'Israel brings together layered history, Mediterranean coast, desert landscapes and sacred sites.', ['Jerusalem old city', 'Dead Sea float', 'Tel Aviv coastal walk', 'Masada sunrise']),
    ('Saudi Arabia', 'saudi-arabia', 'Saudi Arabia offers emerging cultural routes, desert scenery, Red Sea coast and historic settlements.', ['AlUla heritage sites', 'Wadi Al Disah', 'Jeddah historic district', 'Red Sea diving']),
    ('Jordan', 'jordan', 'Jordan is a compact heritage journey through desert, ancient cities and the healing waters of the Dead Sea.', ['Petra visit', 'Wadi Rum camp', 'Dead Sea float', 'Jerash ruins']),
    ('Oman', 'oman', 'Oman combines dramatic wadis, frankincense heritage, desert dunes and a distinctive Arabian coastline.', ['Muscat city tour', 'Wadi Shab swim', 'Wahiba Sands camp', 'Nizwa Fort visit']),
    ('Zanzibar', 'zanzibar', 'Zanzibar adds Swahili heritage, spice culture, clear water and beach time to an Indian Ocean journey.', ['Stone Town walking tour', 'Spice farm visit', 'Dhow sunset sail', 'Nungwi or Matemwe beach day']),
    ('Seychelles', 'seychelles', 'Seychelles offers granite islands, clear water, rainforest walks and unhurried beach days.', ['Mahé island tour', 'Praslin and Vallée de Mai', 'La Digue cycling', 'Snorkelling excursion']),
    ('Mauritius', 'mauritius', 'Mauritius combines lagoon beaches, volcanic scenery, Creole food and polished island stays.', ['Le Morne viewpoint', 'Catamaran lagoon cruise', 'Black River Gorges', 'Port Louis food and market tour']),
    ('Maldives', 'maldives', 'The Maldives is designed for clear-water relaxation, reef time and quiet island stays.', ['Resort beach time', 'Snorkelling or diving', 'Sunset dhoni cruise', 'Sandbank picnic']),
    ('Madagascar', 'madagascar', 'Madagascar is a wildlife-rich island journey shaped by unique species, baobabs and varied coastlines.', ['Avenue of the Baobabs', 'Lemur reserve visit', 'Tsingy landscapes', 'Indian Ocean beach stay']),
)


KENYA_CONTENT = {
    'kenya': ('Kenya brings together wildlife reserves, Indian Ocean beaches, highland scenery and practical city-based travel.', ['Safari game drive', 'Coastal beach stay', 'Cultural or community visit', 'Rift Valley scenic stop']),
    'mombasa-north-coast': ('Mombasa and the North Coast combine Swahili history, warm beaches, marine activities and easy resort stays.', ['Fort Jesus and Old Town', 'North Coast beach day', 'Wasini or marine excursion', 'Swahili food experience']),
    'diani-beach': ('Diani is a relaxed Indian Ocean base for white-sand beaches, reef excursions and coastal adventure.', ['Beach and reef time', 'Kisite-Mpunguti boat trip', 'Colobus conservation visit', 'Kaya Kinondo cultural experience']),
    'kilifi': ('Kilifi is a quieter coastal escape known for creek scenery, water activities and spacious beach stays.', ['Kilifi Creek boat trip', 'Beach and swimming time', 'Mnarani ruins visit', 'Kayaking or paddleboarding']),
    'malindi': ('Malindi combines Swahili heritage, marine conservation, beaches and easy access to Watamu and the coast.', ['Malindi Marine Park', 'Gede Ruins visit', 'Vasco da Gama Pillar', 'Beach and seafood evening']),
    'watamu': ('Watamu offers protected beaches, coral reefs, turtle conservation and low-key coastal days.', ['Watamu Marine Park', 'Mida Creek mangrove tour', 'Gede Ruins', 'Turtle conservation visit']),
    'lamu': ('Lamu is a historic Swahili island experience with dhow sailing, narrow streets and quiet beaches.', ['Lamu Old Town walk', 'Dhow sunset sail', 'Shela beach day', 'Takwa ruins excursion']),
    'nairobi': ('Nairobi is Kenya\'s practical gateway for city culture, wildlife close to the capital and onward travel.', ['Nairobi National Park', 'Giraffe Centre', 'Karen and museum circuit', 'City food experience']),
    'naivasha': ('Naivasha combines lake scenery, flower-country stays, walking safaris and easy Rift Valley access.', ['Lake Naivasha boat ride', 'Crescent Island walk', 'Hell\'s Gate cycling', 'Elmenteita or escarpment viewpoint']),
    'naivasha-and-elementaita': ('Naivasha and Elementaita make a scenic Rift Valley pairing of lakes, birds, wildlife and restorative stays.', ['Lake Naivasha boat ride', 'Crescent Island walk', 'Lake Elementaita birding', 'Hell\'s Gate cycling']),
    'longonot': ('Mount Longonot is a strong day-trip choice for crater hiking, Rift Valley views and active outdoor travel.', ['Mount Longonot crater hike', 'Rift Valley viewpoint', 'Lake Naivasha stop', 'Guided nature walk']),
    'machakos': ('Machakos offers accessible hills, viewpoints, gardens and short countryside escapes from Nairobi.', ['Machakos city and market', 'Machakos People\'s Park', 'Hillside viewpoints', 'Local food and craft visit']),
    'kajiado-suswa': ('Kajiado and Suswa open into Maasai-country landscapes, volcanic terrain and close-to-Nairobi day journeys.', ['Suswa crater viewpoint', 'Maasai cultural visit', 'Rift Valley scenic drive', 'Countryside picnic']),
    'sagana': ('Sagana is a practical outdoor base for river activities, adventure weekends and central Kenya escapes.', ['Tana River rafting', 'Zipline or high ropes', 'Cave and nature walk', 'Aberdare foothill day trip']),
    'kisumu': ('Kisumu is a lakeside base for western Kenya culture, birdlife, markets and Lake Victoria sunsets.', ['Kisumu Impala Sanctuary', 'Dunga Bay sunset', 'Kibuye Market visit', 'Kit Mikayi or nearby cultural site']),
    'maasai-mara-national-reserve': ('Maasai Mara is Kenya\'s signature wildlife landscape, known for big cats, open plains and seasonal movement.', ['Big Five game drives', 'Migration viewing when seasonal', 'Maasai community visit', 'Hot-air balloon safari']),
    'masai-mara-national-reserve': ('The Masai Mara offers open savannah, remarkable wildlife density and memorable guided safari days.', ['Big Five game drives', 'River and wildlife viewing', 'Maasai community visit', 'Sunrise bush breakfast']),
    'amboseli-national-park': ('Amboseli pairs elephant-rich plains with iconic Mount Kilimanjaro views and Maasai-country landscapes.', ['Elephant game drive', 'Observation Hill', 'Kilimanjaro viewpoint', 'Maasai community visit']),
    'samburu-national-reserve': ('Samburu brings dry northern landscapes, distinctive wildlife and strong cultural encounters.', ['Game drive for northern species', 'Ewaso Nyiro river views', 'Samburu community visit', 'Guided bush walk']),
    'tsavo-east-national-park': ('Tsavo East is a spacious red-earth safari landscape with elephants, baobabs and remote wilderness.', ['Game drives', 'Aruba Dam wildlife viewing', 'Mudanda Rock viewpoint', 'Yatta Plateau scenery']),
    'mount-kenya': ('Mount Kenya offers highland scenery, forest trails and a choice of gentle walks or serious trekking.', ['Forest nature walk', 'Mount Kenya foothill views', 'Sirimon or Naro Moru route planning', 'Highland farm visit']),
    'mount-kenya-national-park': ('Mount Kenya National Park is a high-altitude adventure area with forest, moorland and summit routes.', ['Guided mountain trek', 'Chogoria scenery', 'Birdwatching and forest walk', 'Nanyuki highland visit']),
    'nakuru': ('Nakuru connects lake and escarpment scenery with wildlife, birding and accessible Great Rift Valley travel.', ['Lake Nakuru game drive', 'Baboon Cliff viewpoint', 'Menengai Crater', 'Lake Nakuru birding']),
    'marsabit-county': ('Marsabit County is a northern Kenya journey through volcanic landscapes, desert routes and remote cultural country.', ['Marsabit National Park', 'Lake Paradise viewpoint', 'Desert road adventure', 'Local cultural visit']),
    'chalbi-desert': ('The Chalbi Desert is a remote northern Kenya landscape of salt flats, open horizons and expedition-style travel.', ['Desert crossing', 'Lake Turkana shore', 'Sunrise and sunset photography', 'Local community encounter']),
    'great-rift-valley': ('Kenya\'s Great Rift Valley combines escarpment viewpoints, lakes, volcanic landscapes and road-trip variety.', ['Escarpment viewpoints', 'Lake visit', 'Hell\'s Gate activities', 'Menengai or Longonot landscape']),
    'great-rift-valley-naivasha': ('The Naivasha Rift Valley route offers lakeside scenery, wildlife walks and a relaxed countryside pace.', ['Lake Naivasha boat ride', 'Crescent Island walk', 'Hell\'s Gate cycling', 'Rift Valley viewpoint']),
    'vipingo-ridge': ('Vipingo Ridge is a coastal holiday base for beach time, golf, nature and North Coast stays.', ['Beach day', 'Golf experience', 'Coastal nature walk', 'Mombasa North Coast excursion']),
    '07-tsavo-east-watamu-malindi': ('This Kenya route links Tsavo East wildlife with the beaches and marine culture of Watamu and Malindi.', ['Tsavo East game drive', 'Watamu marine excursion', 'Malindi heritage visit', 'Coastal beach time']),
    'kajiado-county': ('Kajiado County offers accessible southern Kenya landscapes, wildlife gateways and Maasai cultural experiences.', ['Amboseli day or safari route', 'Maasai cultural visit', 'Rift Valley viewpoint', 'Local countryside drive']),
    'kwale-county': ('Kwale County stretches from Diani beaches to coastal forests, marine parks and Swahili heritage.', ['Diani beach time', 'Kisite-Mpunguti boat trip', 'Shimba Hills visit', 'Kaya Kinondo cultural experience']),
    'narok-county': ('Narok County is the gateway to Maasai Mara, open savannah, escarpment views and Maasai culture.', ['Maasai Mara safari', 'Maasai community visit', 'Great Rift Valley viewpoint', 'Guided nature walk']),
    'masai-mara-and-diani': ('Masai Mara and Diani combine Kenya\'s classic wildlife safari with a warm-water Indian Ocean finish.', ['Masai Mara game drives', 'Diani beach time', 'Marine boat excursion', 'Maasai community visit']),
}


class Command(BaseCommand):
    help = 'Create or update Kenya destinations used by the Explore Kenya menu.'

    def upsert_destination(self, *, name, slug, description, things_to_do, region, destination_type, parent=None, display_order=0):
        destination, created = Destination.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'destination_type': destination_type,
                'region': region,
                'parent': parent,
                'description': description,
                'things_to_do': things_to_do,
                'is_active': True,
                'show_in_navigation': True,
                'display_order': display_order,
            },
        )
        action = 'created' if created else 'updated'
        self.stdout.write(f'{action}: {destination.name} ({destination.slug})')
        return destination

    def handle(self, *args, **options):
        kenya = Destination.objects.filter(
            name='Kenya',
            destination_type=Destination.COUNTRY,
            region='kenya',
        ).first()
        if not kenya:
            self.stderr.write(self.style.ERROR('Kenya country destination was not found.'))
            return

        rows = list(DESTINATIONS)
        if not Destination.objects.filter(slug='lamu').exists():
            rows.append(('Lamu', 'lamu', 'Lamu Island heritage, beaches and island escapes.', 29))

        for name, slug, description, display_order in rows:
            content = KENYA_CONTENT.get(slug, (description, [
                f'{name} guided visit',
                f'{name} scenic experience',
                f'{name} local culture and food',
                f'{name} nature and photography stop',
            ]))
            self.upsert_destination(
                name=name,
                slug=slug,
                description=content[0],
                things_to_do=content[1],
                region='kenya',
                destination_type=Destination.PLACE,
                parent=kenya,
                display_order=display_order,
            )

        for name, slug, description, things_to_do in WORLD_DESTINATIONS:
            existing = Destination.objects.filter(slug=slug).first()
            self.upsert_destination(
                name=name,
                slug=slug,
                description=description,
                things_to_do=things_to_do,
                region=existing.region if existing else next(
                    region for region, labels in {
                        'africa': {'Tanzania', 'Uganda', 'Rwanda', 'Egypt', 'South Africa', 'Morocco', 'Namibia', 'Zimbabwe'},
                        'americas': {'Canada', 'Brazil', 'Caribbean Islands'},
                        'europe': {'Germany', 'England', 'Italy', 'France', 'Spain', 'Greece', 'Turkey'},
                        'asia': {'China', 'Thailand', 'India', 'Singapore'},
                        'middle-east': {'Abu Dhabi', 'Israel', 'Saudi Arabia', 'Jordan', 'Oman'},
                        'indian-ocean-islands': {'Seychelles', 'Madagascar'},
                    }.items() if name in labels
                ),
                destination_type=existing.destination_type if existing else Destination.COUNTRY,
                parent=existing.parent if existing else None,
                display_order=existing.display_order if existing else 50,
            )

        for slug, (description, things_to_do) in KENYA_CONTENT.items():
            destination = Destination.objects.filter(slug=slug, region='kenya').first()
            if destination:
                destination.description = description
                destination.things_to_do = things_to_do
                destination.is_active = True
                destination.show_in_navigation = True
                destination.save(update_fields=['description', 'things_to_do', 'is_active', 'show_in_navigation', 'updated_at'])
