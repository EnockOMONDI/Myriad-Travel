from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from adminside.models import Destination


# These are relationships that can be established from the existing names and
# package destinations without changing package ownership or deleting records.
COUNTRY_PARENTS = {
    "South Africa": "africa",
    "United States": "americas",
    "Thailand": "asia",
    "Indonesia": "asia",
    "Norway": "europe",
}

DESTINATION_PARENTS = {
    "Akagera National Park": ("Rwanda", Destination.PLACE),
    "Arusha": ("Tanzania", Destination.CITY),
    "Cairo": ("Egypt", Destination.CITY),
    "Cape Town": ("South Africa", Destination.CITY),
    "Dar es Salaam": ("Tanzania", Destination.CITY),
    "Johannesburg": ("South Africa", Destination.CITY),
    "Kibale Forest National Park": ("Uganda", Destination.PLACE),
    "Kigali": ("Rwanda", Destination.CITY),
    "Lake Manyara National Park": ("Tanzania", Destination.PLACE),
    "Matobo National Park": ("Zimbabwe", Destination.PLACE),
    "Mount Kilimanjaro National Park": ("Tanzania", Destination.PLACE),
    "Murchison Falls National Park": ("Uganda", Destination.PLACE),
    "Phuket": ("Thailand", Destination.PLACE),
    "Serengeti National Park": ("Tanzania", Destination.PLACE),
    "Tarangire National Park": ("Tanzania", Destination.PLACE),
    "Ubud Bali": ("Indonesia", Destination.PLACE),
    "Alaska": ("United States", Destination.PLACE),
    "Norwegian Fjords": ("Norway", Destination.PLACE),
    "07 Tsavo East • Watamu • Malindi": ("Kenya", Destination.PLACE),
    "Great Rift Valley": ("Kenya", Destination.CITY),
    "Masai Mara and Diani": ("Kenya", Destination.PLACE),
    "Masai Mara National Reserve": ("Kenya", Destination.PLACE),
    "Mombasa North Coast": ("Kenya", Destination.PLACE),
    "Mount Kenya": ("Kenya", Destination.PLACE),
    "Mount Kenya National Park": ("Kenya", Destination.PLACE),
    "Nairobi": ("Kenya", Destination.CITY),
    "Naivasha and Elementaita": ("Kenya", Destination.PLACE),
    "Samburu National Reserve": ("Kenya", Destination.PLACE),
    "Tsavo East National Park": ("Kenya", Destination.PLACE),
    "Maasai Mara National Reserve": ("Narok County", Destination.PLACE),
    "Diani Beach": ("Kwale County", Destination.PLACE),
    "Amboseli National Park": ("Kajiado County", Destination.PLACE),
    "Dubai": ("UAE", Destination.CITY),
}


class Command(BaseCommand):
    help = "Parent unambiguous flat destination records without deleting packages or destinations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the reviewed parent and type changes. Without this flag the command only previews them.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        created_countries = []
        changes = []
        skipped = []

        with transaction.atomic():
            parent_objects = {
                name: Destination.objects.filter(name=name).order_by('id').first()
                for name in set(COUNTRY_PARENTS) | {parent for parent, _type in DESTINATION_PARENTS.values()}
            }

            if apply_changes:
                for name, region in COUNTRY_PARENTS.items():
                    country = parent_objects.get(name)
                    if not country:
                        country = Destination.objects.create(
                            name=name,
                            slug=slugify(name),
                            destination_type=Destination.COUNTRY,
                            region=region,
                            description="",
                            is_active=True,
                        )
                        created_countries.append(country)
                    parent_objects[name] = country
            else:
                for name, region in COUNTRY_PARENTS.items():
                    if not parent_objects.get(name):
                        parent_objects[name] = Destination(
                            name=name,
                            region=region,
                            destination_type=Destination.COUNTRY,
                        )

            for name, (parent_name, destination_type) in DESTINATION_PARENTS.items():
                destination = Destination.objects.filter(name=name).first()
                parent = parent_objects.get(parent_name)
                if not destination or not parent:
                    skipped.append((name, parent_name, "missing destination or parent"))
                    continue
                if destination.parent_id == parent.id and destination.destination_type == destination_type and destination.region == parent.region:
                    continue
                changes.append((destination, parent, destination_type))
                if apply_changes:
                    destination.parent = parent
                    destination.destination_type = destination_type
                    destination.region = parent.region
                    destination.save(update_fields=["parent", "destination_type", "region", "updated_at"])

            if not apply_changes:
                transaction.set_rollback(True)

        mode = "Applied" if apply_changes else "Preview"
        self.stdout.write(self.style.SUCCESS(f"{mode}: {len(changes)} destination relationships"))
        if created_countries:
            self.stdout.write("Created country parents: " + ", ".join(country.name for country in created_countries))
        elif not apply_changes:
            missing = [name for name in COUNTRY_PARENTS if not Destination.objects.filter(name=name, destination_type=Destination.COUNTRY).exists()]
            if missing:
                self.stdout.write("Would create country parents: " + ", ".join(missing))
        for destination, parent, destination_type in changes:
            self.stdout.write(f"  {destination.name} -> {parent.name} ({destination_type})")
        if skipped:
            self.stdout.write(self.style.WARNING("Skipped:"))
            for name, parent_name, reason in skipped:
                self.stdout.write(f"  {name} -> {parent_name}: {reason}")
        self.stdout.write("Left unchanged because they span multiple countries: Caribbean, Mediterranean Europe, Arabian Gulf, Israel and Jordan.")
