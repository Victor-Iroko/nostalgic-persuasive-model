"""Check database size, particularly for song embeddings."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv("../.env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp")

def main() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Total database size
    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as db_size")
    print(f"Total Database Size: {cur.fetchone()[0]}")
    
    # Table sizes
    cur.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
        LIMIT 15
    """)
    
    print("\nTable Sizes (Top 15):")
    print(f"{'Table':<30} {'Total':<12} {'Data':<12} {'Indexes':<12}")
    print("-" * 66)
    for row in cur.fetchall():
        print(f"{row[0]:<30} {row[1]:<12} {row[2]:<12} {row[3]:<12}")
    
    # Specifically check song_vectors table
    cur.execute("""
        SELECT 
            COUNT(*) as row_count,
            pg_size_pretty(pg_total_relation_size('song_vectors')) as total_size,
            pg_size_pretty(pg_relation_size('song_vectors')) as data_size
        FROM song_vectors
    """)
    row = cur.fetchone()
    print(f"\nSong Vectors Table Details:")
    print(f"  Row Count: {row[0]:,}")
    print(f"  Total Size: {row[1]}")
    print(f"  Data Size: {row[2]}")
    
    # Check embedding column size
    cur.execute("""
        SELECT 
            pg_column_size(embedding) as embedding_bytes
        FROM song_vectors 
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        print(f"  Embedding Size per Row: {row[0]} bytes")
    
    # Analyze lyrics column in songs table
    print("\n" + "=" * 66)
    print("LYRICS COLUMN ANALYSIS")
    print("=" * 66)
    
    # Count songs with lyrics
    cur.execute("""
        SELECT 
            COUNT(*) as total_songs,
            COUNT(lyrics) as songs_with_lyrics,
            COUNT(*) - COUNT(lyrics) as songs_without_lyrics
        FROM songs
    """)
    row = cur.fetchone()
    if row:
        print(f"\nSong Count:")
        print(f"  Total Songs: {row[0]:,}")
        print(f"  With Lyrics: {row[1]:,}")
        print(f"  Without Lyrics: {row[2]:,}")
    
    # Calculate average and total lyrics size
    cur.execute("""
        SELECT 
            AVG(LENGTH(lyrics)) as avg_lyrics_length,
            AVG(pg_column_size(lyrics)) as avg_lyrics_bytes,
            SUM(pg_column_size(lyrics)) as total_lyrics_bytes,
            MAX(LENGTH(lyrics)) as max_lyrics_length,
            MIN(LENGTH(lyrics)) as min_lyrics_length
        FROM songs
        WHERE lyrics IS NOT NULL
    """)
    row = cur.fetchone()
    if row and row[0]:
        avg_length = row[0]
        avg_bytes = row[1]
        total_bytes = row[2]
        max_length = row[3]
        min_length = row[4]
        
        print(f"\nLyrics Size Statistics:")
        print(f"  Avg Lyrics Length: {avg_length:,.0f} characters")
        print(f"  Avg Lyrics Size: {avg_bytes:,.0f} bytes")
        print(f"  Min Lyrics Length: {min_length:,} characters")
        print(f"  Max Lyrics Length: {max_length:,} characters")
        print(f"\nPotential Savings:")
        print(f"  Total Lyrics Size: {total_bytes:,.0f} bytes")
        print(f"  Total Lyrics Size: {total_bytes / (1024 * 1024):,.2f} MB")
        
        # Compare to current table size
        cur.execute("SELECT pg_relation_size('songs') as data_size")
        songs_data_size = cur.fetchone()[0]
        savings_pct = (total_bytes / songs_data_size) * 100
        print(f"\nComparison:")
        print(f"  Current Songs Table Data Size: {songs_data_size / (1024 * 1024):,.2f} MB")
        print(f"  Estimated Savings: ~{savings_pct:.1f}% of songs table data")
        print(f"  New Songs Table Size (estimate): ~{(songs_data_size - total_bytes) / (1024 * 1024):,.2f} MB")
    
    conn.close()

if __name__ == "__main__":
    import sys
    with open("db_size_output.txt", "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        main()
        sys.stdout = old_stdout
    print("Output written to db_size_output.txt")
