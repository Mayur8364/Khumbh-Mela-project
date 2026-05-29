import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

df = pd.read_csv("ml_module/outputs/working_df.csv")
df['text'] = df['headline'].fillna('') + ". " + df['clean_body'].fillna('')

model = SentenceTransformer('all-MiniLM-L6-v2')
print("Generating embeddings...")

embeddings = model.encode(df['text'].tolist(), show_progress_bar=True)
print(f"Shape: {embeddings.shape}")

np.save("ml_module/outputs/embeddings.npy", embeddings)
df.to_csv("ml_module/outputs/working_df.csv", index=False)
print("Done")