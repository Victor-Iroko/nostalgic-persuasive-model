
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OUTPUT_FILE = "lion_db_dump.txt"

def dump_lion_movies():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, year, rating_count 
            FROM movies 
            WHERE title ILIKE '%lion king%' 
            ORDER BY year
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"Found {len(rows)} movies matching 'lion king':\n")
            f.write("-" * 50 + "\n")
            f.write(f"{'ID':<10} | {'Year':<6} | {'Ratings':<8} | {'Title'}\n")
            f.write("-" * 50 + "\n")
            for row in rows:
                f.write(f"{row[0]:<10} | {row[1]:<6} | {row[3]:<8} | {row[2]}\n")
                
        print(f"Successfully wrote {len(rows)} entries to {OUTPUT_FILE}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_lion_movies()
