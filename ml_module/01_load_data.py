import pandas as pd
import shutil

# Backup first
shutil.copy("data_pipeline/kumbh_monitor.db", "data_pipeline/kumbh_monitor_BACKUP.db")
print("Backup done")

# Load data
df = pd.read_csv("data_pipeline/articles_export_clean.csv")
print(f"Total articles: {len(df)}")
print(df.columns.tolist())

df.to_csv("ml_module/outputs/working_df.csv", index=False)
print("Done")