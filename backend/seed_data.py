import os
import random
from datetime import datetime, timedelta, timezone
from app import app, db, IssueReport, get_or_create_citizen

# Define Uttar Pradesh specific data
CITIES = [
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
    {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
    {"name": "Prayagraj", "lat": 25.4358, "lon": 81.8463}
]

CATEGORIES = [
    "Pothole and Road Damage",
    "Garbage and Waste Management",
    "Streetlight and Infrastructure Failure",
    "General Civic Maintenance"
]

DESCRIPTIONS = {
    "Pothole and Road Damage": [
        "Massive pothole on the main road, very dangerous for two-wheelers.",
        "Road cave-in after recent water pipeline work.",
        "Asphalt has completely worn off, creating a dusty and bumpy ride.",
        "Deep crater near the intersection, causing major traffic slowdowns."
    ],
    "Garbage and Waste Management": [
        "Overflowing dumpster, garbage spilling onto the street for 3 days.",
        "Illegal dumping of construction waste in the empty lot.",
        "Public park bins haven't been cleared all week, foul smell.",
        "Plastic waste accumulating near the drainage canal, causing blockage."
    ],
    "Streetlight and Infrastructure Failure": [
        "Streetlight pole fell over during the storm.",
        "Entire block is dark, 5 consecutive streetlights are not working.",
        "Broken pedestrian walkway railing, safety hazard.",
        "Traffic light at the main crossing is stuck on red."
    ],
    "General Civic Maintenance": [
        "Overgrown branches covering the street sign.",
        "Public water tap is leaking continuously.",
        "Stray cattle causing nuisance in the residential area.",
        "Faded zebra crossing lines need repainting."
    ]
}

DESCRIPTIONS_HI = {
    "Pothole and Road Damage": [
        "मुख्य सड़क पर बड़ा गड्ढा, दोपहिया वाहनों के लिए बहुत खतरनाक।",
        "हाल के पानी पाइपलाइन काम के बाद सड़क धंस गई है।",
        "सड़क पूरी तरह से खराब हो गई है, जिससे धूल और झटके लग रहे हैं।",
        "चौराहे के पास गहरा गड्ढा, जिसके कारण भारी ट्रैफिक जाम हो रहा है।"
    ],
    "Garbage and Waste Management": [
        "कूड़ेदान भर गया है, 3 दिनों से सड़क पर कचरा फैल रहा है।",
        "खाली प्लॉट में निर्माण कचरे का अवैध डंपिंग।",
        "पब्लिक पार्क के डिब्बे पूरे हफ्ते से साफ नहीं हुए हैं, बदबू आ रही है।",
        "नाली के पास प्लास्टिक कचरा जमा हो रहा है, जिससे रुकावट हो रही है।"
    ],
    "Streetlight and Infrastructure Failure": [
        "तूफान के दौरान स्ट्रीटलाइट का खंभा गिर गया।",
        "पूरा ब्लॉक अंधेरे में है, लगातार 5 स्ट्रीटलाइट काम नहीं कर रही हैं।",
        "टूटी हुई पैदल यात्री वॉकवे रेलिंग, सुरक्षा के लिए खतरा।",
        "मुख्य क्रॉसिंग पर ट्रैफिक लाइट लाल बत्ती पर अटकी हुई है।"
    ],
    "General Civic Maintenance": [
        "पेड़ की शाखाएं गली के बोर्ड को ढक रही हैं।",
        "सार्वजनिक पानी का नल लगातार लीक कर रहा है।",
        "आवासीय क्षेत्र में आवारा पशु उपद्रव मचा रहे हैं。",
        "फीकी पड़ी ज़ेबरा क्रॉसिंग लाइनों को फिर से रंगने की जरूरत है।"
    ]
}

REPORTER_NAMES = ["Amit Singh", "Priya Sharma", "Rahul Verma", "Sneha Gupta", "Vikas Yadav", "Neha Mishra", "Anonymous"]

def generate_mock_data():
    with app.app_context():
        print("Clearing existing issues...")
        IssueReport.query.delete()
        db.session.commit()

        print("Generating mock data for Uttar Pradesh...")
        
        now = datetime.now(timezone.utc)
        issues = []

        for _ in range(50):
            city = random.choice(CITIES)
            
            # Scatter coordinates slightly around the city center (approx within 5-10km)
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)
            lat = city["lat"] + lat_offset
            lon = city["lon"] + lon_offset

            category = random.choice(CATEGORIES)
            desc_index = random.randint(0, len(DESCRIPTIONS[category]) - 1)
            description = DESCRIPTIONS[category][desc_index]
            description_hi = DESCRIPTIONS_HI[category][desc_index]
            
            # Bias severity based on category
            if category == "Pothole and Road Damage":
                severity = random.randint(3, 5)
            elif category == "Garbage and Waste Management":
                severity = random.randint(2, 4)
            else:
                severity = random.randint(1, 5)

            status = random.choice(["Pending", "Resolved"])
            flagged = False
            if status == "Pending" and random.random() < 0.05:
                flagged = True

            upvotes = random.randint(0, 45)
            downvotes = random.randint(0, 5)

            # Randomize dates within the last 14 days
            days_ago = random.randint(0, 14)
            hours_ago = random.randint(0, 23)
            created_at = now - timedelta(days=days_ago, hours=hours_ago)
            
            resolved_at = None
            if status == "Resolved":
                resolve_hours = random.randint(12, 72)
                resolved_at = created_at + timedelta(hours=resolve_hours)
                if resolved_at > now:
                    resolved_at = now

            reporter = random.choice(REPORTER_NAMES)
            if reporter != "Anonymous":
                citizen = get_or_create_citizen(reporter)
                citizen.points += 10
                citizen.reports_filed += 1
            
            issue = IssueReport(
                category=category,
                description=f"{description} (Location: near {city['name']})",
                latitude=lat,
                longitude=lon,
                media_type='image',
                status=status,
                flagged_spam=flagged,
                upvotes=upvotes,
                downvotes=downvotes,
                ai_severity=severity,
                ai_summary=description,
                ai_summary_hi=description_hi,
                reporter_name=reporter,
                created_at=created_at,
                resolved_at=resolved_at
            )
            issues.append(issue)

        db.session.add_all(issues)
        db.session.commit()
        print(f"Successfully inserted {len(issues)} mock civic issues across Uttar Pradesh!")

if __name__ == '__main__':
    generate_mock_data()
