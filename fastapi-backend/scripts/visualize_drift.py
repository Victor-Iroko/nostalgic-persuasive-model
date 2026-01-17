import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import os
import datetime
import time
from dotenv import load_dotenv

# Load environment (from scripts/ -> fastapi-backend/ -> project_root/)
load_dotenv("../../.env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp")

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def demonstrate_drift():
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()

    print("--- Recency Weighting Demonstration ---\n")

    # 1. Fetch two distinct genres to correct contrast
    # Let's say User USED to like 'Country' but NOW likes 'Techno/Pop'
    
    print("Fetching 'Country' songs (Old History)...")
    # Using specific IDs or genre search if possible
    cursor.execute("SELECT id, name, artists FROM songs WHERE genre ILIKE '%country%' LIMIT 5")
    country_songs = cursor.fetchall()
    
    if not country_songs:
        # Fallback if no Country songs
        print("No Country songs found, trying 'Rock'...")
        cursor.execute("SELECT id, name, artists FROM songs WHERE genre ILIKE '%rock%' LIMIT 5")
        country_songs = cursor.fetchall()
        
    country_ids = [s[0] for s in country_songs]
    
    print(f"Fetching 'Pop' songs (New Obsession)...")
    cursor.execute("SELECT id, name, artists FROM songs WHERE genre ILIKE '%pop%' LIMIT 1")
    pop_song = cursor.fetchone()
    
    if not pop_song:
         print("No Pop songs found, taking random song...")
         cursor.execute("SELECT id, name, artists FROM songs ORDER BY RANDOM() LIMIT 1")
         pop_song = cursor.fetchone()

    pop_id = pop_song[0]

    if not country_ids or not pop_id:
        print("Error: Could not find enough songs to test.")
        return

    # 2. Get Embeddings
    all_ids = country_ids + [pop_id]
    placeholders = ",".join(["%s"] * len(all_ids))
    cursor.execute(f"SELECT spotify_id, embedding FROM song_vectors WHERE spotify_id IN ({placeholders})", all_ids)
    rows = cursor.fetchall()
    
    embeddings = {}
    for r in rows:
        val = r[1]
        if isinstance(val, str):
            vec = np.array([float(x) for x in val.strip("[]").split(",")])
        else:
            vec = np.array(val)
        embeddings[r[0]] = vec

    if len(embeddings) < 2:
        print("Error: Could not fetch embeddings.")
        return

    # 3. Scenario A: Standard Average (Old Logic)
    # All songs have equal weight (1.0)
    print("\n[Scenario A] Standard Average (All likes equal)")
    
    vecs_a = []
    for uid in country_ids:
        if uid in embeddings:
            vecs_a.append(embeddings[uid])
    
    if pop_id in embeddings:
        vecs_a.append(embeddings[pop_id])
    
    user_vector_a = np.mean(vecs_a, axis=0) # Flat average
    
    # Measure distance/similarity to the New Pop Song
    # Cosine Similarity = dot(A, B) / (norm(A) * norm(B))
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    target_emb = embeddings[pop_id]
    sim_a = cosine_sim(user_vector_a, target_emb)
    print(f"Similarity to New Pop Song: {sim_a:.4f} (The model barely noticed you liked it)")

    # 4. Scenario B: Recency Weighted (New Logic)
    # Country songs = 1 year old (Weight ~0.2)
    # Pop song = Today (Weight = 1.0)
    print("\n[Scenario B] Recency Weighted")
    
    vecs_b = []
    weights_b = []
    
    # Old songs
    for uid in country_ids:
        if uid in embeddings:
            vecs_b.append(embeddings[uid])
            weights_b.append(0.2) # Floor weight
        
    # New song
    if pop_id in embeddings:
        vecs_b.append(embeddings[pop_id])
        weights_b.append(1.0) # Maximum weight
    
    user_vector_b = np.average(vecs_b, axis=0, weights=weights_b)
    
    sim_b = cosine_sim(user_vector_b, target_emb)
    print(f"Similarity to New Pop Song: {sim_b:.4f} (The model shifted significantly!)")
    
    if sim_a != 0:
        improvement = ((sim_b - sim_a) / sim_a) * 100
        print(f"\nResult: The personalized recommendation vector moved {improvement:.1f}% closer to your new interest.")
    else:
        print("\nResult: Significant improvement detected.")

    conn.close()

if __name__ == "__main__":
    demonstrate_drift()
