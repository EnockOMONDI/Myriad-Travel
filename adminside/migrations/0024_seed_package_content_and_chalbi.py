from datetime import date, time

from django.db import migrations


PACKING_ITEMS = [
    'Closed shoes',
    'Hat or cap',
    'Sunglasses',
    'Sunscreen',
    'Warm jacket',
    'Comfortable clothing',
    'Swimwear and towel',
    'Refillable water bottle',
    'Power bank',
    'Toiletries',
    'Identification document',
    'Kenyan cash',
]


def seed_and_update_chalbi(apps, schema_editor):
    PackingListItem = apps.get_model('adminside', 'PackingListItem')
    Package = apps.get_model('adminside', 'Package')
    PackageDeparture = apps.get_model('adminside', 'PackageDeparture')
    Itinerary = apps.get_model('adminside', 'Itinerary')
    ItineraryDay = apps.get_model('adminside', 'ItineraryDay')

    for order, name in enumerate(PACKING_ITEMS, start=1):
        PackingListItem.objects.update_or_create(
            name=name,
            defaults={'display_order': order, 'is_active': True},
        )

    package = Package.objects.filter(slug='twende-chalbi-4-nights-5-days').first()
    if not package:
        return

    package.adult_price = 54500
    package.child_price = 43500
    package.single_occupancy_supplement = 5000
    package.meta_description = 'A 5-day, 4-night northern Kenya adventure from Nairobi through Marsabit, Chalbi Desert, North Horr, Lake Turkana and Isiolo.'
    package.meta_keywords = 'Chalbi Desert, Northern Kenya safari, Lake Turkana, Marsabit, North Horr, El Molo culture'
    package.aeo_summary = 'A 5-day northern Kenya road adventure from Nairobi to Marsabit, Chalbi Desert, Lake Turkana and Isiolo.'
    package.travel_notes = '\n'.join([
        'Expect tarmac, marram roads and desert tracks with long driving distances.',
        'Network coverage may be limited or unavailable in some sections.',
        'Northern Kenya can be hot during the day and cooler early and in the evening.',
        'Timings, stops and activities may change due to roads, weather, terrain and operational conditions.',
    ])
    package.inclusions = '<ul>' + ''.join(
        f'<li>{item}</li>' for item in [
            'Safari Land Cruiser transport',
            '4 nights accommodation',
            'Full-board meals from dinner on Day 1 to breakfast on Day 5',
            'Mineral water throughout',
            'Professional guides and experienced drivers',
            'Marsabit National Park and Lake Paradise experience',
            'Chalbi Desert experience',
            'North Horr Sand Dunes',
            'Lake Turkana Wind Power experience',
            'Swimming experience at Lake Turkana',
            'North Kenya boat ride',
            'El Molo community and cultural experience',
        ]
    ) + '</ul>'
    package.save(update_fields=[
        'adult_price', 'child_price', 'single_occupancy_supplement',
        'meta_description', 'meta_keywords', 'aeo_summary', 'travel_notes',
        'inclusions', 'updated_at',
    ])

    PackageDeparture.objects.update_or_create(
        package=package,
        starts_on=date(2026, 12, 10),
        ends_on=date(2026, 12, 14),
        defaults={
            'label': 'Twende Chalbi December 2026',
            'departure_location': 'Nairobi',
            'departure_time': time(3, 30),
            'return_location': 'Nairobi',
            'return_time_note': 'approximately 4:00–5:00 PM',
            'is_active': True,
            'display_order': 1,
        },
    )

    itinerary, _ = Itinerary.objects.get_or_create(
        package=package,
        defaults={
            'title': 'Twende Chalbi 5-Day Northern Kenya Circuit',
            'overview': 'A 5-day northern Kenya adventure from Nairobi through Marsabit, Chalbi Desert, North Horr, Lake Turkana and Isiolo.',
        },
    )
    itinerary.title = 'Twende Chalbi 5-Day Northern Kenya Circuit'
    itinerary.overview = 'A 5-day northern Kenya adventure from Nairobi through Marsabit, Chalbi Desert, North Horr, Lake Turkana and Isiolo.'
    itinerary.save(update_fields=['title', 'overview', 'updated_at'])

    days = [
        {
            'day_number': 1, 'date': date(2026, 12, 10), 'theme': 'Into the North',
            'route': 'Nairobi – Nanyuki – Samburu – Marsabit',
            'title': 'Nairobi to Marsabit',
            'summary': 'Equator stop, Samburu stopover, Mount Oloolokwe views and Marsabit National Park landscapes.',
            'description': 'Depart Nairobi early and travel north through Nanyuki and Samburu before continuing towards Marsabit. The route includes an Equator stop, views of Mount Oloolokwe and the crater lakes and forests of Marsabit National Park.',
            'main_activities': 'Equator stop\nSamburu stopover\nMount Oloolokwe viewpoint\nMarsabit National Park\nCrater lakes and forests',
            'optional_activities': '', 'overnight_location': 'Marsabit',
            'breakfast': False, 'lunch': True, 'dinner': True,
            'estimated_departure_time': time(3, 30), 'estimated_arrival_time': None,
            'operational_notes': 'Long driving day. Timing depends on road and traffic conditions.',
        },
        {
            'day_number': 2, 'date': date(2026, 12, 11), 'theme': 'Desert Days',
            'route': 'Marsabit – Chalbi Desert – North Horr',
            'title': 'Marsabit to North Horr via Chalbi Desert',
            'summary': 'Northern landscapes, Chalbi Desert and North Horr Sand Dunes at sunset.',
            'description': 'Travel across the dramatic northern landscapes into the Chalbi Desert and continue to North Horr. The day closes with a visit to the North Horr Sand Dunes around sunset.',
            'main_activities': 'Chalbi Desert experience\nVast white landscapes\nNorth Horr Sand Dunes\nSunset experience',
            'optional_activities': '', 'overnight_location': 'North Horr',
            'breakfast': True, 'lunch': True, 'dinner': True,
            'estimated_departure_time': None, 'estimated_arrival_time': None,
            'operational_notes': 'Desert tracks and long remote sections. Activity timing is weather and road dependent.',
        },
        {
            'day_number': 3, 'date': date(2026, 12, 12), 'theme': 'By the Jade Sea',
            'route': 'North Horr – Loiyangalani – Lake Turkana',
            'title': 'North Horr to Lake Turkana',
            'summary': 'Optional sunrise, boat experience, El Molo culture and lakeside time by the Jade Sea.',
            'description': 'Continue to Loiyangalani and Lake Turkana. The day includes a North Kenya boat ride, El Molo community and cultural experience, swimming and lakeside relaxation where conditions allow.',
            'main_activities': 'Loiyangalani journey\nNorth Kenya boat ride\nEl Molo community and cultural experience\nLakeside relaxation',
            'optional_activities': 'Sunrise experience\nSwimming at Lake Turkana', 'overnight_location': 'Lake Turkana / Loiyangalani',
            'breakfast': True, 'lunch': True, 'dinner': True,
            'estimated_departure_time': None, 'estimated_arrival_time': None,
            'operational_notes': 'Boat and swimming activities depend on local conditions and operator confirmation.',
        },
        {
            'day_number': 4, 'date': date(2026, 12, 13), 'theme': 'The Scenic Route',
            'route': 'Lake Turkana – Wind Power – Ngurunit – Isiolo',
            'title': 'Lake Turkana to Isiolo',
            'summary': 'Lake Turkana Wind Power landscape, Ngurunit and the route through Laisamis and Archers Post.',
            'description': 'Leave Lake Turkana and travel through the Wind Power landscape towards Ngurunit, Laisamis and Archers Post before continuing to Isiolo.',
            'main_activities': 'Lake Turkana Wind Power experience\nNgurunit landscape\nLaisamis\nArchers Post',
            'optional_activities': 'Natural sliding rocks at Ngurunit', 'overnight_location': 'Isiolo',
            'breakfast': True, 'lunch': True, 'dinner': True,
            'estimated_departure_time': None, 'estimated_arrival_time': None,
            'operational_notes': 'Long transfer day across mixed roads and remote terrain.',
        },
        {
            'day_number': 5, 'date': date(2026, 12, 14), 'theme': 'Home With Stories',
            'route': 'Isiolo – Nairobi',
            'title': 'Isiolo to Nairobi',
            'summary': 'Breakfast, check-out and the journey home to Nairobi.',
            'description': 'After breakfast, check out and depart Isiolo at approximately 9:30 AM. Continue to Nairobi, expected around 4:00–5:00 PM depending on road conditions.',
            'main_activities': 'Breakfast and check-out\nReturn journey to Nairobi',
            'optional_activities': '', 'overnight_location': '',
            'breakfast': True, 'lunch': False, 'dinner': False,
            'estimated_departure_time': time(9, 30), 'estimated_arrival_time': None,
            'operational_notes': 'Expected Nairobi arrival is approximately 4:00–5:00 PM.',
        },
    ]

    for values in days:
        day_number = values.pop('day_number')
        ItineraryDay.objects.update_or_create(
            itinerary=itinerary,
            day_number=day_number,
            defaults=values,
        )


def reverse_seed(apps, schema_editor):
    PackageDeparture = apps.get_model('adminside', 'PackageDeparture')
    PackageDeparture.objects.filter(
        package__slug='twende-chalbi-4-nights-5-days',
        starts_on=date(2026, 12, 10),
        ends_on=date(2026, 12, 14),
    ).delete()


class Migration(migrations.Migration):
    dependencies = [('adminside', '0023_packinglistitem_itineraryday_date_and_more')]
    operations = [migrations.RunPython(seed_and_update_chalbi, reverse_seed)]
