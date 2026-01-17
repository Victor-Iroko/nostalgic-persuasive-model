import psycopg2
import os
from dotenv import load_dotenv

# Load environment (from scripts/ -> fastapi-backend/ -> project_root/)
load_dotenv("../../.env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp")

def check_years():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Check Songs Table
        print("Checking 'songs' table...")
        cursor.execute("SELECT COUNT(*) FROM songs WHERE year BETWEEN 1998 AND 2002")
        count_songs = cursor.fetchone()[0]
        print(f"  Songs matching 1998-2002: {count_songs}")
        
        # 2. Check Vectors Table
        print("Checking 'song_vectors' table...")
        cursor.execute("SELECT COUNT(*) FROM song_vectors")
        count_vectors = cursor.fetchone()[0]
        print(f"  Total Vectors: {count_vectors}")
        
        # 3. Check Join
        print("Checking JOIN (vectors + songs)...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM song_vectors sv
            JOIN songs s ON sv.spotify_id = s.id
            WHERE s.year BETWEEN 1998 AND 2002
        """)
        count_join = cursor.fetchone()[0]
        print(f"  Vectors matching 1998-2002: {count_join}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_years()
