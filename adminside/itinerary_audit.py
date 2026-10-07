"""Read-only itinerary interpretation used by public pages and Django admin."""

import re

from django.utils.html import strip_tags


DAY_TITLE_RE = re.compile(
    r"^\s*day\s*(?P<start>\d+)(?:\s*(?:-|–|to)\s*(?:day\s*)?(?P<end>\d+))?\s*[:\-–]?\s*",
    re.IGNORECASE,
)
DESCRIPTION_RANGE_RE = re.compile(
    r"(?P<prefix>.*?)(?:days?\s*(?P<start>\d+)\s*(?:-|–|to)\s*(?P<end>\d+)\s*:\s*)(?P<body>.+)",
    re.IGNORECASE | re.DOTALL,
)


def _plain(value):
    return ' '.join(strip_tags(str(value or '')).split())


def _title_details(title, fallback_day):
    title = _plain(title)
    match = DAY_TITLE_RE.match(title)
    if not match:
        return fallback_day, fallback_day, f'Day {fallback_day}', title

    start = int(match.group('start'))
    end = int(match.group('end') or start)
    label = f'Day {start}' if start == end else f'Days {start}-{end}'
    return start, end, label, title[match.end():].strip()


def analyse_itinerary(package):
    """Return presentation rows and a transparent data-quality assessment.

    The function never rewrites itinerary records. It only exposes explicit day
    ranges already present in titles or descriptions.
    """
    try:
        raw_days = list(package.itinerary.days.all().order_by('day_number'))
    except Exception:
        raw_days = []

    if not raw_days:
        return {
            'status': 'needs-review',
            'label': 'Needs itinerary content',
            'details': 'No itinerary days have been added.',
            'rows': [],
        }

    rows = []
    covered_days = set()
    issues = []
    grouped = False

    for day in raw_days:
        start, end, label, cleaned_title = _title_details(day.title, day.day_number)
        if day.day_number != start:
            issues.append(
                f'Record {day.day_number} is titled {label}; review the stored day number.'
            )
        if end > start:
            grouped = True
        covered_days.update(range(start, end + 1))

        description = _plain(day.description)
        range_match = DESCRIPTION_RANGE_RE.search(description)
        if range_match:
            embedded_start = int(range_match.group('start'))
            embedded_end = int(range_match.group('end'))
            if embedded_end >= embedded_start:
                grouped = True
                covered_days.update(range(embedded_start, embedded_end + 1))
                before = range_match.group('prefix').strip()
                if before:
                    rows.append({
                        'label': label,
                        'title': cleaned_title,
                        'description': before,
                        'meals': _meals(day),
                        'stay': _stay(day),
                    })
                rows.append({
                    'label': f'Days {embedded_start}-{embedded_end}',
                    'title': '',
                    'description': range_match.group('body').strip(),
                    'meals': '',
                    'stay': '',
                })
                continue

        rows.append({
            'label': label,
            'title': cleaned_title,
            'description': description,
            'meals': _meals(day),
            'stay': _stay(day),
        })

    expected_days = set(range(1, package.duration_days + 1))
    missing_days = sorted(expected_days - covered_days)
    extra_days = sorted(covered_days - expected_days)
    if missing_days:
        issues.append('Missing coverage for ' + ', '.join(f'Day {number}' for number in missing_days) + '.')
    if extra_days:
        issues.append('Contains itinerary days beyond the sold duration.')

    if issues:
        status = 'needs-review'
        label = 'Needs itinerary review'
    elif grouped:
        status = 'grouped'
        label = 'Grouped itinerary'
    else:
        status = 'complete'
        label = 'Day-by-day complete'

    details = ' '.join(dict.fromkeys(issues))
    if not details and grouped:
        details = 'This package uses explicit multi-day itinerary ranges.'
    if not details:
        details = 'Each sold day is represented by a separate itinerary entry.'

    return {
        'status': status,
        'label': label,
        'details': details,
        'rows': rows,
    }


def _meals(day):
    return ', '.join(label for enabled, label in [
        (day.breakfast, 'Breakfast'),
        (day.lunch, 'Lunch'),
        (day.dinner, 'Dinner'),
    ] if enabled)


def _stay(day):
    return day.accommodation.name if day.accommodation else ''
