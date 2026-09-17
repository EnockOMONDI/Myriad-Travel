from django.core.management.base import BaseCommand
from django.utils.text import slugify
from adminside.models import Package, Itinerary, ItineraryDay, Destination

class Command(BaseCommand):
    help = 'Create sample itineraries for Multiday Bush Safaris, Nairobi Excursions, and Outbound Packages'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample itineraries...')

        # Get or create destinations
        kenya = Destination.objects.filter(name__icontains='kenya', destination_type='country').first()
        nairobi = Destination.objects.filter(name__icontains='nairobi', destination_type='city').first()
        masai_mara = Destination.objects.filter(name__icontains='masai mara').first()
        serengeti = Destination.objects.filter(name__icontains='serengeti').first()
        cape_town = Destination.objects.filter(name__icontains='cape town').first()

        # Sample itineraries data
        itineraries_data = {
            'multiday_bush_safari': {
                'title': '7-Day Ultimate Bush Safari Experience',
                'overview': 'Experience the raw beauty of East Africa with this comprehensive 7-day safari that takes you through Kenya\'s most iconic wildlife destinations. Witness the Great Migration, encounter the Big Five, and immerse yourself in Maasai culture.',
                'days': [
                    {
                        'day_number': 1,
                        'title': 'Arrival in Nairobi & Maasai Cultural Visit',
                        'description': 'Arrive at Jomo Kenyatta International Airport where you will be met by our representative. Transfer to your hotel in Nairobi for check-in and relaxation. In the afternoon, visit a Maasai village to learn about their traditional way of life, cultural dances, and customs. Enjoy a traditional Maasai meal before returning to Nairobi for your overnight stay.',
                        'destination': nairobi,
                        'breakfast': False,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 2,
                        'title': 'Maasai Mara Game Drive',
                        'description': 'After breakfast, fly to the Maasai Mara. Upon arrival, check into your luxury tented camp. Embark on your first game drive in the Maasai Mara, known for its abundant wildlife and the annual wildebeest migration. Look out for lions, elephants, zebras, and various antelope species. Return to camp for dinner and overnight.',
                        'destination': masai_mara,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 3,
                        'title': 'Full Day Maasai Mara Exploration',
                        'description': 'Spend the full day exploring the Maasai Mara. Early morning game drive to catch the sunrise and wildlife activity. Visit the Mara River where crocodiles wait for migrating wildebeest. Afternoon game drive focusing on different areas of the reserve. Optional hot air balloon safari available at extra cost.',
                        'destination': masai_mara,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 4,
                        'title': 'Maasai Mara to Serengeti',
                        'description': 'Morning game drive in Maasai Mara before crossing to Tanzania. Drive to the Isebania border, complete immigration formalities, and continue to Serengeti National Park. Arrive at your luxury lodge in the afternoon. Evening game drive to spot wildlife unique to the Serengeti ecosystem.',
                        'destination': serengeti,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 5,
                        'title': 'Serengeti Exploration',
                        'description': 'Full day exploring the vast Serengeti plains. The Serengeti is famous for its large lion prides, cheetah families, and the incredible diversity of wildlife. Visit different areas including the Seronera Valley and possibly the Moru Kopjes. Optional visit to a Maasai village in Tanzania.',
                        'destination': serengeti,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 6,
                        'title': 'Serengeti to Ngorongoro Crater',
                        'description': 'Morning game drive before departing for Ngorongoro Conservation Area. Descend into the Ngorongoro Crater for a full day crater tour. The crater is home to over 25,000 animals including the Big Five. Picnic lunch in the crater. Return to your lodge in the evening.',
                        'destination': serengeti,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 7,
                        'title': 'Departure from Arusha',
                        'description': 'Morning at leisure or optional activities. Transfer to Arusha Airport for your flight back home. Alternatively, extend your safari or connect to Zanzibar for beach relaxation.',
                        'destination': serengeti,
                        'breakfast': True,
                        'lunch': False,
                        'dinner': False
                    }
                ]
            },
            'nairobi_excursion': {
                'title': '2-Day Nairobi City Experience',
                'overview': 'Discover the vibrant capital of Kenya with this comprehensive 2-day excursion that combines urban exploration, wildlife encounters, and cultural experiences.',
                'days': [
                    {
                        'day_number': 1,
                        'title': 'Nairobi City Tour & National Park',
                        'description': 'Start your Nairobi adventure with a comprehensive city tour visiting key landmarks including the Parliament Buildings, Kenyatta International Conference Centre, and the University of Nairobi. Visit the Karen Blixen Museum and learn about Kenya\'s colonial history. In the afternoon, explore Nairobi National Park, Kenya\'s first national park located within city limits. Spot lions, giraffes, and other wildlife while enjoying views of the city skyline.',
                        'destination': nairobi,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 2,
                        'title': 'David Sheldrick Wildlife Trust & Departure',
                        'description': 'Morning visit to the David Sheldrick Wildlife Trust to witness the elephant orphanage and learn about wildlife conservation efforts. Visit the Giraffe Centre to feed and interact with Rothschild giraffes. Afternoon at leisure for shopping or optional activities. Transfer to the airport for your departure flight.',
                        'destination': nairobi,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': False
                    }
                ]
            },
            'outbound_package': {
                'title': 'Cape Town Adventure - 7 Days',
                'overview': 'Experience the stunning beauty of Cape Town with this comprehensive 7-day adventure that combines urban exploration, natural wonders, and South African culture.',
                'days': [
                    {
                        'day_number': 1,
                        'title': 'Arrival in Cape Town',
                        'description': 'Arrive at Cape Town International Airport. Transfer to your hotel in the city center. Afternoon at leisure to settle in and enjoy the beautiful surroundings. Optional Table Mountain cable car ride for panoramic views of the city and coastline.',
                        'destination': cape_town,
                        'breakfast': False,
                        'lunch': False,
                        'dinner': True
                    },
                    {
                        'day_number': 2,
                        'title': 'Cape Peninsula Tour',
                        'description': 'Full day tour of the Cape Peninsula including the Cape of Good Hope, Cape Point, and the historic Cape Point Lighthouse. Visit Boulders Beach to see the African penguin colony. Stop at Simon\'s Town and enjoy scenic coastal drives with stunning ocean views.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 3,
                        'title': 'Table Mountain & City Tour',
                        'description': 'Morning cable car ride up Table Mountain (weather permitting) for breathtaking views. Afternoon city tour including the Castle of Good Hope, District Six Museum, and the vibrant Bo-Kaap neighborhood. Visit the V&A Waterfront for shopping and entertainment.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 4,
                        'title': 'Stellenbosch Wine Route',
                        'description': 'Day trip to Stellenbosch, South Africa\'s oldest town and heart of the wine industry. Visit several wine estates for tastings and tours. Learn about the history of winemaking in the region and enjoy the beautiful Cape Dutch architecture.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 5,
                        'title': 'Whale Watching & Coastal Drive',
                        'description': 'Morning whale watching tour (seasonal) or coastal drive along Chapman\'s Peak. Visit the coastal towns of Hout Bay and Camps Bay. Afternoon visit to the Two Oceans Aquarium or relax on the beautiful beaches.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 6,
                        'title': 'Robben Island Tour',
                        'description': 'Full day tour to Robben Island, former prison island and UNESCO World Heritage Site. Take a ferry to the island and join a guided tour led by former political prisoners. Learn about Nelson Mandela\'s imprisonment and South Africa\'s struggle for freedom.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': True,
                        'dinner': True
                    },
                    {
                        'day_number': 7,
                        'title': 'Departure from Cape Town',
                        'description': 'Morning at leisure for last-minute shopping or relaxation. Transfer to Cape Town International Airport for your departure flight. Optional extension to safari destinations or other South African adventures.',
                        'destination': cape_town,
                        'breakfast': True,
                        'lunch': False,
                        'dinner': False
                    }
                ]
            }
        }

        # Create itineraries for matching packages
        packages_created = 0

        for package in Package.objects.filter(status='published'):
            package_name = package.name.lower()

            # Determine which itinerary to create based on package name
            itinerary_key = None
            if 'multiday' in package_name or 'bush safari' in package_name:
                itinerary_key = 'multiday_bush_safari'
            elif 'nairobi' in package_name and ('excursion' in package_name or 'city' in package_name or 'full day' in package_name):
                itinerary_key = 'nairobi_excursion'
            elif 'outbound' in package_name or 'cape town' in package_name:
                itinerary_key = 'outbound_package'

            if itinerary_key and not hasattr(package, 'itinerary'):
                itinerary_data = itineraries_data[itinerary_key]

                # Create itinerary
                itinerary = Itinerary.objects.create(
                    package=package,
                    title=itinerary_data['title'],
                    overview=itinerary_data['overview']
                )

                # Create itinerary days
                for day_data in itinerary_data['days']:
                    ItineraryDay.objects.create(
                        itinerary=itinerary,
                        day_number=day_data['day_number'],
                        title=day_data['title'],
                        description=day_data['description'],
                        destination=day_data['destination'],
                        breakfast=day_data['breakfast'],
                        lunch=day_data['lunch'],
                        dinner=day_data['dinner']
                    )

                packages_created += 1
                self.stdout.write(f'Created itinerary for: {package.name}')

        self.stdout.write(self.style.SUCCESS(f'Successfully created itineraries for {packages_created} packages'))
        self.stdout.write('Sample itineraries creation completed!')