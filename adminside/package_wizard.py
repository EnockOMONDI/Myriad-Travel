from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .models import Accommodation, Destination, Package, PackageCategory, TravelCollection, TravelMode


WIZARD_SESSION_KEY = "adminside_package_wizard"
STEP_TITLES = {
    1: ("Basics", "Name the package and choose the exact destination."),
    2: ("Placement", "Choose the existing collections and travel categories."),
    3: ("Content and price", "Add the public description, inclusions, and pricing."),
    4: ("Options and publish", "Add accommodation, travel options, media, and visibility."),
}


class DestinationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        parts = []
        current = obj
        while current:
            parts.append(current.name)
            current = current.parent
        return " > ".join(reversed(parts))


class PackageBasicsForm(forms.Form):
    name = forms.CharField(max_length=200, label="Package name")
    subtitle = forms.CharField(
        max_length=280,
        required=False,
        label="Short card description",
        help_text="A short sentence shown on package cards.",
        widget=forms.TextInput(attrs={"placeholder": "For example: A relaxed four-day safari for first-time visitors."}),
    )
    main_destination = DestinationChoiceField(
        queryset=Destination.objects.none(),
        label="Main destination",
        help_text="Choose the most specific existing destination. The country and region will be inherited from it.",
    )
    duration_days = forms.IntegerField(min_value=1, label="Duration in days")
    duration_nights = forms.IntegerField(min_value=0, label="Duration in nights")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["main_destination"].queryset = Destination.objects.filter(is_active=True).select_related("parent").order_by("name")


class DestinationQuickCreateForm(forms.Form):
    """Create the missing geographic record without leaving package creation."""

    name = forms.CharField(
        max_length=200,
        label="Destination name",
        widget=forms.TextInput(attrs={"placeholder": "For example: Lake Nakuru National Park"}),
    )
    destination_type = forms.ChoiceField(
        choices=Destination.DESTINATION_TYPES,
        label="What kind of place is this?",
        help_text="Country is the top level. City is a town or wider area. Place is a specific park, beach, or attraction.",
    )
    region = forms.ChoiceField(
        choices=[("", "Choose a region")] + list(Destination.REGION_CHOICES),
        label="Region",
        help_text="This places the new record in the public Explore the World structure.",
    )
    parent = forms.ModelChoiceField(
        queryset=Destination.objects.none(),
        required=False,
        label="Parent place",
        help_text="Choose the country for a city, or the city for a specific place. Leave blank for a country.",
    )
    description = forms.CharField(
        required=False,
        label="Short description",
        help_text="Optional for now. The public destination page can be completed later.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "What should travellers know about this place?"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Destination.objects.filter(is_active=True).order_by("destination_type", "name")

    def clean(self):
        cleaned = super().clean()
        destination_type = cleaned.get("destination_type")
        parent = cleaned.get("parent")
        if destination_type == Destination.COUNTRY and parent:
            self.add_error("parent", "Countries sit at the top level, so they cannot have a parent.")
        elif destination_type == Destination.CITY and (not parent or parent.destination_type != Destination.COUNTRY):
            self.add_error("parent", "A city must belong to an existing country.")
        elif destination_type == Destination.PLACE and (
            not parent or parent.destination_type not in {Destination.CITY, Destination.COUNTRY}
        ):
            self.add_error("parent", "A specific place must belong to an existing country or city.")

        name = cleaned.get("name")
        if name:
            slug = slugify(name)
            if Destination.objects.filter(slug=slug).exists():
                self.add_error("name", "A destination with this name already exists. Choose it from the package form.")
        return cleaned


class PackagePlacementForm(forms.Form):
    legacy_collection = forms.ChoiceField(
        choices=Package.REGION_CHOICES,
        label="Main package collection",
        help_text="This is the existing public collection grouping, not a geographic region.",
    )
    travel_collections = forms.ModelMultipleChoiceField(
        queryset=TravelCollection.objects.none(),
        required=False,
        label="Additional collections",
        help_text="A package can appear in more than one existing collection. Leave blank if the collection list has not been set up yet.",
        widget=forms.CheckboxSelectMultiple,
    )
    category = forms.ModelChoiceField(
        queryset=PackageCategory.objects.none(),
        required=False,
        label="Main category",
        help_text="The main travel style shown on the package card.",
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=PackageCategory.objects.none(),
        required=False,
        label="Additional categories",
        help_text="Add other existing categories that should help visitors find this package.",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        collections = TravelCollection.objects.filter(is_active=True).order_by("section", "display_order", "name")
        categories = PackageCategory.objects.filter(is_active=True).order_by("display_order", "name")
        self.fields["travel_collections"].queryset = collections
        self.fields["category"].queryset = categories
        self.fields["categories"].queryset = categories


class PackageContentForm(forms.Form):
    description = forms.CharField(
        label="Public package description",
        help_text="Write for a traveller: what the trip feels like, what they will do, and who it suits.",
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    highlights = forms.CharField(
        required=False,
        label="Highlights",
        help_text="One highlight per line. These appear on package cards and detail pages.",
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Game drives\nComfortable transport\nFlexible group options"}),
    )
    inclusions = forms.CharField(
        required=False,
        label="What is included",
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    exclusions = forms.CharField(
        required=False,
        label="What is not included",
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    adult_price = forms.IntegerField(min_value=0, label="Adult price", help_text="Use the package currency configured by Myriad.")
    child_price = forms.IntegerField(min_value=0, label="Child price")
    lipa_pole_pole = forms.BooleanField(required=False, label="Offer Lipa Pole Pole")
    lipa_pole_pole_months = forms.IntegerField(min_value=1, required=False, initial=4, label="Installment months")


class PackageOptionsForm(forms.Form):
    available_accommodations = forms.ModelMultipleChoiceField(
        queryset=Accommodation.objects.none(),
        required=False,
        label="Available accommodation",
        help_text="Select the hotels, lodges, resorts, or guest houses that can be offered with this package.",
        widget=forms.CheckboxSelectMultiple,
    )
    available_travel_modes = forms.ModelMultipleChoiceField(
        queryset=TravelMode.objects.none(),
        required=False,
        label="Available travel options",
        help_text="Select the existing flights, charter flights, vehicles, boats, trains, tour vans, cruise ships, or 4x4 cruisers available for this package.",
        widget=forms.CheckboxSelectMultiple,
    )
    featured_image = forms.ImageField(required=False, label="Featured image", help_text="Use a clear image that represents this trip.")
    status = forms.ChoiceField(choices=Package.STATUS_CHOICES, initial=Package.DRAFT, label="Publishing status")
    is_featured = forms.BooleanField(required=False, label="Feature this package")
    home_rank = forms.IntegerField(min_value=0, initial=100, label="Homepage order", help_text="Lower numbers appear first.")
    meta_title = forms.CharField(max_length=200, required=False, label="Search title")
    meta_description = forms.CharField(max_length=300, required=False, label="Search description", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, destination_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        accommodations = Accommodation.objects.filter(is_active=True).select_related("destination").order_by("name")
        if destination_id:
            destination = Destination.objects.filter(pk=destination_id, is_active=True).first()
            if destination:
                destination_ids = [destination.pk] + [child.pk for child in destination.get_all_children()]
                accommodations = accommodations.filter(destination_id__in=destination_ids)
        self.fields["available_accommodations"].queryset = accommodations
        self.fields["available_travel_modes"].queryset = TravelMode.objects.filter(is_active=True).order_by("transport_type", "name")


FORM_CLASSES = {
    1: PackageBasicsForm,
    2: PackagePlacementForm,
    3: PackageContentForm,
    4: PackageOptionsForm,
}


def _json_safe(value):
    if hasattr(value, "pk"):
        return value.pk
    if hasattr(value, "values_list"):
        return list(value.values_list("pk", flat=True))
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _initial_for_step(step, saved):
    initial = dict(saved.get(str(step), {}))
    for field in ("travel_collections", "categories", "available_accommodations", "available_travel_modes"):
        if field in initial:
            initial[field] = initial[field]
    return initial


def _destination_path(destination):
    if not destination:
        return "Not selected"
    parts = []
    current = destination
    while current:
        parts.append(current.name)
        current = current.parent
    return " > ".join(reversed(parts))


@staff_member_required
def package_wizard(request):
    """Guided package creation using the existing Package model and relationships."""
    try:
        step = int(request.GET.get("step", request.POST.get("step", 1)))
    except (TypeError, ValueError):
        step = 1
    step = max(1, min(step, 4))

    saved = request.session.get(WIZARD_SESSION_KEY, {})
    if step > 1 and not saved.get("1"):
        return redirect(f"{reverse('adminside:package_wizard')}?step=1")

    create_destination = request.GET.get("create_destination") == "1" or request.POST.get("action") == "create_destination"
    destination_form = DestinationQuickCreateForm(
        request.POST or None if request.POST.get("action") == "create_destination" else None
    )
    if request.method == "POST" and request.POST.get("action") == "create_destination":
        if destination_form.is_valid():
            destination = Destination.objects.create(
                name=destination_form.cleaned_data["name"],
                slug=slugify(destination_form.cleaned_data["name"]),
                destination_type=destination_form.cleaned_data["destination_type"],
                region=destination_form.cleaned_data["region"],
                parent=destination_form.cleaned_data["parent"],
                description=destination_form.cleaned_data.get("description", ""),
                is_active=True,
            )
            messages.success(request, f"{destination.name} was added. It is ready to use for this package.")
            return redirect(f"{reverse('adminside:package_wizard')}?step=1&destination_id={destination.pk}")
        create_destination = True

    form_class = FORM_CLASSES[step]
    if request.method == "POST" and request.POST.get("direction") == "back":
        return redirect(f"{reverse('adminside:package_wizard')}?step={max(1, step - 1)}")

    form_kwargs = {}
    if step == 4:
        form_kwargs["destination_id"] = saved.get("1", {}).get("main_destination")
    initial = _initial_for_step(step, saved)
    if step == 1 and request.GET.get("destination_id") and request.method == "GET":
        initial["main_destination"] = request.GET["destination_id"]
    form = form_class(
        request.POST or None,
        request.FILES or None,
        initial=initial,
        **form_kwargs,
    )
    if request.method == "POST" and form.is_valid():
        cleaned = {key: _json_safe(value) for key, value in form.cleaned_data.items()}
        if step < 4:
            saved[str(step)] = cleaned
            request.session[WIZARD_SESSION_KEY] = saved
            request.session.modified = True
            return redirect(f"{reverse('adminside:package_wizard')}?step={step + 1}")

        _save_package(saved, form.cleaned_data)
        request.session.pop(WIZARD_SESSION_KEY, None)
        messages.success(request, "Package created as a draft. Review it before publishing.")
        return redirect("admin:adminside_package_changelist")

    destination = None
    if saved.get("1", {}).get("main_destination"):
        destination = Destination.objects.filter(pk=saved["1"]["main_destination"]).first()

    context = {
        "form": form,
        "step": step,
        "steps": [(number, title) for number, (title, _description) in STEP_TITLES.items()],
        "step_title": STEP_TITLES[step][0],
        "step_description": STEP_TITLES[step][1],
        "destination_path": _destination_path(destination),
        "saved": saved,
        "page_title": "Add package",
        "destination_form": destination_form,
        "create_destination": create_destination and step == 1,
        "accommodation_count": form.fields["available_accommodations"].queryset.count() if step == 4 else 0,
        "travel_mode_count": form.fields["available_travel_modes"].queryset.count() if step == 4 else 0,
    }
    return render(request, "adminside/package_wizard.html", context)


@transaction.atomic
def _save_package(saved, options):
    basics = saved.get("1", {})
    placement = saved.get("2", {})
    content = saved.get("3", {})
    package = Package.objects.create(
        name=basics["name"],
        subtitle=basics.get("subtitle", ""),
        main_destination_id=basics["main_destination"],
        duration_days=basics["duration_days"],
        duration_nights=basics["duration_nights"],
        region=placement.get("legacy_collection", Package.REGION_CHOICES[0][0]),
        category_id=placement.get("category") or None,
        description=content.get("description", ""),
        highlights=content.get("highlights", ""),
        inclusions=content.get("inclusions", ""),
        exclusions=content.get("exclusions", ""),
        adult_price=content["adult_price"],
        child_price=content["child_price"],
        lipa_pole_pole=content.get("lipa_pole_pole", False),
        lipa_pole_pole_months=content.get("lipa_pole_pole_months") or 4,
        featured_image=options.get("featured_image"),
        status=options.get("status", Package.DRAFT),
        is_featured=options.get("is_featured", False),
        home_rank=options.get("home_rank", 100),
        meta_title=options.get("meta_title", ""),
        meta_description=options.get("meta_description", ""),
        published_at=timezone.now() if options.get("status") == Package.PUBLISHED else None,
    )
    package.categories.set(placement.get("categories", []))
    package.available_accommodations.set(options.get("available_accommodations", []))
    package.available_travel_modes.set(options.get("available_travel_modes", []))

    for collection_id in placement.get("travel_collections", []):
        collection = TravelCollection.objects.filter(pk=collection_id, is_active=True).first()
        if collection:
            collection.packages.add(package)

    return package
