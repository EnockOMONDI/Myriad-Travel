from django.core.management.base import BaseCommand

from adminside.models import Destination


DESTINATION_COPY = {
    "uae": "The UAE pairs world-class city skylines, desert landscapes, shopping and Gulf coast escapes across Dubai and Abu Dhabi.",
    "dubai": "Dubai combines skyline experiences, desert landscapes, shopping districts, family attractions and warm Gulf coast stays, with easy options for city breaks and longer UAE itineraries.",
    "zanzibar-island": "Zanzibar Island blends Stone Town heritage, spice routes, dhow sailing and clear-water beaches for a relaxed Indian Ocean escape.",
    "dubai-abu-dhabi": "Dubai and Abu Dhabi combine skyline landmarks, desert adventures, grand mosques, museums and Gulf coast leisure in one easy UAE journey.",
    "mediterranean-europe": "Mediterranean Europe brings together colourful coastal towns, historic cities, island waters and regional food across a relaxed multi-country route.",
    "arabian-gulf": "The Arabian Gulf offers a mix of modern city breaks, desert landscapes, cultural landmarks, warm-water shores and polished hospitality.",
    "alaska": "Alaska is a wilderness-led journey of glacier scenery, dramatic coastlines, wildlife and wide-open national park landscapes.",
    "caribbean": "The Caribbean offers warm-water island escapes with beaches, sailing, reef experiences, local food and relaxed coastal rhythms.",
    "norwegian-fjords": "Norway's fjords combine deep-water inlets, mountain scenery, scenic rail and coastal villages for a dramatic nature escape.",
    "phuket": "Phuket pairs Andaman beaches, island-hopping, Thai food, temples and lively coastal stays, with easy access to southern Thailand.",
    "ubud-bali": "Ubud is Bali's cultural and wellness heart, known for rice terraces, temples, craft traditions, forest landscapes and thoughtful retreats.",
    "johannesburg": "Johannesburg is a vibrant gateway to South Africa, combining urban culture, history, food and onward routes to the country's safari and coast.",
    "israel-and-jordan": "Israel and Jordan connect historic cities, sacred sites, desert landscapes and the Dead Sea in a rich Middle East journey.",
    "kigali": "Kigali is Rwanda's clean, welcoming capital and a thoughtful base for city culture, memorial history, coffee, and onward journeys to the country's parks and lakes.",
    "zambia": "Zambia offers intimate walking safaris, river wildlife, Victoria Falls and remote wilderness for travellers seeking a quieter African adventure.",
    "akagera-national-park": "Akagera is Rwanda's savannah park, where lakes, wetlands and open plains support game drives, birding and boat-based wildlife viewing.",
    "kibale-forest-national-park": "Kibale Forest is Uganda's primate capital, offering chimpanzee tracking, rainforest walks and rich birdlife near the crater-lake country.",
    "cairo": "Cairo is Egypt's energetic gateway to pharaonic history, Nile journeys, Islamic architecture, museums and the wider country.",
    "lake-manyara-national-park": "Lake Manyara is a compact Tanzania safari stop with groundwater forest, bird-rich wetlands, dramatic escarpment views and varied wildlife.",
    "matobo-national-park": "Matobo National Park is a Zimbabwe landscape of granite balancing rocks, ancient cultural sites, rhino tracking and striking sunset scenery.",
    "serengeti-national-park": "The Serengeti is Tanzania's vast savannah wilderness, renowned for big-cat sightings, year-round wildlife and the seasonal wildebeest movement.",
    "tarangire-national-park": "Tarangire is known for elephant herds, baobab-dotted plains, seasonal river wildlife and a quieter northern Tanzania safari rhythm.",
    "cape-town": "Cape Town brings together Table Mountain, coastal scenery, neighbourhood food, history and easy routes into the Winelands and wider South Africa.",
    "mount-kilimanjaro-national-park": "Mount Kilimanjaro National Park is the setting for Africa's highest mountain, with guided trekking routes, forest foothills and dramatic volcanic scenery.",
    "murchison-falls-national-park": "Murchison Falls is Uganda's largest national park, combining a powerful Nile cascade with savannah game drives and river wildlife cruises.",
    "arusha": "Arusha is Tanzania's safari gateway, linking city culture and coffee country with routes toward Kilimanjaro, Tarangire, Manyara and the Serengeti.",
    "dar-es-salaam": "Dar es Salaam is Tanzania's coastal gateway, combining Swahili city life, Indian Ocean islands and onward routes to southern Tanzania's parks.",
    "indonesia": "Indonesia is an archipelago of temples, rice landscapes, volcanic scenery, island beaches and rich regional cultures, with journeys shaped around each island.",
    "norway": "Norway combines fjords, northern light landscapes, coastal towns, scenic rail journeys and outdoor experiences across every season.",
}


class Command(BaseCommand):
    help = "Update public destination descriptions from the reviewed destination copy set."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show changes without saving them.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0
        missing = []
        for slug, description in DESTINATION_COPY.items():
            try:
                destination = Destination.objects.get(slug=slug)
            except Destination.DoesNotExist:
                missing.append(slug)
                continue
            if destination.description == description:
                continue
            self.stdout.write(f"{'Would update' if dry_run else 'Updating'} {destination.name} ({slug})")
            if not dry_run:
                destination.description = description
                destination.save(update_fields=["description", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"{'Would update' if dry_run else 'Updated'} {updated} destinations."))
        if missing:
            self.stdout.write(self.style.WARNING(f"Missing slugs: {', '.join(missing)}"))
