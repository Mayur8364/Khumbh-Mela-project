import pandas as pd
import sqlite3

df = pd.read_csv("ml_module/outputs/working_df.csv")

# Risk scoring
SOURCE_TIER = {'pti':1,'reuters':1,'timesofindia':2,'thehindu':2,'ndtv':2}

def get_tier(source):
    s = str(source).lower()
    for k, v in SOURCE_TIER.items():
        if k in s: return v
    return 3

def get_risk(row):
    tier = get_tier(row['source'])
    base = {1:0.05, 2:0.15, 3:0.40}.get(tier, 0.40)
    if 'incident' in str(row['ml_event_type']): base += 0.20
    return round(min(base, 1.0), 2)

def get_band(score):
    if score < 0.25: return 'low'
    elif score < 0.50: return 'medium'
    elif score < 0.75: return 'high'
    else: return 'critical'

df['source_tier'] = df['source'].apply(get_tier)
df['risk_score']  = df.apply(get_risk, axis=1)
df['risk_band']   = df['risk_score'].apply(get_band)

# Save CSV for Anushri
cols = ['id','source','publish_date','headline',
        'ml_themes','ml_event_type','ml_temporal_phase',
        'ml_cluster_id','viz_x','viz_y','risk_score','risk_band']
df[cols].to_csv("ml_module/outputs/articles_with_taxonomy.csv", index=False)
print("CSV saved ✅")

# Save to database
conn = sqlite3.connect("data_pipeline/kumbh_monitor.db")
cursor = conn.cursor()

new_cols = [("ml_themes","TEXT"),("ml_event_type","TEXT"),
            ("ml_temporal_phase","TEXT"),("ml_cluster_id","INTEGER"),
            ("viz_x","REAL"),("viz_y","REAL"),
            ("risk_score","REAL"),("risk_band","TEXT")]

for col, dtype in new_cols:
    try:
        cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} {dtype}")
    except: pass

for _, row in df.iterrows():
    cursor.execute("""
        UPDATE articles SET
            ml_themes=?, ml_event_type=?, ml_temporal_phase=?,
            ml_cluster_id=?, viz_x=?, viz_y=?, risk_score=?, risk_band=?
        WHERE id=?
    """, (row['ml_themes'], row['ml_event_type'], row['ml_temporal_phase'],
          int(row['ml_cluster_id']), float(row['viz_x']), float(row['viz_y']),
          float(row['risk_score']), row['risk_band'], row['id']))

conn.commit()
conn.close()
print("Database updated ✅")