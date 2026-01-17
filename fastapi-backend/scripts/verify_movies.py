import pandas as pd
import sys
import os
import datetime
import numpy as np

# Add parent directory (fastapi-backend) to path
sys.path.insert(0, "..")

from services.movie_recommender import MovieRecommender

def test_movies():
    print("--- Testing MovieRecommender ---\n")
    
    try:
        recommender = MovieRecommender(database_url=os.getenv("DATABASE_URL"))
    except Exception as e:
        print(f"Failed to init: {e}")
        return

    # 1. Search for Seed Movies
    print("Searching for seed movies...")
    # Seed 1: Action/Sci-Fi (Old Interest)
    matrix_res = recommender.search_movies("The Matrix", limit=1)
    # Seed 2: Animation/Children (New Interest)
    toy_res = recommender.search_movies("Toy Story", limit=1)
    
    if matrix_res.empty or toy_res.empty:
        print("Could not find seed movies (Matrix or Toy Story).")
        return
        
    matrix = matrix_res.iloc[0]
    toy = toy_res.iloc[0]
    
    print(f"  Seed A (Old): {matrix['title']} ({matrix['decade']}) [ID: {matrix['movieId']}]")
    print(f"  Seed B (New): {toy['title']} ({toy['decade']}) [ID: {toy['movieId']}]")

    # 2. Test Recency Weighting
    # Scenario: User liked Matrix 2 years ago, but liked Toy Story TODAY.
    # Expectation: Recommendations should be dominated by Animation, not mixed 50/50.
    
    print("\n[Test] Recency Weighting")
    print("  User Profile: Liked 'Matrix' (700 days ago) vs 'Toy Story' (0 days ago)")
    
    now = datetime.datetime.now()
    old_date = now - datetime.timedelta(days=700)
    
    liked_items = [
        {"movieId": int(matrix['movieId']), "timestamp": old_date.isoformat()},
        {"movieId": int(toy['movieId']), "timestamp": now.isoformat()}
    ]
    
    recs = recommender.recommend(liked_items, n_recommendations=10)
    
    print(f"\nResults ({len(recs)}):")
    print(f"{'Title':<30} | {'Genres':<20} | {'Score':<6}")
    print("-" * 65)
    
    animation_count = 0
    action_count = 0
    
    for _, row in recs.iterrows():
        title = row['title'][:27] + ".." if len(row['title']) > 27 else row['title']
        genres = row['genres'][:17] + ".." if len(row['genres']) > 17 else row['genres']
        score = f"{row['score']:.2f}"
        
        print(f"{title:<30} | {genres:<20} | {score}")
        
        if "Animation" in row['genres'] or "Children" in row['genres']:
            animation_count += 1
        if "Action" in row['genres'] or "Sci-Fi" in row['genres']:
            action_count += 1
            
    print(f"\nAnalysis:")
    print(f"  Animation/Children Matches: {animation_count}/10")
    print(f"  Action/Sci-Fi Matches:      {action_count}/10")
    
    if animation_count > action_count:
        print("  SUCCESS: Model successfully drifted towards the recent interest (Toy Story).")
    else:
        print("  RESULT: Recommendations are mixed or sticky to old history.")

    recommender.close()

if __name__ == "__main__":
    test_movies()
