import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE

df = pd.read_csv("ml_module/outputs/working_df.csv")
embeddings = np.load("ml_module/outputs/embeddings.npy")
embeddings_norm = normalize(embeddings)

# Find best K
print("Finding best number of clusters...")
scores = []
for k in range(3, 10):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings_norm)
    score = silhouette_score(embeddings_norm, labels)
    scores.append(score)
    print(f"K={k}  Score={score:.3f}")

best_k = range(3, 10)[scores.index(max(scores))]
print(f"Best K = {best_k}")

# Apply clustering
km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df['ml_cluster_id'] = km_final.fit_predict(embeddings_norm)

# 2D coordinates for dashboard
tsne = TSNE(n_components=2, random_state=42, perplexity=20)
coords = tsne.fit_transform(embeddings_norm)
df['viz_x'] = coords[:, 0]
df['viz_y'] = coords[:, 1]

df.to_csv("ml_module/outputs/working_df.csv", index=False)
print("Done")