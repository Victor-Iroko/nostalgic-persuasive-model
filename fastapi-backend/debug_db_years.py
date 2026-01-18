
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("\n=== Checking Movie Years ===")
        cursor.execute("SELECT title, year FROM movies WHERE title ILIKE '%Toy Story 4%'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Movie: {row[0]}, Year: {row[1]}")
            
        cursor.execute("SELECT title, year FROM movies WHERE title ILIKE '%Bender: The Beginning%'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Movie: {row[0]}, Year: {row[1]}")

        print("\n=== Checking Song Years ===")
        cursor.execute("SELECT name, year FROM songs WHERE name ILIKE '%Someone You Loved%'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Song: {row[0]}, Year: {row[1]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
