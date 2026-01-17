import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.movie_recommender import MovieRecommender
from services.song_recommender import SongRecommender
import pandas as pd

def debug_recommenders():
    print("="*60)
    print("Debugging Recommenders")
    print("="*60)

    # 1. Test Movie Recommender
    print("\n[1/2] Testing Movie Recommender...")
    try:
        mr = MovieRecommender()
        print("MovieRecommender initialized")
        
        # Test with dummy liked items
        liked_movies = [{"movieId": 1, "timestamp": None}] # Toy Story
        print(f"   Requesting recs for: {liked_movies}")
        
        recs = mr.recommend(liked_movies, n_recommendations=5)
        print(f"   Received {len(recs)} recommendations")
        if not recs.empty:
            print("   Top 3:")
            print(recs[["title", "year"]].head(3))
        else:
            print("   No movie recs returned!")
            
        mr.close()
    except Exception as e:
        print(f"   MovieRecommender Failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Test Song Recommender
    print("\n[2/2] Testing Song Recommender...")
    try:
        sr = SongRecommender()
        print("SongRecommender initialized")
        
        # Test with dummy liked items (Need a valid spotify ID from seed)
        # Using a common ID (hopefully in DB) or we need to find one
        # Let's try to query one first?
        # For now, let's try a dummy ID or just check if it handles empty/invalid gracefully
        # But we want to see SUCCESS.
        
        # Checking one ID from known seed or random?
        # Let's try to search first to get a valid ID
        print("   Searching for 'Yesterday' to get valid ID...")
        search_res = sr.search_songs("Yesterday", limit=1)
        
        if not search_res.empty:
            valid_id = search_res.iloc[0]["spotify_id"]
            title = search_res.iloc[0]["name"]
            print(f"   Found song: {title} ({valid_id})")
            
            liked_songs = [{"spotify_id": valid_id, "timestamp": None}]
            print(f"   Requesting recs for: {liked_songs}")
            
            recs = sr.recommend(liked_songs, n_recommendations=5)
            print(f"   Received {len(recs)} recommendations")
            if not recs.empty:
                print("   Top 3:")
                print(recs[["name", "year", "genre"]].head(3))
            else:
                print("   No song recs returned!")
        else:
            print("   Could not find a song to test with!")
            
        sr.close()
    except Exception as e:
        print(f"   SongRecommender Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_recommenders()
