from django.core.management.base import BaseCommand
from django.db import transaction

from adminside.models import Destination


# Only records with known generic/empty copy are eligible. Existing reviewed
# descriptions and activity lists are left untouched by default.
LEGACY_GUIDES = {
    'akagera-national-park': ('Akagera National Park is Rwanda\'s savannah reserve, with lakes, wetlands and a growing range of wildlife.', ['Game drives', 'Boat trip on Lake Ihema', 'Birdwatching in the wetlands', 'Community and conservation visit']),
    'arusha': ('Arusha is the practical gateway to northern Tanzania\'s safari circuit and Mount Meru, with a lively city and coffee-country setting.', ['Arusha National Park', 'Mount Meru foothills', 'Coffee farm visit', 'Local market and city walk']),
    'cairo': ('Cairo is Egypt\'s energetic capital, linking ancient monuments, museums, markets and the Nile.', ['Pyramids of Giza', 'Egyptian Museum', 'Khan el-Khalili walk', 'Nile cruise']),
    'cape-town': ('Cape Town combines a dramatic coastline, mountain scenery, layered history, food culture and nearby wine country.', ['Table Mountain', 'Cape Peninsula drive', 'Robben Island', 'Winelands visit']),
    'dar-es-salaam': ('Dar es Salaam is a coastal gateway to Tanzania, with Swahili heritage, island excursions and Indian Ocean life.', ['City and National Museum tour', 'Bongoyo or Mbudya island trip', 'Kivukoni fish market', 'Swahili food experience']),
    'johannesburg': ('Johannesburg is South Africa\'s major urban gateway, with important history, arts, dining and nearby heritage sites.', ['Apartheid Museum', 'Soweto tour', 'Constitution Hill', 'Cradle of Humankind']),
    'kibale-forest-national-park': ('Kibale Forest is Uganda\'s leading primate destination, surrounded by crater lakes, forest and community landscapes.', ['Chimpanzee tracking', 'Forest birding', 'Bigodi wetland walk', 'Crater-lake excursion']),
    'kigali': ('Kigali is Rwanda\'s clean, welcoming capital and a useful base for city culture, conservation and journeys into the country\'s highlands.', ['Kigali Genocide Memorial', 'Kimironko Market', 'Nyamirambo cultural walk', 'Inema Arts Center']),
    'lake-manyara-national-park': ('Lake Manyara National Park is a compact northern Tanzania safari area known for varied habitats, birdlife and a dramatic escarpment setting.', ['Game drive', 'Lake and wetland birding', 'Canopy walkway', 'Rift Valley viewpoint']),
    'matobo-national-park': ('Matobo National Park is a Zimbabwe landscape of balancing granite hills, wildlife, ancient rock art and wide southern skies.', ['Granite kopjes drive', 'Rhino tracking', 'San rock-art site', 'Cultural or heritage tour']),
    'mount-kilimanjaro-national-park': ('Mount Kilimanjaro National Park protects Africa\'s highest mountain and the forest, moorland and alpine landscapes on its routes.', ['Guided mountain trek', 'Foothill nature walk', 'Waterfall visit', 'Chagga cultural experience']),
    'murchison-falls-national-park': ('Murchison Falls National Park combines savannah wildlife, the Nile and one of Uganda\'s most powerful waterfalls.', ['Game drive', 'Nile boat safari', 'Murchison Falls viewpoint', 'Birdwatching']),
    'serengeti-national-park': ('Serengeti National Park is a vast northern Tanzania safari landscape famous for open plains, predators and seasonal wildlife movement.', ['Game drives', 'Migration viewing when seasonal', 'Sunrise bush experience', 'Hot-air balloon safari']),
    'tarangire-national-park': ('Tarangire National Park is known for elephant herds, baobabs, seasonal wetlands and quieter northern Tanzania game viewing.', ['Game drive', 'Elephant viewing', 'Baobab landscape photography', 'Birdwatching']),
    'zambia': ('Zambia offers uncrowded safari landscapes, powerful rivers and walking experiences led by skilled guides.', ['South Luangwa safari', 'Walking safari', 'Victoria Falls', 'Zambezi canoe or boat trip']),
    'zanzibar-island': ('Zanzibar Island combines Swahili heritage, spice culture, clear water and relaxed Indian Ocean beach stays.', ['Stone Town walk', 'Spice farm visit', 'Dhow sunset sail', 'Nungwi or Matemwe beach day']),
    'alaska': ('Alaska is a vast North American destination for wilderness, glaciers, wildlife and long summer landscapes.', ['Glacier cruise', 'Wildlife viewing', 'Denali landscapes', 'Northern lights when seasonal']),
    'caribbean': ('The Caribbean is a collection of warm-water islands suited to beach time, sailing, reef experiences and local culture.', ['Island beach day', 'Snorkelling or diving', 'Catamaran sailing', 'Local food and culture tour']),
    'armenia': ('Armenia pairs a historic capital with monasteries, mountain scenery, distinctive food and a strong cultural identity.', ['Yerevan city walk', 'Geghard and Garni', 'Lake Sevan', 'Local food and wine experience']),
    'indonesia': ('Indonesia brings together island cultures, volcanic landscapes, rainforest, temples and warm-water escapes.', ['Temple visit', 'Volcano sunrise', 'Island or beach day', 'Local food experience']),
    'phuket': ('Phuket is a tropical Andaman base for beaches, island excursions, food and easy access to southern Thailand.', ['Beach day', 'Phang Nga Bay boat trip', 'Old Phuket Town', 'Snorkelling or diving']),
    'ubud-bali': ('Ubud is Bali\'s cultural and wellness centre, surrounded by rice terraces, temples, arts and river valleys.', ['Rice-terrace walk', 'Temple visit', 'Balinese cooking class', 'Arts and market tour']),
    'mediterranean-europe': ('Mediterranean Europe brings together colourful coastal towns, island waters, historic cities and long-standing food cultures.', ['Coastal town visit', 'Island or harbour cruise', 'Historic old-town walk', 'Local food and market experience']),
    'norway': ('Norway combines fjords, Arctic landscapes, design-led cities and outdoor journeys across changing seasons.', ['Fjord cruise', 'Oslo or Bergen city walk', 'Scenic rail journey', 'Northern lights when seasonal']),
    'norwegian-fjords': ('The Norwegian fjords are a dramatic route of deep waterways, waterfalls, mountain villages and scenic viewpoints.', ['Fjord cruise', 'Waterfall viewpoint', 'Scenic rail journey', 'Guided mountain walk']),
    'arabian-gulf': ('The Arabian Gulf combines modern cities, desert landscapes, coastal resorts and distinctive regional heritage.', ['Desert excursion', 'Old-town or souk walk', 'Coastal boat trip', 'Museum and architecture tour']),
    'dubai-abu-dhabi': ('Dubai and Abu Dhabi pair modern city experiences, desert landscapes, museums, shopping and warm Gulf coast stays.', ['Burj Khalifa and Downtown', 'Desert safari', 'Sheikh Zayed Grand Mosque', 'Louvre Abu Dhabi']),
    'israel-and-jordan': ('Israel and Jordan connect layered history, Mediterranean coast, desert landscapes and iconic archaeological sites.', ['Jerusalem old city', 'Petra', 'Dead Sea', 'Wadi Rum']),
    'uae': ('The United Arab Emirates combines modern city breaks, desert scenery, museums, shopping and Gulf coast escapes.', ['Dubai city landmarks', 'Abu Dhabi mosque and museums', 'Desert safari', 'Souk and heritage visit']),
}


GENERIC_MARKERS = ('travel destination for', 'package destination', 'destination used for', 'destination served by')


class Command(BaseCommand):
    help = 'Refresh legacy destination guides with reviewed descriptions and activities.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write changes; otherwise preview only.')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        changed = []
        skipped = []
        with transaction.atomic():
            for slug, (description, activities) in LEGACY_GUIDES.items():
                destination = Destination.objects.filter(slug=slug, is_active=True).first()
                if not destination:
                    skipped.append(slug)
                    continue
                current_description = (destination.description or '').strip().lower()
                needs_refresh = not destination.things_to_do or not current_description or any(marker in current_description for marker in GENERIC_MARKERS)
                if not needs_refresh:
                    continue
                changed.append(slug)
                if apply_changes:
                    destination.description = description
                    destination.things_to_do = activities
                    destination.save(update_fields=['description', 'things_to_do', 'updated_at'])
            if not apply_changes:
                transaction.set_rollback(True)
        mode = 'Applied' if apply_changes else 'Preview'
        self.stdout.write(self.style.SUCCESS(f'{mode}: {len(changed)} destination guides'))
        if changed:
            self.stdout.write('  ' + ', '.join(changed))
        if skipped:
            self.stdout.write(self.style.WARNING('Missing records: ' + ', '.join(skipped)))
