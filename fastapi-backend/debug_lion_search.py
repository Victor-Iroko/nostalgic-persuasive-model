
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def debug_search():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("\n=== Checking 'The Lion King' ===")
        cursor.execute("SELECT id, title, year, rating_count FROM movies WHERE title ILIKE '%Lion King%'")
        rows = cursor.fetchall()
        if not rows:
            print("❌ 'The Lion King' NOT FOUND in database!")
        for row in rows:
            print(f"ID: {row[0]}, Title: {row[1]}, Year: {row[2]}, Ratings: {row[3]}")
            
        print("\n=== Simulating Search for 'lion' (Top 15) ===")
        # Logic matches movies.get.ts:
        # ilike %lion%, year <= 2016, order by rating_count desc
        query = """
            SELECT title, year, rating_count 
            FROM movies 
            WHERE title ILIKE '%lion%' 
            AND year <= 2016 
            ORDER BY rating_count DESC 
            LIMIT 15
        """
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"Found {len(results)} matches. Top 15:")
        for idx, row in enumerate(results):
            print(f"{idx+1}. {row[0]} ({row[1]}) - {row[2]} ratings")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search()
