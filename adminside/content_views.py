from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import ContentSection, HeroSlider, HomepageExploreCard


DEFAULT_HERO_SLIDES = (
    ('Explore Kenya', 'images/hero/discover-kenya.webp', 'Elephants beneath Mount Kilimanjaro'),
    ('Explore The World', 'images/hero/beyond-imagination.webp', 'Turquoise island lagoon'),
    ('Tours & Safaris', 'images/hero/tours-safaris.webp', 'Safari vehicle at sunset'),
    ('Themed Experiences', 'images/hero/signature-tours.webp', 'Giraffes on open savannah'),
    ('Deals', 'images/hero/signature-tours.webp', 'Myriad Travel seasonal deal'),
)


HOMEPAGE_SECTIONS = (
    {
        'key': 'homepage-hero',
        'name': 'Homepage Hero',
        'description': 'The first message visitors see, including the carousel and primary button.',
        'icon': '✦',
        'editable': True,
        'url_name': 'admin_content:homepage_hero',
    },
    {
        'key': 'homepage-deals',
        'name': 'Homepage Deals',
        'description': 'The seasonal offer banner shown below the homepage hero.',
        'icon': '◆',
        'editable': True,
        'url_name': 'admin:adminside_contentsection_change',
    },
    {
        'key': 'homepage-explore-kenya',
        'name': 'Explore Kenya',
        'description': 'Kenya package discovery cards and supporting introduction.',
        'icon': '◎',
        'editable': True,
        'url_name': 'admin_content:homepage_explore_kenya',
    },
    {
        'key': 'homepage-explore-world',
        'name': 'Explore the World',
        'description': 'International region cards and the global discovery introduction.',
        'icon': '◌',
        'editable': True,
        'url_name': 'admin_content:homepage_explore_world',
    },
    {
        'key': 'homepage-campaigns',
        'name': 'Current Campaigns',
        'description': 'Live campaign cards selected from the Campaigns / Deals catalogue.',
        'icon': '◇',
        'editable': False,
    },
    {
        'key': 'homepage-services',
        'name': 'Services',
        'description': 'Myriad services and corporate travel introduction.',
        'icon': '＋',
        'editable': False,
    },
    {
        'key': 'homepage-testimonials',
        'name': 'Testimonials',
        'description': 'Verified traveller reviews shown on the homepage.',
        'icon': '♥',
        'editable': False,
    },
    {
        'key': 'homepage-accreditation',
        'name': 'Accreditations',
        'description': 'Partner authorities and trust marks shown near the footer.',
        'icon': '✓',
        'editable': False,
    },
)


class ContentSectionEditorForm(forms.ModelForm):
    class Meta:
        model = ContentSection
        fields = ('eyebrow', 'title', 'description', 'image', 'cta_text', 'cta_url')
        widgets = {
            'eyebrow': forms.TextInput(attrs={'maxlength': 120, 'placeholder': 'Small label above the heading'}),
            'title': forms.TextInput(attrs={'maxlength': 200, 'placeholder': 'Main heading'}),
            'description': forms.Textarea(attrs={'rows': 4, 'maxlength': 240, 'placeholder': 'One short supporting sentence'}),
            'cta_text': forms.TextInput(attrs={'maxlength': 80, 'placeholder': 'Button label'}),
            'cta_url': forms.TextInput(attrs={'maxlength': 300, 'placeholder': '/explore-kenya/'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eyebrow'].label = 'Small label'
        self.fields['title'].label = 'Main heading'
        self.fields['description'].label = 'Supporting description'
        self.fields['image'].label = 'Section image'
        self.fields['cta_text'].label = 'Button label'
        self.fields['cta_url'].label = 'Button destination'
        self.fields['eyebrow'].help_text = 'Optional. Example: Myriad Travel seasonal offer.'
        self.fields['title'].help_text = 'Keep the heading clear and easy to scan.'
        self.fields['description'].help_text = 'Optional. Keep this to one short sentence.'
        self.fields['image'].help_text = 'Optional Uploadcare replacement. The current static fallback remains live when this is empty.'
        self.fields['cta_url'].help_text = 'Use a Myriad page path such as /explore-kenya/ or /deals/.'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'content-input')


class HeroSlideEditorForm(forms.ModelForm):
    image_scaling = forms.ChoiceField(
        choices=(
            ('2048x768', 'Wide hero — recommended 2048 × 768'),
            ('16:9', 'Standard 16:9'),
            ('', 'Free form'),
        ),
        required=False,
        initial='2048x768',
        help_text='Keep important subjects away from the extreme edges for mobile crops.',
    )

    class Meta:
        model = HeroSlider
        fields = ('title', 'subtitle', 'image', 'cta_text', 'cta_url', 'is_active', 'order')
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 200}),
            'subtitle': forms.Textarea(attrs={'rows': 3, 'maxlength': 240}),
            'cta_text': forms.TextInput(attrs={'maxlength': 80}),
            'cta_url': forms.TextInput(attrs={'maxlength': 300}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Slide label'
        self.fields['subtitle'].label = 'Slide supporting text'
        self.fields['image'].label = 'Slide image'
        self.fields['is_active'].label = 'Show this slide'
        self.fields['order'].help_text = 'Lower numbers appear first.'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'content-input')


class ExploreKenyaCardEditorForm(forms.ModelForm):
    class Meta:
        model = HomepageExploreCard
        fields = ('name', 'description', 'image', 'url', 'action_label', 'display_order', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 120}),
            'description': forms.TextInput(attrs={'maxlength': 240}),
            'url': forms.TextInput(attrs={'maxlength': 300}),
            'action_label': forms.TextInput(attrs={'maxlength': 80}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Card title'
        self.fields['description'].label = 'Card description'
        self.fields['image'].label = 'Card image'
        self.fields['url'].label = 'Card destination'
        self.fields['action_label'].label = 'Card link label'
        self.fields['display_order'].label = 'Display order'
        self.fields['image'].help_text = 'Optional Uploadcare replacement. Recommended display size: 1200 × 800px. The static fallback stays live when empty.'
        self.fields['url'].help_text = 'Use a Myriad page path such as /kenyan-coast/ or /day-trips/.'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'content-input')


def _homepage_card_data():
    sections = {item.section_key: item for item in ContentSection.objects.all()}
    hero = sections.get('homepage-hero')
    deals = sections.get('homepage-deals')
    active_uploaded_slides = HeroSlider.objects.filter(
        section=hero, is_active=True,
    ).exclude(image='').count() if hero else 0

    cards = []
    for item in HOMEPAGE_SECTIONS:
        record = sections.get(item['key'])
        if item['key'] == 'homepage-hero':
            source = 'Database override' if active_uploaded_slides else 'Static default'
            detail = f'{len(DEFAULT_HERO_SLIDES)} static fallback slides remain available'
            if active_uploaded_slides:
                detail = f'{active_uploaded_slides} uploaded slide(s) currently active'
        elif item['key'] == 'homepage-deals':
            source = 'Mixed: database copy + static image' if record and not record.image else 'Database override'
            detail = 'Static fallback image remains live until an Uploadcare image is published' if record and not record.image else 'Uploadcare image override is active'
        elif item['key'] == 'homepage-explore-kenya':
            card_count = HomepageExploreCard.objects.filter(section=record, is_active=True).count() if record else 0
            source = 'Database cards' if card_count else 'Static default'
            detail = f'{card_count or 6} editable card(s) · static image fallback available'
        elif item['key'] == 'homepage-explore-world':
            card_count = HomepageExploreCard.objects.filter(section=record, is_active=True).count() if record else 0
            source = 'Database cards' if card_count else 'Static default'
            detail = f'{card_count or 6} editable card(s) · static image fallback available'
        else:
            source = 'Static default'
            detail = 'Structured editor planned; current public component remains unchanged'

        card = dict(item)
        card.update({
            'record': record,
            'source': source,
            'detail': detail,
            'status_class': 'source-db' if 'Database' in source else 'source-mixed' if 'Mixed' in source else 'source-static',
        })
        if item.get('editable'):
            if item['key'] == 'homepage-deals' and record:
                card['edit_url'] = reverse('admin:adminside_contentsection_change', args=(record.pk,))
            else:
                card['edit_url'] = reverse(item['url_name'])
        cards.append(card)
    return cards


@staff_member_required
def content_overview(request):
    return render(request, 'admin/content/overview.html', {
        'page_title': 'Website Content',
        'homepage_cards': _homepage_card_data(),
    })


@staff_member_required
def homepage_hero(request):
    section, _ = ContentSection.objects.get_or_create(
        section_key='homepage-hero',
        defaults={'name': 'Homepage Hero', 'title': 'Beyond Imagination', 'cta_text': 'Take Me There', 'cta_url': '/explore-kenya/'},
    )
    form = ContentSectionEditorForm(request.POST or None, request.FILES or None, instance=section)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Homepage Hero draft saved. The current static fallback remains safe until an uploaded slide is published.')
        return redirect('admin_content:homepage_hero')

    slides = HeroSlider.objects.filter(section=section).order_by('order', '-created_at')
    return render(request, 'admin/content/hero.html', {
        'page_title': 'Homepage Hero',
        'section': section,
        'form': form,
        'slides': slides,
        'default_slides': DEFAULT_HERO_SLIDES,
        'live_source': 'Database override' if slides.filter(is_active=True).exclude(image='').exists() else 'Static default',
        'overview_url': reverse('admin_content:content_overview'),
    })


@staff_member_required
def homepage_explore_kenya(request):
    section, _ = ContentSection.objects.get_or_create(
        section_key='homepage-explore-kenya',
        defaults={
            'name': 'Homepage Explore Kenya',
            'eyebrow': 'Explore Kenya',
            'title': 'Kenya, beyond the usual route',
            'description': 'Safari circuits, coastal stays, northern-frontier adventures and weekend escapes.',
            'is_active': True,
        },
    )
    cards = HomepageExploreCard.objects.filter(section=section).order_by('display_order', 'id')
    if request.method == 'POST':
        section_form = ContentSectionEditorForm(request.POST, request.FILES, instance=section, prefix='section')
        card_forms = [
            ExploreKenyaCardEditorForm(request.POST, request.FILES, instance=card, prefix=f'card-{card.pk}')
            for card in cards
        ]
        if section_form.is_valid() and all(card_form.is_valid() for card_form in card_forms):
            section_form.save()
            for card_form in card_forms:
                card_form.save()
            messages.success(request, 'Explore Kenya content saved. Empty image fields continue using the static fallback images.')
            return redirect('admin_content:homepage_explore_kenya')
    else:
        section_form = ContentSectionEditorForm(instance=section, prefix='section')
        card_forms = [
            ExploreKenyaCardEditorForm(instance=card, prefix=f'card-{card.pk}')
            for card in cards
        ]
    return render(request, 'admin/content/explore_kenya.html', {
        'page_title': 'Explore Kenya',
        'section': section,
        'section_form': section_form,
        'card_forms': zip(cards, card_forms),
        'overview_url': reverse('admin_content:content_overview'),
    })


@staff_member_required
def homepage_explore_world(request):
    section, _ = ContentSection.objects.get_or_create(
        section_key='homepage-explore-world',
        defaults={
            'name': 'Homepage Explore the World',
            'eyebrow': 'Explore The World',
            'title': 'Go further with Myriad',
            'description': 'City breaks, island holidays and carefully planned journeys beyond Kenya.',
            'is_active': True,
        },
    )
    cards = HomepageExploreCard.objects.filter(section=section).order_by('display_order', 'id')
    if request.method == 'POST':
        section_form = ContentSectionEditorForm(request.POST, request.FILES, instance=section, prefix='section')
        card_forms = [
            ExploreKenyaCardEditorForm(request.POST, request.FILES, instance=card, prefix=f'card-{card.pk}')
            for card in cards
        ]
        if section_form.is_valid() and all(card_form.is_valid() for card_form in card_forms):
            section_form.save()
            for card_form in card_forms:
                card_form.save()
            messages.success(request, 'Explore the World content saved. Empty image fields continue using the static fallback images.')
            return redirect('admin_content:homepage_explore_world')
    else:
        section_form = ContentSectionEditorForm(instance=section, prefix='section')
        card_forms = [
            ExploreKenyaCardEditorForm(instance=card, prefix=f'card-{card.pk}')
            for card in cards
        ]
    return render(request, 'admin/content/explore_world.html', {
        'page_title': 'Explore the World',
        'section': section,
        'section_form': section_form,
        'card_forms': zip(cards, card_forms),
        'overview_url': reverse('admin_content:content_overview'),
    })


@staff_member_required
def hero_slide_editor(request, pk=None):
    section = get_object_or_404(ContentSection, section_key='homepage-hero')
    slide = get_object_or_404(HeroSlider, pk=pk, section=section) if pk else HeroSlider(section=section)
    form = HeroSlideEditorForm(request.POST or None, request.FILES or None, instance=slide)
    if request.method == 'POST' and form.is_valid():
        slide = form.save(commit=False)
        slide.section = section
        slide.save()
        messages.success(request, 'Hero slide saved. It will replace the matching static fallback only when active and uploaded.')
        return redirect('admin_content:homepage_hero')
    return render(request, 'admin/content/hero_slide.html', {
        'page_title': 'Hero slide',
        'form': form,
        'slide': slide,
        'is_new': not bool(pk),
        'back_url': reverse('admin_content:homepage_hero'),
    })
