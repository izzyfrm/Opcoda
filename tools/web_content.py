"""Content pools for the web curriculum: businesses, palettes, people, places.

All text is original. Variety here is what stops Coda from memorising pages: every page
mixes a business, palette, font, layout and section set chosen at random.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    key: str
    desc: str
    dark: bool
    bg: str
    surface: str
    text: str
    muted: str
    primary: str
    on_primary: str
    border: str
    accent: str


PALETTES = [
    Palette("espresso", "warm cream and coffee-brown colors", False, "#fbf7f2", "#ffffff", "#2b211b", "#6f5f55", "#7a4a2a", "#ffffff", "#eadfd4", "#c98a4b"),
    Palette("ocean", "a clean white and ocean-blue color scheme", False, "#f7fafc", "#ffffff", "#1a2433", "#5a6b7f", "#1d6fd8", "#ffffff", "#dde5ee", "#14b8a6"),
    Palette("forest", "fresh greens", False, "#f6faf6", "#ffffff", "#1d2b20", "#5c6f60", "#2f7d4f", "#ffffff", "#dbe8dc", "#a3c76d"),
    Palette("sunset", "a dark theme with orange accents", True, "#14110f", "#1f1a17", "#f5eee8", "#b7a99d", "#f97316", "#1a0f05", "#3a302a", "#facc15"),
    Palette("midnight", "a dark navy theme with cyan accents", True, "#0b1020", "#131a2e", "#e6ecff", "#9aa7c7", "#22d3ee", "#04121a", "#24304d", "#a78bfa"),
    Palette("rose", "soft pink and rose tones", False, "#fff7f8", "#ffffff", "#2d1b20", "#7a5c64", "#e11d48", "#ffffff", "#f6dde3", "#fb7185"),
    Palette("slate", "a neutral gray look", False, "#f8f9fa", "#ffffff", "#1f2328", "#5f6670", "#24292f", "#ffffff", "#e1e4e8", "#0969da"),
    Palette("charcoal", "a dark charcoal theme with lime accents", True, "#111312", "#1a1d1b", "#eef2ee", "#a3aca5", "#a3e635", "#121a06", "#2c312d", "#4ade80"),
    Palette("lemon", "bright yellow and black", False, "#fffdf2", "#ffffff", "#1c1a10", "#6b6650", "#1c1a10", "#fde047", "#efe9c9", "#eab308"),
    Palette("berry", "a dark purple theme", True, "#140f1c", "#1e1729", "#f1ecf8", "#b2a6c4", "#c084fc", "#1a0b2e", "#342a45", "#f472b6"),
    Palette("sand", "sandy beige with teal accents", False, "#faf6ef", "#fffdf9", "#2a2620", "#706756", "#0f766e", "#ffffff", "#ebe3d4", "#d97706"),
    Palette("mint", "mint green and white", False, "#f3fbf8", "#ffffff", "#163028", "#567a6e", "#0d9488", "#ffffff", "#d3ece4", "#34d399"),
    Palette("ink", "a black and white theme", True, "#0a0a0a", "#161616", "#f5f5f5", "#a3a3a3", "#ffffff", "#0a0a0a", "#2a2a2a", "#e5e5e5"),
    Palette("sky", "light sky blue", False, "#f4f9ff", "#ffffff", "#132238", "#55657d", "#0284c7", "#ffffff", "#d6e6f5", "#f59e0b"),
]

FONTS = [
    ('system-ui, -apple-system, "Segoe UI", Roboto, sans-serif', "a clean sans-serif font"),
    ('Georgia, "Times New Roman", serif', "a classic serif font"),
    ('"Helvetica Neue", Arial, sans-serif', "Helvetica"),
    ('"Trebuchet MS", Verdana, sans-serif', "a friendly rounded font"),
    ('Inter, system-ui, sans-serif', "the Inter font"),
]

CITIES = ["Portland", "Austin", "Denver", "Chicago", "Seattle", "Boston", "Miami", "Atlanta", "Nashville", "Phoenix",
          "San Diego", "Minneapolis", "Toronto", "Vancouver", "London", "Dublin", "Melbourne", "Brooklyn", "Oakland",
          "Pittsburgh", "Raleigh", "Salt Lake City", "Madison", "Tucson", "Savannah"]

FIRST_NAMES = ["Ava", "Liam", "Maya", "Noah", "Zoe", "Ethan", "Lena", "Omar", "Ivy", "Lucas", "Nora", "Kai", "Elena",
               "Theo", "Ruby", "Mateo", "Hana", "Leo", "Sofia", "Jonah", "Amara", "Felix", "Iris", "Diego", "Clara",
               "Ravi", "Mila", "Owen", "Priya", "Sam"]
LAST_NAMES = ["Rivera", "Chen", "Patel", "Okafor", "Novak", "Kim", "Garcia", "Larsen", "Haddad", "Moreau", "Silva",
              "Tanaka", "Brooks", "Ward", "Ito", "Kowalski", "Mensah", "Reyes", "Fischer", "Nguyen", "Hughes", "Costa",
              "Byrne", "Shah", "Lopez"]

TESTIMONIALS = [
    "Easily the best {kind} in {city}. I recommend it to everyone.",
    "Friendly people, great service, and fair prices. I'll be back.",
    "I've tried a lot of places, but {name} is the one I keep coming back to.",
    "Everything was ready on time and better than I expected.",
    "The team at {name} made the whole thing easy. Five stars.",
    "Great value and even better people.",
]

GENERIC_FEATURES = [
    ("Friendly team", "Real people who are happy to help with anything you need."),
    ("Fair prices", "Clear pricing with no surprise fees, ever."),
    ("Book online", "Pick a time that suits you in under a minute."),
    ("Open late", "We stay open until 9pm on weekdays."),
    ("Locally owned", "Proudly run by people who live in the neighborhood."),
    ("Satisfaction guaranteed", "Not happy? We will make it right."),
    ("Fast service", "Most requests are handled the same day."),
    ("Years of experience", "Over a decade of doing this one thing well."),
]

# kind -> content. "generic": uses GENERIC_FEATURES and made-up names.
BUSINESSES: dict[str, dict] = {
    "coffee shop": {
        "names": ["Bean & Brew", "Copper Cup", "Morning Ritual", "Roast House", "Daily Grind", "Little Owl Coffee"],
        "taglines": ["Small-batch coffee roasted every morning.", "Your neighborhood spot for great coffee.", "Good coffee, good people, every day."],
        "features": [("Fresh roasts", "Every bean is roasted in small batches each week."), ("Cozy space", "Plenty of seats, fast Wi-Fi and good music."),
                     ("Order ahead", "Skip the line by ordering from your phone."), ("Local pastries", "Croissants and muffins from the bakery next door."),
                     ("Plant milks included", "Oat, almond and soy at no extra cost."), ("Brewing classes", "Learn pour-over at our Saturday workshops.")],
        "products": [("Espresso", 3.0), ("Flat white", 4.5), ("Cold brew", 4.0), ("Chai latte", 4.75), ("Mocha", 5.0), ("Cortado", 3.75)],
        "cta": ["Order ahead", "See the menu", "Visit us"],
        "nav": ["Menu", "About", "Locations", "Contact"],
        "food": True,
    },
    "bakery": {
        "names": ["Northwind Bakery", "Golden Crust", "Flour & Salt", "Sweet Rise", "The Rolling Pin"],
        "taglines": ["Bread baked fresh before sunrise.", "Pastries, cakes and loaves made by hand.", "Real butter, real flour, no shortcuts."],
        "features": [("Baked daily", "Everything on the shelf was made this morning."), ("Custom cakes", "Birthday and wedding cakes made to order."),
                     ("Sourdough", "Our starter is over ten years old."), ("Gluten-free options", "A dedicated gluten-free shelf every day."),
                     ("Catering", "Trays of pastries for offices and events."), ("Pre-order", "Reserve your loaf online and pick it up warm.")],
        "products": [("Sourdough loaf", 7.0), ("Croissant", 3.5), ("Cinnamon roll", 4.25), ("Baguette", 4.0), ("Lemon tart", 5.5), ("Chocolate cake slice", 6.0)],
        "cta": ["Order a cake", "See today's bakes", "Pre-order now"],
        "nav": ["Breads", "Cakes", "About", "Contact"],
        "food": True,
    },
    "gym": {
        "names": ["Iron Peak Gym", "Pulse Fitness", "Forge Athletics", "Summit Strength", "Core Club"],
        "taglines": ["Get stronger with coaches who care.", "Training for every level, open 24/7.", "Your goals, our plan."],
        "features": [("Personal training", "One-on-one sessions built around your goals."), ("Group classes", "HIIT, spin and yoga every day."),
                     ("Open 24/7", "Train whenever it fits your schedule."), ("Free first week", "Try everything before you commit."),
                     ("Modern equipment", "Racks, rowers and free weights for everyone."), ("Nutrition coaching", "Simple meal plans that actually work.")],
        "products": [("Day pass", 15.0), ("Monthly membership", 49.0), ("10-class pack", 120.0), ("Personal session", 60.0)],
        "cta": ["Start free trial", "Join today", "Book a tour"],
        "nav": ["Classes", "Coaches", "Pricing", "Contact"],
    },
    "bookstore": {
        "names": ["Harbor Books", "The Reading Room", "Paper Lantern Books", "Chapter One", "Inkwell & Co."],
        "taglines": ["New releases, used gems, and great recommendations.", "An independent bookstore since 1998.", "Find your next favorite book."],
        "features": [("Staff picks", "Handwritten recommendations on every shelf."), ("Book clubs", "Three clubs meet here every month."),
                     ("Used books", "Trade in your old books for store credit."), ("Kids corner", "Story time every Saturday at 10am."),
                     ("Special orders", "We can get almost any book in two days."), ("Author events", "Readings and signings all year.")],
        "products": [("Paperback", 14.0), ("Hardcover", 28.0), ("Gift card", 25.0), ("Tote bag", 18.0)],
        "cta": ["Browse books", "Join a book club", "See events"],
        "nav": ["Books", "Events", "Clubs", "Contact"],
    },
    "florist": {
        "names": ["Bloom & Stem", "Wild Petal", "The Flower Cart", "Garden Gate Florals", "Fern & Fig"],
        "taglines": ["Fresh flowers for every moment.", "Bouquets arranged by hand, delivered the same day.", "Seasonal flowers, beautifully arranged."],
        "features": [("Same-day delivery", "Order before noon for delivery today."), ("Wedding flowers", "Bouquets and centerpieces for your big day."),
                     ("Weekly subscription", "Fresh flowers at your door every week."), ("Locally grown", "Most stems come from farms nearby."),
                     ("Plant care", "Free advice for keeping your plants happy."), ("Custom bouquets", "Tell us the mood and we'll design it.")],
        "products": [("Seasonal bouquet", 45.0), ("Single rose", 6.0), ("Potted orchid", 38.0), ("Weekly subscription", 30.0)],
        "cta": ["Send flowers", "Shop bouquets", "Plan a wedding"],
        "nav": ["Shop", "Weddings", "Subscriptions", "Contact"],
    },
    "photography studio": {
        "names": ["Pixel Studio", "Golden Hour Photo", "Frame & Light", "Northlight Studio", "Shutter House"],
        "taglines": ["Portraits, weddings and brand photos.", "Photos you will want to keep forever.", "Natural light, honest moments."],
        "features": [("Portraits", "Relaxed sessions in the studio or outdoors."), ("Weddings", "Full-day coverage with two photographers."),
                     ("Brand photos", "Product and team photos for your website."), ("Fast delivery", "Edited photos in your inbox within a week."),
                     ("Prints", "Museum-quality prints and albums."), ("Studio rental", "Rent our studio by the hour.")],
        "products": [("Mini session", 150.0), ("Portrait session", 300.0), ("Wedding package", 2400.0), ("Studio hour", 75.0)],
        "cta": ["Book a session", "View portfolio", "Get a quote"],
        "nav": ["Portfolio", "Services", "Pricing", "Contact"],
    },
    "web design agency": {
        "names": ["Lumen Labs", "Pixel & Pine", "Northstar Digital", "Brightside Studio", "Blueprint Web"],
        "taglines": ["Websites that look good and load fast.", "We design and build websites for small businesses.", "From idea to launch in weeks, not months."],
        "features": [("Custom design", "No templates. Every site is designed for you."), ("Fast websites", "Built to load in under a second."),
                     ("SEO basics", "Set up so customers can find you."), ("Easy updates", "Edit your own content without code."),
                     ("Ongoing support", "We stick around after launch."), ("Accessible by default", "Usable by everyone, on every device.")],
        "products": [("Starter site", 1500.0), ("Business site", 4000.0), ("Online store", 7500.0), ("Monthly care plan", 99.0)],
        "cta": ["Start a project", "See our work", "Get a quote"],
        "nav": ["Work", "Services", "Process", "Contact"],
    },
    "yoga studio": {
        "names": ["Still Water Yoga", "Lotus Room", "Breathe Studio", "Sun Salute Yoga", "Quiet Mind Yoga"],
        "taglines": ["Classes for every body and every level.", "Slow down, breathe, and move.", "A calm space in a busy city."],
        "features": [("Beginner friendly", "Gentle classes to learn the basics."), ("Hot yoga", "Heated vinyasa flows to build strength."),
                     ("Meditation", "Guided sessions every evening."), ("Small classes", "Never more than fifteen people."),
                     ("Mats provided", "Just show up, we have everything."), ("Private lessons", "One-on-one sessions at your pace.")],
        "products": [("Drop-in class", 20.0), ("5-class pass", 90.0), ("Unlimited monthly", 120.0), ("Private lesson", 75.0)],
        "cta": ["Book a class", "See the schedule", "Try a free class"],
        "nav": ["Classes", "Schedule", "Teachers", "Contact"],
    },
    "dental clinic": {
        "names": ["Bright Smile Dental", "Maple Dental", "Pearl Dental Care", "Gentle Dental", "Riverside Dental"],
        "taglines": ["Gentle care for the whole family.", "Modern dentistry without the stress.", "Healthy smiles start here."],
        "features": [("Family dentistry", "Checkups and cleanings for all ages."), ("Emergency visits", "Same-day appointments for urgent pain."),
                     ("Teeth whitening", "Safe, professional whitening in one visit."), ("Insurance friendly", "We work with most major plans."),
                     ("Evening hours", "Open until 7pm on weekdays."), ("Calm environment", "Blankets, headphones and a gentle team.")],
        "products": [("Checkup and cleaning", 120.0), ("Whitening", 350.0), ("Filling", 180.0), ("Emergency visit", 95.0)],
        "cta": ["Book an appointment", "Call us", "Request a visit"],
        "nav": ["Services", "Our team", "Insurance", "Contact"],
    },
    "bike shop": {
        "names": ["Spoke & Chain", "Two Wheels", "Gearhouse Cycles", "Velo Works", "Pedal Republic"],
        "taglines": ["Bikes, repairs, and friendly advice.", "Your local shop for every kind of ride.", "Tune-ups done right, done fast."],
        "features": [("Repairs", "Most tune-ups are done in 48 hours."), ("New and used bikes", "Road, gravel, city and kids bikes."),
                     ("Bike fitting", "Get set up for comfort and speed."), ("Group rides", "Free rides every Sunday morning."),
                     ("Rentals", "Rent a bike by the day or week."), ("Parts and gear", "Helmets, lights, locks and more.")],
        "products": [("Basic tune-up", 65.0), ("Full service", 140.0), ("Day rental", 35.0), ("Flat fix", 15.0)],
        "cta": ["Book a repair", "Shop bikes", "Rent a bike"],
        "nav": ["Bikes", "Repairs", "Rentals", "Contact"],
    },
    "restaurant": {
        "names": ["Olive & Thyme", "The Corner Table", "Saffron House", "Harvest Kitchen", "Blue Plate"],
        "taglines": ["Seasonal dishes made from local ingredients.", "Dinner with friends, done right.", "Fresh food, warm room, good wine."],
        "features": [("Seasonal menu", "Our menu changes with what's fresh."), ("Private dining", "A room for parties of up to twenty."),
                     ("Takeout", "Order online and pick up in 20 minutes."), ("Weekend brunch", "Saturdays and Sundays from 9am."),
                     ("Wine list", "Over forty wines by the glass."), ("Kids menu", "Simple, tasty plates for little ones.")],
        "products": [("Roasted chicken", 22.0), ("Mushroom risotto", 19.0), ("Grilled salmon", 26.0), ("Garden salad", 12.0), ("Chocolate tart", 9.0), ("Pasta of the day", 18.0)],
        "cta": ["Book a table", "See the menu", "Order takeout"],
        "nav": ["Menu", "Reservations", "About", "Contact"],
        "food": True,
    },
    "pet grooming": {
        "names": ["Happy Paws", "The Groom Room", "Fluff & Fold", "Wag Wash", "Pawsh Spa"],
        "taglines": ["Gentle grooming for happy pets.", "Clean, fluffy and calm, every visit.", "Your pet's favorite spa day."],
        "features": [("Full groom", "Bath, haircut, nails and ears."), ("Gentle handlers", "Calm, patient groomers who love animals."),
                     ("Cat grooming", "Quiet appointments just for cats."), ("Self-serve wash", "Wash your dog in our tubs."),
                     ("Nail trims", "Quick walk-in nail trims."), ("Pickup and drop-off", "We can collect your pet from home.")],
        "products": [("Small dog groom", 55.0), ("Large dog groom", 85.0), ("Cat groom", 70.0), ("Nail trim", 15.0)],
        "cta": ["Book grooming", "See prices", "Call us"],
        "nav": ["Services", "Prices", "Gallery", "Contact"],
    },
    "music school": {
        "names": ["Echo Music School", "Treble & Bass", "Harmony House", "Downbeat Academy", "Major Key Music"],
        "taglines": ["Lessons for every age and instrument.", "Learn to play the music you love.", "Patient teachers, fun lessons."],
        "features": [("Piano lessons", "From first notes to advanced pieces."), ("Guitar lessons", "Acoustic, electric and bass."),
                     ("Singing lessons", "Find your voice with a vocal coach."), ("Kids programs", "Playful classes for ages 5 to 12."),
                     ("Recitals", "Two student concerts every year."), ("Flexible scheduling", "Lessons after school and on weekends.")],
        "products": [("30-minute lesson", 35.0), ("60-minute lesson", 60.0), ("Monthly plan", 200.0), ("Group class", 25.0)],
        "cta": ["Book a lesson", "Meet our teachers", "Try a free lesson"],
        "nav": ["Lessons", "Teachers", "Pricing", "Contact"],
    },
    "coworking space": {
        "names": ["The Hive", "Common Desk", "Workshop Commons", "Studio 12", "Open Office Club"],
        "taglines": ["Desks, meeting rooms, and good coffee.", "A focused place to do your best work.", "Flexible workspace for freelancers and teams."],
        "features": [("Hot desks", "Grab any free desk, any day."), ("Private offices", "Lockable offices for teams of two to ten."),
                     ("Meeting rooms", "Bookable rooms with screens and whiteboards."), ("Fast internet", "Gigabit Wi-Fi throughout."),
                     ("Free coffee", "Unlimited coffee and tea."), ("Community events", "Lunch talks and socials every month.")],
        "products": [("Day pass", 25.0), ("Hot desk", 180.0), ("Dedicated desk", 320.0), ("Private office", 900.0)],
        "cta": ["Book a tour", "Get a day pass", "See membership"],
        "nav": ["Spaces", "Pricing", "Events", "Contact"],
    },
    "travel agency": {
        "names": ["Atlas Travel", "Wander & Co.", "Compass Trips", "Far Horizons", "Passport Travel"],
        "taglines": ["Trips planned around you.", "Adventure, relaxation, or both.", "Let us handle the details."],
        "features": [("Custom itineraries", "Every trip is planned from scratch."), ("Group tours", "Small groups with expert guides."),
                     ("Honeymoons", "Romantic trips to unforgettable places."), ("24/7 support", "Help is one call away while you travel."),
                     ("Best price promise", "We match any better price you find."), ("Visa help", "We guide you through the paperwork.")],
        "products": [("Weekend city break", 650.0), ("Beach week", 1400.0), ("Safari tour", 3200.0), ("Trip planning", 150.0)],
        "cta": ["Plan my trip", "See destinations", "Talk to an agent"],
        "nav": ["Destinations", "Tours", "About", "Contact"],
    },
    "plant shop": {
        "names": ["Green Leaf", "Fern & Fronds", "The Plant Room", "Urban Jungle", "Root & Pot"],
        "taglines": ["Plants that are easy to love.", "Bring a little green home.", "Houseplants, pots and friendly advice."],
        "features": [("Easy-care plants", "Picks that thrive even if you forget to water."), ("Repotting service", "Bring your plant, we'll repot it."),
                     ("Plant doctor", "Free help for sad-looking plants."), ("Pots and planters", "Handmade ceramics from local makers."),
                     ("Delivery", "Plants delivered safely to your door."), ("Workshops", "Learn to build a terrarium.")],
        "products": [("Snake plant", 28.0), ("Monstera", 45.0), ("Pothos", 18.0), ("Ceramic pot", 22.0), ("Terrarium kit", 35.0)],
        "cta": ["Shop plants", "Book a workshop", "Visit the shop"],
        "nav": ["Plants", "Pots", "Workshops", "Contact"],
    },
}

# Extra kinds that reuse GENERIC_FEATURES, so Coda learns to copy any business type.
GENERIC_KINDS = ["lawn care company", "plumbing service", "tattoo studio", "daycare", "car repair shop", "cleaning service",
                 "moving company", "barber shop", "tutoring center", "accounting firm", "food truck", "ice cream shop",
                 "dog walking service", "art gallery", "hair salon", "home bakery", "climbing gym", "tea house",
                 "print shop", "vintage clothing store"]
GENERIC_NAME_PARTS = (["Bright", "Blue", "Golden", "Little", "North", "Happy", "Urban", "Maple", "Silver", "Red", "Oak", "Sunny"],
                      ["Bear", "Fox", "Lane", "Leaf", "Peak", "River", "Corner", "Harbor", "Field", "Studio", "Works", "House"])

PROJECTS = [("Brand refresh", "A new identity for a local coffee roaster."), ("Mobile app", "A habit tracker with 20k users."),
            ("Online store", "A shop for handmade ceramics."), ("Dashboard", "Analytics for a delivery startup."),
            ("Portfolio site", "A minimal site for a photographer."), ("Booking system", "Online booking for a yoga studio."),
            ("Recipe app", "Meal planning with shopping lists."), ("Event website", "Tickets and schedule for a music festival."),
            ("Newsletter design", "Email templates for a bookstore."), ("Travel blog", "Stories and maps from a year abroad.")]
ROLES = [("web developer", ["HTML", "CSS", "JavaScript", "Python", "Accessibility", "Git"]),
         ("product designer", ["Figma", "User research", "Prototyping", "Design systems", "CSS", "Illustration"]),
         ("photographer", ["Portraits", "Lighting", "Lightroom", "Weddings", "Film", "Editing"]),
         ("data analyst", ["Python", "SQL", "Excel", "Dashboards", "Statistics", "Visualization"]),
         ("illustrator", ["Procreate", "Character design", "Lettering", "Branding", "Watercolor", "Editorial"])]

FAQS = [("Do I need to book in advance?", "Booking ahead is recommended, but walk-ins are welcome when we have space."),
        ("What are your opening hours?", "We are open Monday to Saturday, 8am to 6pm."),
        ("Do you offer gift cards?", "Yes. Gift cards are available in the shop and online."),
        ("Can I cancel or reschedule?", "Yes, free of charge up to 24 hours before your appointment."),
        ("Is there parking nearby?", "There is free street parking and a garage one block away."),
        ("Which payment methods do you accept?", "We accept cards, cash and mobile payments."),
        ("Do you have a refund policy?", "If something is not right, contact us within 14 days for a refund."),
        ("Is the space wheelchair accessible?", "Yes, there is step-free access and an accessible restroom.")]

HOURS = [("Monday to Friday", "8am to 6pm"), ("Saturday", "9am to 4pm"), ("Sunday", "Closed")]

QUIZ_TOPICS = {
    "space": [("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter"], 1),
              ("What is the largest planet in our solar system?", ["Saturn", "Earth", "Jupiter"], 2),
              ("What is the name of our galaxy?", ["Milky Way", "Andromeda", "Orion"], 0)],
    "geography": [("What is the capital of Japan?", ["Kyoto", "Tokyo", "Osaka"], 1),
                  ("Which ocean is the largest?", ["Atlantic", "Indian", "Pacific"], 2),
                  ("Which river flows through Egypt?", ["Nile", "Amazon", "Danube"], 0)],
    "web development": [("What does HTML stand for?", ["HyperText Markup Language", "High Tech Modern Language", "Home Tool Markup Language"], 0),
                        ("Which language styles web pages?", ["Python", "CSS", "SQL"], 1),
                        ("Which tag creates a link?", ["<link>", "<href>", "<a>"], 2)],
    "animals": [("What is the fastest land animal?", ["Lion", "Cheetah", "Horse"], 1),
                ("How many legs does a spider have?", ["Six", "Eight", "Ten"], 1),
                ("Which animal is known for its black and white stripes?", ["Zebra", "Panda", "Skunk"], 0)],
}

QUOTES = [("Simplicity is the soul of efficiency.", "Austin Freeman"),
          ("Make it work, make it right, make it fast.", "Kent Beck"),
          ("The best way to get started is to quit talking and begin doing.", "Walt Disney"),
          ("It always seems impossible until it's done.", "Nelson Mandela"),
          ("Well done is better than well said.", "Benjamin Franklin"),
          ("Small steps every day add up.", "Unknown")]
