# Configurations for Kumbh Monitor Data Ingestion Pipeline

# Target Years & Dates
NASHIK_2015_START = "2014-07-14"  # Event was July - Sept 2015, window ±1 year
NASHIK_2015_END = "2016-09-25"

PRAYAGRAJ_2025_START = "2024-01-14"  # Event was Jan - Feb 2025, window ±1 year
PRAYAGRAJ_2025_END = "2026-02-26"

# Core search terms scoped by theme clusters
KEYWORDS = {
    "general": [
        "Nashik Kumbh Mela 2015",
        "Nashik Simhastha 2015",
        "Prayagraj Maha Kumbh 2025",
        "Kumbh Mela 2025"
    ],
    "infrastructure": [
        "Kumbh roads flyover bridge bypass traffic",
        "Kumbh bathing ghats river embankments civil works",
        "Kumbh toilets sanitation sewage drainage plumbing",
        "Kumbh electrical grid street lighting power",
        "Kumbh telecom towers Wi-Fi connectivity internet network",
        "Kumbh public transport buses special trains parking layout"
    ],
    "health_food_water": [
        "Kumbh epidemic disease tracking outbreak surveillance",
        "Kumbh temporary hospitals medical camps ambulances",
        "Kumbh mental health counselling trauma support",
        "Kumbh community kitchens langar food distribution",
        "Kumbh food safety adulteration hygiene FSSAI",
        "Kumbh drinking water supply pipelines tankers"
    ],
    "crowd_safety_environment": [
        "Kumbh crowd management density control queues gates",
        "Kumbh stampede fire incident drownings emergency rescue",
        "Kumbh police deployment security surveillance command center",
        "Kumbh missing persons lost found rehabilitation",
        "Kumbh Godavari Ganga river water quality pollution BOD levels",
        "Kumbh waste garbage plastic management recycling clearing",
        "Kumbh air quality climate weather forecast impact"
    ],
    "spiritual_cultural_tech": [
        "Kumbh Shahi Snan royal bath procession order",
        "Kumbh Akhada operations mahants disputes governance",
        "Kumbh daily aartis rituals ceremonies pravachan",
        "Kumbh heritage cultural programs art exhibitions",
        "Kumbh pilgrim mobile apps booking system",
        "Kumbh AI computer vision crowd analytics predictive",
        "Kumbh aerial drones IoT sensors CCTV monitoring"
    ],
    "governance_economy_info": [
        "Kumbh government planning coordination policy master plan",
        "Kumbh budget allocation spending audit funds release",
        "Kumbh tourism economy commercial vendor vendors local",
        "Kumbh fake news rumors viral misinformation",
        "Kumbh fact checks corrections official rebuttals"
    ]
}

# Domain-specific targeting list (to query specific news outlets)
NEWS_DOMAINS = [
    # National English
    "timesofindia.indiatimes.com",
    "indianexpress.com",
    "thehindu.com",
    "hindustantimes.com",
    "ndtv.com",
    # Regional Marathi (Nashik)
    "lokmat.com",
    "esakal.com",
    "maharashtratimes.com",
    # Regional Hindi (Prayagraj)
    "dainikbhaskar.com",
    "amarujala.com",
    "jagran.com"
]

# Database Path
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "kumbh_monitor.db")
