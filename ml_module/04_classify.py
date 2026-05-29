import pandas as pd
import json
from transformers import pipeline
from datetime import datetime

df = pd.read_csv("ml_module/outputs/working_df.csv")
classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-MiniLM2-L6-H768")

THEMES = {
    "theme.roads_bridges": "roads, bridges, flyovers, traffic",
    "theme.sanitation_infra": "toilets, sewage, drainage, sanitation",
    "theme.medical_response": "hospitals, medical camps, ambulance",
    "theme.crowd_management": "crowd density, queue, barrier, flow control",
    "theme.incident_response": "stampede, fire, drowning, accident",
    "theme.river_health": "water quality, pollution, BOD, river",
    "theme.shahi_snan": "royal bath, shahi snan, bathing day",
    "theme.akhada_activity": "akhada, mahant, sadhus, ascetic",
    "theme.ai_analytics": "AI, machine learning, computer vision",
    "theme.sensors_drones": "drone, IoT, cameras, sensors",
    "theme.policy_planning": "government plans, policy, coordination",
    "theme.budget_spending": "budget, allocation, expenditure, audit",
    "theme.pilgrim_experience": "pilgrim, devotee, visitor experience",
}

EVENT_TYPES = {
    "event_type.announcement": "future plan, government will do something",
    "event_type.milestone": "completed, inaugurated, launched",
    "event_type.incident": "accident, stampede, unexpected event",
    "event_type.analysis": "opinion, commentary, analysis",
    "event_type.data_release": "data published, official report, statistics",
}

def classify_themes(text):
    result = classifier(text[:512], candidate_labels=list(THEMES.values()), multi_label=True)
    tags = []
    for label, score in zip(result['labels'], result['scores']):
        if score >= 0.15:
            tags.append(list(THEMES.keys())[list(THEMES.values()).index(label)])
        if len(tags) >= 3:
            break
    return json.dumps(tags)

def classify_event_type(text):
    result = classifier(text[:512], candidate_labels=list(EVENT_TYPES.values()), multi_label=False)
    best = result['labels'][0]
    return list(EVENT_TYPES.keys())[list(EVENT_TYPES.values()).index(best)]

def get_phase(row):
    DATES = {
        'nashik':    {'start': datetime(2015, 7, 14), 'end': datetime(2015, 9, 25)},
        'prayagraj': {'start': datetime(2025, 1, 14), 'end': datetime(2025, 2, 26)},
    }
    try:
        pub = pd.to_datetime(row['publish_date'])
        text = str(row.get('headline', '')).lower()
        ed = 'prayagraj' if '2025' in text or 'prayagraj' in text else 'nashik'
        s, e = DATES[ed]['start'], DATES[ed]['end']
        before = (s - pub).days
        after  = (pub - e).days
        if   before > 365: return 'phase.planning'
        elif before > 30:  return 'phase.buildup'
        elif before > 0:   return 'phase.arrival'
        elif after  < 0:   return 'phase.event'
        elif after  <= 180: return 'phase.aftermath'
        else:              return 'phase.legacy'
    except:
        return 'phase.unknown'

print(f"Classifying {len(df)} articles... this takes ~10 mins")
df['ml_themes']         = df['text'].apply(classify_themes)
print("Themes done ✅")
df['ml_event_type']     = df['text'].apply(classify_event_type)
print("Event types done ✅")
df['ml_temporal_phase'] = df.apply(get_phase, axis=1)
print("Phases done ✅")

df.to_csv("ml_module/outputs/working_df.csv", index=False)
print("All done")