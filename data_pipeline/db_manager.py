import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "kumbh_monitor.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys, set busy timeout, and enable Write-Ahead Logging (WAL) mode
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    print(f"Initializing SQLite database at: {DB_PATH}")
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("Schema successfully applied.")
    except Exception as e:
        conn.rollback()
        print(f"Error applying schema: {e}")
        raise e
    finally:
        conn.close()

def seed_taxonomy():
    print("Seeding taxonomy data...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Editions
    editions = [
        ('edition.nashik_2015', 'Nashik Simhastha 2015', 2015, '2015-07-14', '2015-09-25'),
        ('edition.prayagraj_2025', 'Maha Kumbh Prayagraj 2025', 2025, '2025-01-14', '2025-02-26'),
        ('edition.nashik_2027', 'Nashik Simhastha 2027', 2027, None, None),
        ('edition.historical_other', 'Other Historical Kumbh', 0, None, None)
    ]
    
    # 2. Themes (28 themes organized into 11 clusters)
    themes = [
        # Infrastructure Cluster
        ('theme.roads_bridges', 'Roads & Bridges', 'Vehicular infrastructure built or upgraded for Kumbh — roads, flyovers, bridges, traffic signal systems.', 'Infrastructure'),
        ('theme.ghats_river_works', 'Ghats & River Works', 'Bathing ghats, river embankments, dredging, river-side civil works specific to Kumbh.', 'Infrastructure'),
        ('theme.sanitation_infra', 'Sanitation Infrastructure', 'Toilets, sewage lines, treatment plants, drainage — the physical plumbing of waste.', 'Infrastructure'),
        ('theme.power_lighting', 'Power & Lighting', 'Electrical grid upgrades, generators, street lighting, temporary power for the event.', 'Infrastructure'),
        ('theme.connectivity', 'Connectivity & Network', 'Telecom infrastructure — towers, fibre, Wi-Fi hotspots, network capacity for Kumbh.', 'Infrastructure'),
        ('theme.transport_systems', 'Transport Systems', 'Buses, special trains, parking strategy, public transit operations for the event.', 'Infrastructure'),
        # Health Cluster
        ('theme.epidemic_surveillance', 'Epidemic Surveillance', 'Disease monitoring, outbreak response, vector control, waterborne disease tracking.', 'Health'),
        ('theme.medical_response', 'Medical Response', 'Hospitals, temporary medical camps, ambulance deployment, mass casualty preparation.', 'Health'),
        ('theme.mental_health', 'Mental Health', 'Counselling services, trauma response, psychological support for pilgrims and responders.', 'Health'),
        # Food & Water Cluster
        ('theme.community_kitchens', 'Community Kitchens', 'Annadanam, langar, akhada and NGO food distribution at scale.', 'Food & Water'),
        ('theme.food_safety', 'Food Safety', 'Adulteration, hygiene inspections, FSSAI raids, food poisoning incidents.', 'Food & Water'),
        ('theme.water_supply', 'Drinking Water Supply', 'Provision and distribution of drinking water — tankers, points, distribution logistics.', 'Food & Water'),
        # Crowd & Safety Cluster
        ('theme.crowd_management', 'Crowd Management', 'Density monitoring, flow control, queue systems, barrier and slot management.', 'Crowd & Safety'),
        ('theme.incident_response', 'Incident Response', 'Stampedes, fires, drownings, accidents, and the operational response to them.', 'Crowd & Safety'),
        ('theme.policing_security', 'Policing & Security', 'Police deployment, security architecture, surveillance, anti-terror protocols.', 'Crowd & Safety'),
        ('theme.lost_found', 'Lost & Found', 'Missing persons systems, especially for children and elderly; reunification.', 'Crowd & Safety'),
        # Environment Cluster
        ('theme.river_health', 'River Health', 'Godavari water quality, pollution, biological oxygen demand, post-event recovery.', 'Environment'),
        ('theme.waste_management', 'Waste Management', 'Solid waste, plastic accumulation, recycling drives, daily clearance operations.', 'Environment'),
        ('theme.air_climate', 'Air & Climate', 'Air quality, extreme weather affecting Kumbh, climate-driven scheduling concerns.', 'Environment'),
        # Spiritual & Cultural Cluster
        ('theme.shahi_snan', 'Shahi Snan', 'Royal bath events, akhada procession order, ritual schedule of bathing days.', 'Spiritual & Cultural'),
        ('theme.akhada_activity', 'Akhada Activity', 'Akhada operations, disputes, leadership, finances, the 13 traditional akhadas.', 'Spiritual & Cultural'),
        ('theme.rituals_ceremonies', 'Rituals & Ceremonies', 'Daily aartis, pujas, kalpvas, pravachans — the granular calendar of devotion.', 'Spiritual & Cultural'),
        ('theme.heritage_culture', 'Heritage & Cultural Programs', 'Art, music, performance, heritage preservation, cultural exhibitions at Kumbh.', 'Spiritual & Cultural'),
        # Technology Cluster
        ('theme.apps_platforms', 'Apps & Platforms', 'Pilgrim apps, akhada apps, booking platforms, government information systems.', 'Technology'),
        ('theme.ai_analytics', 'AI & Analytics', 'Computer vision, ML, NLP, predictive analytics deployed at Kumbh.', 'Technology'),
        ('theme.sensors_drones', 'Sensors & Drones', 'Aerial drones, IoT sensors, fixed cameras, hardware-led monitoring.', 'Technology'),
        # Governance & Economy Cluster
        ('theme.policy_planning', 'Policy & Planning', 'Government plans, decisions, inter-agency coordination, master planning.', 'Governance & Economy'),
        ('theme.budget_spending', 'Budget & Spending', 'Allocations, expenditure, accountability, audit findings, financial reports.', 'Governance & Economy'),
        ('theme.economy_commerce', 'Economy & Commerce', 'Tourism revenue, vendor activity, sponsorships, real estate, local economy.', 'Governance & Economy'),
        # Information & Truth Cluster
        ('theme.rumors_misinfo', 'Rumors & Misinformation', 'Documented false claims, recycled imagery, viral falsehoods, communal misinformation.', 'Information & Truth'),
        ('theme.fact_checks', 'Fact-Checks & Corrections', 'Verified counter-information, official rebuttals, retractions, fact-checker output.', 'Information & Truth'),
        # People & Experience Cluster
        ('theme.pilgrim_experience', 'Pilgrim Experience', 'First-person accounts, demographic stories, accessibility, foreign visitors.', 'People & Experience'),
        ('theme.volunteers_ngos', 'Volunteers & NGOs', 'Civil society activity, volunteer coordination, NGO operations, mutual aid.', 'People & Experience')
    ]
    
    # 3. Event Types (12 mutually exclusive registers)
    event_types = [
        ('event_type.announcement', 'Announcement', 'A future-tense statement of intention. Forward-looking, press release.'),
        ('event_type.decision_policy', 'Decision / Policy', 'A formal decision made — policy enacted, order issued, tender awarded. Carries administrative authority.'),
        ('event_type.milestone', 'Milestone', 'Something completed and made public. Bridge opened, app launched, hospital inaugurated.'),
        ('event_type.incident', 'Incident', 'Something unplanned happened. Stampede, fire, drowning, raid, protest, accident.'),
        ('event_type.analysis', 'Analysis', 'Opinion, commentary, op-ed, deep dive, retrospective. Author interprets events.'),
        ('event_type.investigation', 'Investigation', 'Journalism that uncovers information not previously public.'),
        ('event_type.forecast', 'Forecast', 'Predictions, projections, planning estimates of what will happen.'),
        ('event_type.testimony', 'Testimony', 'First-person account of lived experience (e.g., pilgrim diary).'),
        ('event_type.correction', 'Correction', 'Retraction, clarification, fact-check, official rebuttal.'),
        ('event_type.data_release', 'Data Release', 'Government, academic, or institutional publication of numbers or formal reports.'),
        ('event_type.cultural_moment', 'Cultural Moment', 'Notable performance, gathering, or religious ceremony.'),
        ('event_type.legal_judicial', 'Legal / Judicial', 'Court rulings, FIRs filed, litigation, formal complaints.')
    ]
    
    # 4. Stakeholders (13 perspectives)
    stakeholders = [
        ('stakeholder.gov_centre', 'Government — Centre', 'Union ministries, central agencies (NDRF national, ICMR).'),
        ('stakeholder.gov_state', 'Government — State', 'Maharashtra state government and its ministries; MPCB; state police HQ.'),
        ('stakeholder.gov_municipal', 'Government — Municipal', 'Nashik Municipal Corp, district administration, local elected representatives.'),
        ('stakeholder.akhada', 'Akhadas', 'The 13 traditional akhadas as institutions — Akhada Parishad, individual councils.'),
        ('stakeholder.temple_trust', 'Temple Trusts', 'Temple management bodies like Trimbakeshwar Temple Trust.'),
        ('stakeholder.pilgrim', 'Pilgrims', 'Individual or aggregate pilgrim voices.'),
        ('stakeholder.vendor_business', 'Vendors & Local Business', 'Stallholders, shopkeepers, hotels, local businesses.'),
        ('stakeholder.media_journalist', 'Media & Journalists', 'News organizations and reporters as actors in the story.'),
        ('stakeholder.civil_society', 'Civil Society / NGOs', 'NGOs, volunteer groups, community collectives.'),
        ('stakeholder.researcher', 'Researchers & Academics', 'Universities, think tanks, scholars.'),
        ('stakeholder.foreign_observer', 'Foreign Observers', 'International media, diplomats, foreign visitors.'),
        ('stakeholder.security_emergency', 'Security & Emergency Services', 'Police in operational role, local fire, NDRF field teams, ambulance.'),
        ('stakeholder.critic_whistleblower', 'Critics & Whistleblowers', 'Opposition politicians, activists, whistleblowers, leaks.')
    ]
    
    # 5. Places (Nashik/Trimbakeshwar gazetteer sample)
    places = [
        ('place.nashik.ramkund', 'Ramkund', 20.0039, 73.7915, 'Nashik', 'Main bathing ghat, central to Nashik Kumbh.'),
        ('place.nashik.tapovan', 'Tapovan', 20.0078, 73.8055, 'Nashik', 'Camping area for pilgrims and sadhus.'),
        ('place.nashik.sadhugram', 'Sadhugram', 20.0150, 73.8150, 'Nashik', 'Temporary city built for sadhus.'),
        ('place.nashik.panchavati', 'Panchavati', 20.0045, 73.7930, 'Nashik', 'Historic religious precinct surrounding Ramkund.'),
        ('place.nashik.kapaleshwar', 'Kapaleshwar Temple', 20.0042, 73.7925, 'Nashik', 'Major Shiva temple complex in Panchavati.'),
        ('place.trimbakeshwar.temple', 'Trimbakeshwar Mahadev Temple', 19.9328, 73.5305, 'Trimbakeshwar', 'One of the 12 Jyotirlingas.'),
        ('place.trimbakeshwar.kushavarta', 'Kushavarta Kund', 19.9332, 73.5298, 'Trimbakeshwar', 'Source kund of Godavari.'),
        ('place.nashik.gangapur_dam', 'Gangapur Dam', 20.0380, 73.6840, 'Nashik', 'Controls river flow into Nashik.'),
        ('place.nashik.general', 'Nashik (general)', None, None, 'Nashik', 'Fallback for general Nashik content.'),
        ('place.trimbakeshwar.general', 'Trimbakeshwar (general)', None, None, 'Trimbakeshwar', 'Fallback for general Trimbakeshwar content.'),
        ('place.prayagraj.sangam', 'Triveni Sangam', 25.4285, 81.8885, 'Prayagraj', 'Confluence of Ganges, Yamuna, and Saraswati.'),
        ('place.prayagraj.general', 'Prayagraj (general)', None, None, 'Prayagraj', 'Fallback for general Prayagraj content.')
    ]
    
    # 6. Outcomes
    outcomes = [
        ('outcome.public_health', 'Public Health', 'Disease, waterborne illness, health campaigns.'),
        ('outcome.public_safety', 'Public Safety', 'Crowd safety, stampedes, fire safety, policing.'),
        ('outcome.environment', 'Environment', 'Ecological health, water pollution, river quality.'),
        ('outcome.economic', 'Economic', 'Tourism, local businesses, spending, vendor economy.'),
        ('outcome.spiritual_religious', 'Spiritual & Religious', 'Religious devotion, akhada activity, rituals.'),
        ('outcome.political_governance', 'Political & Governance', 'Government performance, policies, political debates.'),
        ('outcome.cultural_memory', 'Cultural Memory', 'Historical preservation, documentary, oral archives.'),
        ('outcome.infrastructure_legacy', 'Infrastructure Legacy', 'Long-term value of roads, ghats, sanitation built.'),
        ('outcome.tech_deployment', 'Technology Deployment', 'Adoption of apps, analytics, hardware for crowd/smart city.'),
        ('outcome.social_relations', 'Social Relations', 'Social dynamics, volunteers, community conflicts/collaboration.')
    ]
    
    try:
        cursor.executemany("INSERT OR REPLACE INTO editions VALUES (?, ?, ?, ?, ?);", editions)
        cursor.executemany("INSERT OR REPLACE INTO themes VALUES (?, ?, ?, ?);", themes)
        cursor.executemany("INSERT OR REPLACE INTO event_types VALUES (?, ?, ?);", event_types)
        cursor.executemany("INSERT OR REPLACE INTO stakeholders VALUES (?, ?, ?);", stakeholders)
        cursor.executemany("INSERT OR REPLACE INTO places VALUES (?, ?, ?, ?, ?, ?);", places)
        cursor.executemany("INSERT OR REPLACE INTO outcomes VALUES (?, ?, ?);", outcomes)
        
        conn.commit()
        print("Taxonomy successfully seeded.")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding taxonomy: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    seed_taxonomy()
