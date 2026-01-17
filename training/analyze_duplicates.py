"""
Analyze duplicates in the songs dataset.
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Setup
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp")


def analyze_duplicates() -> None:
    """Analyze near-duplicate songs in the dataset."""
    print("=" * 70)
    print("SONG DATASET DUPLICATE ANALYSIS")
    print("=" * 70 + "\n")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Total songs
    cursor.execute("SELECT COUNT(*) FROM songs;")
    total_songs = cursor.fetchone()[0]
    print(f"Total songs in database: {total_songs:,}")

    # 1. Exact title duplicates (same name, same artist)
    print("\n" + "-" * 70)
    print("1. EXACT DUPLICATES (same title + same artists)")
    print("-" * 70)
    cursor.execute("""
        SELECT name, artists, COUNT(*) as cnt
        FROM songs
        GROUP BY name, artists
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 20;
    """)
    exact_dups = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT name, artists
            FROM songs
            GROUP BY name, artists
            HAVING COUNT(*) > 1
        ) t;
    """)
    n_exact_dup_groups = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT SUM(cnt) - COUNT(*) FROM (
            SELECT name, artists, COUNT(*) as cnt
            FROM songs
            GROUP BY name, artists
            HAVING COUNT(*) > 1
        ) t;
    """)
    n_exact_dup_extra = cursor.fetchone()[0] or 0
    
    print(f"  Groups with duplicates: {n_exact_dup_groups:,}")
    print(f"  Extra rows (could be removed): {n_exact_dup_extra:,}")
    print(f"  Percentage of dataset: {n_exact_dup_extra / total_songs * 100:.2f}%")
    print("\n  Top 10 most duplicated (same title+artist):")
    for name, artists, cnt in exact_dups[:10]:
        print(f"    {cnt}x: {name[:50]:<50} by {str(artists)[:30]}")

    # 2. Title duplicates (same name, different artist or release)
    print("\n" + "-" * 70)
    print("2. TITLE DUPLICATES (same title, any artist)")
    print("-" * 70)
    cursor.execute("""
        SELECT name, COUNT(*) as cnt, COUNT(DISTINCT artists) as n_artists
        FROM songs
        GROUP BY name
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 20;
    """)
    title_dups = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT name
            FROM songs
            GROUP BY name
            HAVING COUNT(*) > 1
        ) t;
    """)
    n_title_dup_groups = cursor.fetchone()[0]
    
    print(f"  Titles appearing more than once: {n_title_dup_groups:,}")
    print("\n  Top 10 most common titles:")
    for name, cnt, n_artists in title_dups[:10]:
        print(f"    {cnt}x ({n_artists} artists): {name[:60]}")

    # 3. Same artist + title with variants (live, remix, etc.)
    print("\n" + "-" * 70)
    print("3. VARIANTS (same artist, title contains original)")
    print("-" * 70)
    cursor.execute("""
        SELECT 
            name,
            artists,
            year
        FROM songs
        WHERE 
            name ILIKE '%remix%'
            OR name ILIKE '%live%'
            OR name ILIKE '%remaster%'
            OR name ILIKE '%acoustic%'
            OR name ILIKE '%radio edit%'
            OR name ILIKE '%version%'
        LIMIT 20;
    """)
    variants = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM songs
        WHERE 
            name ILIKE '%remix%'
            OR name ILIKE '%live%'
            OR name ILIKE '%remaster%'
            OR name ILIKE '%acoustic%'
            OR name ILIKE '%radio edit%'
            OR name ILIKE '%version%';
    """)
    n_variants = cursor.fetchone()[0]
    
    print(f"  Songs with variant keywords: {n_variants:,}")
    print(f"  Percentage of dataset: {n_variants / total_songs * 100:.2f}%")
    print("\n  Sample variants:")
    for name, artists, year in variants[:10]:
        print(f"    {name[:60]:<60} ({year})")

    # 4. Same artist, same year, similar title length (likely re-releases)
    print("\n" + "-" * 70)
    print("4. LIKELY RE-RELEASES (same artist+title, different year)")
    print("-" * 70)
    cursor.execute("""
        SELECT 
            name,
            artists,
            COUNT(DISTINCT year) as n_years,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM songs
        WHERE year IS NOT NULL
        GROUP BY name, artists
        HAVING COUNT(DISTINCT year) > 1
        ORDER BY n_years DESC
        LIMIT 20;
    """)
    rereleases = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT name, artists
            FROM songs
            WHERE year IS NOT NULL
            GROUP BY name, artists
            HAVING COUNT(DISTINCT year) > 1
        ) t;
    """)
    n_rereleases = cursor.fetchone()[0]
    
    print(f"  Songs with multiple release years: {n_rereleases:,}")
    print("\n  Top 10 most re-released:")
    for name, artists, n_years, min_year, max_year in rereleases[:10]:
        print(f"    {n_years} years ({min_year}-{max_year}): {name[:40]:<40} by {str(artists)[:25]}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total songs:                    {total_songs:>10,}")
    print(f"  Exact duplicates (extra rows):  {n_exact_dup_extra:>10,} ({n_exact_dup_extra/total_songs*100:.1f}%)")
    print(f"  Variant tracks (remix/live/etc):{n_variants:>10,} ({n_variants/total_songs*100:.1f}%)")
    print(f"  Re-releases (diff years):       {n_rereleases:>10,}")
    
    # Save summary to file
    summary = f"""SONG DATASET DUPLICATE ANALYSIS
================================
Total songs:                    {total_songs:,}
Exact duplicates (extra rows):  {n_exact_dup_extra:,} ({n_exact_dup_extra/total_songs*100:.1f}%)
Variant tracks (remix/live/etc):{n_variants:,} ({n_variants/total_songs*100:.1f}%)
Re-releases (diff years):       {n_rereleases:,}
"""
    output_file = Path(__file__).parent / "duplicate_analysis_results.txt"
    with open(output_file, "w") as f:
        f.write(summary)
    print(f"\n✅ Results saved to {output_file}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    analyze_duplicates()
