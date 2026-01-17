"""Quick example comparison between full model and audio-only baseline."""
import psycopg2
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv("../.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Get a popular 2005 Pop song
cur.execute("""
    SELECT sv.spotify_id, sv.embedding, s.name, s.artists, s.year, s.genre 
    FROM song_vectors sv 
    JOIN songs s ON sv.spotify_id = s.id 
    WHERE s.year = 2023 AND s.genre = 'Pop' AND s.name IS NOT NULL
    ORDER BY s.popularity DESC 
    LIMIT 1
""")
sid, emb_str, name, artists, year, genre = cur.fetchone()

print("=" * 60)
print("QUERY SONG")
print("=" * 60)
print(f"  {name}")
print(f"  {artists}")
print(f"  Year: {year}, Genre: {genre}")

# Parse embedding
emb = np.array([float(x) for x in emb_str.strip("[]").split(",")])

# Create audio-only mask (dims 0-4)
mask = np.zeros(128)
mask[0:5] = 1.0
masked = emb * mask
masked = masked / np.linalg.norm(masked)
masked_str = "[" + ",".join(map(str, masked.tolist())) + "]"

# Extract base name for filtering duplicates
base_name = name.split(" - ")[0].strip() if name else ""

# Full model recommendations (with duplicate filter)
print("\n" + "=" * 60)
print("FULL MODEL RECOMMENDATIONS (year+genre weighted)")
print("=" * 60)
cur.execute("""
    SELECT name, artists, year, genre, distance FROM (
        SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
               s.name, s.artists, s.year, s.genre,
               (sv.embedding <=> %s::vector) as distance
        FROM song_vectors sv 
        JOIN songs s ON sv.spotify_id = s.id 
        WHERE sv.spotify_id != %s 
          AND s.name IS NOT NULL
          AND LOWER(s.name) NOT LIKE LOWER(%s)
          AND LOWER(s.name) NOT LIKE LOWER(%s)
        ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)), (sv.embedding <=> %s::vector)
    ) sub
    ORDER BY distance
    LIMIT 5
""", (emb_str, sid, f"%{base_name}%", f"%{name}%", emb_str))
for i, r in enumerate(cur.fetchall(), 1):
    similarity = (1 - r[4]) * 100  # Convert distance to similarity percentage
    print(f"  {i}. {r[0][:50]}")
    print(f"     {r[1]}")
    print(f"     Year: {r[2]}, Genre: {r[3]}, Similarity: {similarity:.1f}%")
    print()

# Audio-only recommendations (with duplicate filter)
print("=" * 60)
print("AUDIO-ONLY RECOMMENDATIONS (masked embedding)")
print("=" * 60)
cur.execute("""
    SELECT name, artists, year, genre, distance FROM (
        SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
               s.name, s.artists, s.year, s.genre,
               (sv.embedding <=> %s::vector) as distance
        FROM song_vectors sv 
        JOIN songs s ON sv.spotify_id = s.id 
        WHERE sv.spotify_id != %s 
          AND s.name IS NOT NULL
          AND LOWER(s.name) NOT LIKE LOWER(%s)
          AND LOWER(s.name) NOT LIKE LOWER(%s)
        ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)), (sv.embedding <=> %s::vector)
    ) sub
    ORDER BY distance
    LIMIT 5
""", (masked_str, sid, f"%{base_name}%", f"%{name}%", masked_str))
for i, r in enumerate(cur.fetchall(), 1):
    similarity = (1 - r[4]) * 100  # Convert distance to similarity percentage
    print(f"  {i}. {r[0][:50]}")
    print(f"     {r[1]}")
    print(f"     Year: {r[2]}, Genre: {r[3]}, Similarity: {similarity:.1f}%")
    print()

conn.close()

# Also write to file
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

with open("example_output.txt", "w", encoding="utf-8") as f:
    cur.execute("""
        SELECT sv.spotify_id, sv.embedding, s.name, s.artists, s.year, s.genre 
        FROM song_vectors sv 
        JOIN songs s ON sv.spotify_id = s.id 
        WHERE s.year = 2023 AND s.genre = 'Pop' AND s.name IS NOT NULL
        ORDER BY s.popularity DESC 
        LIMIT 1
    """)
    sid, emb_str, name, artists, year, genre = cur.fetchone()
    
    f.write("=" * 60 + "\n")
    f.write("QUERY SONG\n")
    f.write("=" * 60 + "\n")
    f.write(f"  {name}\n")
    f.write(f"  {artists}\n")
    f.write(f"  Year: {year}, Genre: {genre}\n\n")
    
    emb = np.array([float(x) for x in emb_str.strip("[]").split(",")])
    mask = np.zeros(128)
    mask[0:5] = 1.0
    masked = emb * mask
    masked = masked / np.linalg.norm(masked)
    masked_str = "[" + ",".join(map(str, masked.tolist())) + "]"
    
    # Extract base name for filtering duplicates
    base_name = name.split(" - ")[0].strip() if name else ""
    
    f.write("=" * 60 + "\n")
    f.write("FULL MODEL RECOMMENDATIONS (year+genre weighted)\n")
    f.write("=" * 60 + "\n")
    cur.execute("""
        SELECT name, artists, year, genre, distance FROM (
            SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
                   s.name, s.artists, s.year, s.genre,
                   (sv.embedding <=> %s::vector) as distance
            FROM song_vectors sv 
            JOIN songs s ON sv.spotify_id = s.id 
            WHERE sv.spotify_id != %s 
              AND s.name IS NOT NULL
              AND LOWER(s.name) NOT LIKE LOWER(%s)
              AND LOWER(s.name) NOT LIKE LOWER(%s)
            ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)), (sv.embedding <=> %s::vector)
        ) sub
        ORDER BY distance
        LIMIT 5
    """, (emb_str, sid, f"%{base_name}%", f"%{name}%", emb_str))
    for i, r in enumerate(cur.fetchall(), 1):
        similarity = (1 - r[4]) * 100
        f.write(f"  {i}. {r[0]}\n")
        f.write(f"     {r[1]}\n")
        f.write(f"     Year: {r[2]}, Genre: {r[3]}, Similarity: {similarity:.1f}%\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("AUDIO-ONLY RECOMMENDATIONS (masked embedding)\n")
    f.write("=" * 60 + "\n")
    cur.execute("""
        SELECT name, artists, year, genre, distance FROM (
            SELECT DISTINCT ON (LOWER(SPLIT_PART(s.name, ' - ', 1)))
                   s.name, s.artists, s.year, s.genre,
                   (sv.embedding <=> %s::vector) as distance
            FROM song_vectors sv 
            JOIN songs s ON sv.spotify_id = s.id 
            WHERE sv.spotify_id != %s 
              AND s.name IS NOT NULL
              AND LOWER(s.name) NOT LIKE LOWER(%s)
              AND LOWER(s.name) NOT LIKE LOWER(%s)
            ORDER BY LOWER(SPLIT_PART(s.name, ' - ', 1)), (sv.embedding <=> %s::vector)
        ) sub
        ORDER BY distance
        LIMIT 5
    """, (masked_str, sid, f"%{base_name}%", f"%{name}%", masked_str))
    for i, r in enumerate(cur.fetchall(), 1):
        similarity = (1 - r[4]) * 100
        f.write(f"  {i}. {r[0]}\n")
        f.write(f"     {r[1]}\n")
        f.write(f"     Year: {r[2]}, Genre: {r[3]}, Similarity: {similarity:.1f}%\n\n")

conn.close()
print("\nOutput saved to example_output.txt")
