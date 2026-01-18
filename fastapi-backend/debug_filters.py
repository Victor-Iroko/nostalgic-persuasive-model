
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from services.movie_recommender import MovieRecommender
from services.song_recommender import SongRecommender

def debug_movie_recommender():
    print("\n=== Debugging Movie Recommender ===")
    try:
        recommender = MovieRecommender()
        print("MovieRecommender initialized.")
        
        # 1. Check Cache
        print("\nChecking _old_movie_cache...")
        cache = recommender._old_movie_cache
        metadata = cache.get('metadata', {})
        if not metadata:
            print("CACHE EMPTY!")
        else:
            years = [m['year'] for m in metadata.values()]
            if years:
                print(f"Cache Size: {len(years)}")
                print(f"Max Year in Cache: {max(years)}")
                print(f"Min Year in Cache: {min(years)}")
                
                recent_movies = [y for y in years if y > (datetime.now().year - 10)]
                if recent_movies:
                    print(f"FAIL: Found {len(recent_movies)} recent movies in cache! Examples: {recent_movies[:5]}")
                else:
                    print("PASS: Cache contains only old movies.")
        
        # 2. Check Search
        print("\nChecking search_movies(min_years_old=10)...")
        results = recommender.search_movies("Love", limit=20, min_years_old=10)
        max_search_year = results['year'].max() if not results.empty and 'year' in results else 0
        print(f"Max Year in Search Results: {max_search_year}")
        if not results.empty:
             over_limit = results[results['year'] > (datetime.now().year - 10)]
             if not over_limit.empty:
                 print(f"FAIL: Search results contain recent movies:\n{over_limit[['title', 'year']]}")
             else:
                 print("PASS: Search results clean.")

        # 3. Check Recommend (Fallback)
        print("\nChecking recommend() [Fallback]...")
        # Empty input triggers fallback
        recs = recommender.recommend([], n_recommendations=10, min_years_old=10)
        if not recs.empty:
            max_rec_year = recs['year'].max()
            print(f"Max Year in Fallback Recommendations: {max_rec_year}")
            over_limit = recs[recs['year'] > (datetime.now().year - 10)]
            if not over_limit.empty:
                 print(f"FAIL: Fallback results contain recent movies:\n{over_limit[['title', 'year']]}")
            else:
                 print("PASS: Fallback results clean.")
        else:
            print("Warning: Fallback returned empty df.")

    except Exception as e:
        print(f"Error debugging movies: {e}")
        import traceback
        traceback.print_exc()

def debug_song_recommender():
    print("\n=== Debugging Song Recommender ===")
    try:
        recommender = SongRecommender()
        print("SongRecommender initialized.")
        
        # 1. Check Search
        print("\nChecking search_songs(min_years_old=10)...")
        results = recommender.search_songs("Love", limit=20, min_years_old=10)
        if not results.empty:
             max_search_year = results['year'].max()
             print(f"Max Year in Search Results: {max_search_year}")
             over_limit = results[results['year'] > (datetime.now().year - 10)]
             if not over_limit.empty:
                 print(f"FAIL: Search results contain recent songs:\n{over_limit[['name', 'year']]}")
             else:
                 print("PASS: Search results clean.")
        else:
            print("No search results found.")

        # 2. Check Recommend (Random Fallback doesn't use filter yet? Or does it?)
        # Wait, SongRecommender.recommend fallback calls _get_random_recommendations
        # Let's check ordinary recommend with dummy input
        print("\nChecking recommend() [Vector Search]...")
        # Get a real song ID to use
        conn = recommender._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT spotify_id FROM song_vectors LIMIT 1")
        sid = cur.fetchone()[0]
        cur.close()
        
        recs = recommender.recommend([{'spotify_id': sid, 'timestamp': None}], n_recommendations=10, min_years_old=10)
        if not recs.empty:
            max_rec_year = recs['year'].max()
            print(f"Max Year in Recommendations: {max_rec_year}")
            over_limit = recs[recs['year'] > (datetime.now().year - 10)]
            if not over_limit.empty:
                 print(f"FAIL: Recommendations contain recent songs:\n{over_limit[['name', 'year']]}")
            else:
                 print("PASS: Recommendations clean.")
        else:
            print("Warning: Recommendations returned empty.")

    except Exception as e:
        print(f"Error debugging songs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    with open("debug_results.log", "w", encoding="utf-8") as f:
        sys.stdout = f
        try:
            debug_movie_recommender()
            debug_song_recommender()
        except Exception as e:
            print(f"FATAL ERROR: {e}")

