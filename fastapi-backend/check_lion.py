
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_lion_king():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, year, rating_count FROM movies WHERE title = 'The Lion King'")
        rows = cursor.fetchall()
        for row in rows:
            print(f"TITLE: {row[1]} || YEAR: {row[2]} || RATINGS: {row[3]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_lion_king()
