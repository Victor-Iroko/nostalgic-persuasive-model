"""
Contextual Bandit for Nostalgic Recommendations using MAB2Rec.

This module implements a contextual bandit using the mab2rec library
with LinUCB policy for selecting optimal nostalgic content recommendations.

The bandit learns which content features work best in different
contexts (stress level, emotion, time of day, etc.).
"""

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy


# Type aliases
ContentType = Literal["song", "movie"]

# Default context dimension
# Components: stress(1) + emotion(7) + positive_rate(1) + birth_year(1) + padding(2) = 12
CONTEXT_DIM = 12


class LinUCBBandit:
    """
    LinUCB contextual bandit using MABWiser.
    
    LinUCB maintains a linear model for each arm and uses upper confidence
    bounds for exploration. It learns the relationship between context
    features and rewards for each arm (content type/genre).
    """

    def __init__(
        self,
        arms: list[str] | None = None,
        alpha: float = 1.0,
        context_dim: int = CONTEXT_DIM,
    ) -> None:
        """
        Initialize the LinUCB bandit.

        Args:
            arms: List of arm identifiers (e.g., content types/genres).
            alpha: Exploration parameter (higher = more exploration).
            context_dim: Number of context features.
        """
        # Default arms: genre-only (12 total)
        # Genre implicitly identifies content type (movie genres vs song genres don't overlap)
        if arms is None:
            movie_genres = ["drama", "comedy", "action", "romance", "thriller", "other_movie"]
            song_genres = ["pop", "rock", "hiphop", "rnb", "country", "other_song"]
            arms = movie_genres + song_genres
        
        self.arms = arms
        self.alpha = alpha
        self.context_dim = context_dim
        self.n_updates = 0
        
        # Initialize MABWiser with LinUCB policy
        self.mab = MAB(
            arms=arms,
            learning_policy=LearningPolicy.LinUCB(alpha=alpha),
        )
        
        # Track if we have any training data
        self._is_fitted = False

    def _get_arm_from_candidate(self, candidate: dict) -> str:
        """Map a candidate to its genre arm."""
        content_type = candidate.get("type", "movie")
        
        if content_type == "movie":
            raw_genre = candidate.get("genres", "")
            return normalize_movie_genre(raw_genre)
        else:
            raw_genre = candidate.get("genre", "")
            return normalize_song_genre(raw_genre)

    def _ensure_context_shape(self, context: np.ndarray) -> np.ndarray:
        """Ensure context has the right shape."""
        context = np.array(context).flatten()
        if len(context) < self.context_dim:
            context = np.pad(context, (0, self.context_dim - len(context)))
        elif len(context) > self.context_dim:
            context = context[:self.context_dim]
        return context.reshape(1, -1)

    def select(
        self,
        context: np.ndarray,
        candidates: list[dict],
    ) -> tuple[int, float]:
        """
        Select the best candidate using LinUCB.

        Args:
            context: Context feature vector.
            candidates: List of candidate content items.

        Returns:
            Tuple of (selected_index, score).
        """
        if not candidates:
            raise ValueError("No candidates provided")
        
        context_2d = self._ensure_context_shape(context)
        
        # If not fitted yet, select randomly
        if not self._is_fitted:
            import random
            idx = random.randint(0, len(candidates) - 1)
            return idx, 0.5
        
        # Map candidates to arms
        candidate_arms = [self._get_arm_from_candidate(c) for c in candidates]
        
        # Get prediction from MAB for each candidate's arm
        scores = []
        for i, arm in enumerate(candidate_arms):
            if arm in self.arms:
                # Get expectation for this arm given context
                expectations = self.mab.predict_expectations(context_2d)
                score = expectations.get(arm, 0.5)
            else:
                score = 0.5
            scores.append((i, score))
        
        # Sort by score and return best
        scores.sort(key=lambda x: x[1], reverse=True)
        best_idx, best_score = scores[0]
        
        return best_idx, float(best_score)

    def update(
        self,
        context: np.ndarray,
        candidate: dict,
        reward: float,
    ) -> None:
        """
        Update the bandit with observed reward.

        Args:
            context: Context feature vector.
            candidate: The candidate that was shown.
            reward: Observed reward (0-1).
        """
        context_2d = self._ensure_context_shape(context)
        arm = self._get_arm_from_candidate(candidate)
        
        # Convert reward to binary decision for simpler learning
        decision = arm
        binary_reward = 1 if reward > 0.5 else 0
        
        if not self._is_fitted:
            # First fit
            self.mab.fit(
                decisions=[decision],
                rewards=[binary_reward],
                contexts=context_2d,
            )
            self._is_fitted = True
        else:
            # Incremental update
            self.mab.partial_fit(
                decisions=[decision],
                rewards=[binary_reward],
                contexts=context_2d,
            )
        
        self.n_updates += 1

    def warm_start(self, decisions: list[str], rewards: list[float], contexts: np.ndarray) -> None:
        """
        Warm start the bandit with historical data.

        Args:
            decisions: List of arm decisions.
            rewards: List of rewards.
            contexts: Context matrix (n_samples, context_dim).
        """
        if len(decisions) == 0:
            return
            
        self.mab.fit(
            decisions=decisions,
            rewards=rewards,
            contexts=contexts,
        )
        self._is_fitted = True
        self.n_updates = len(decisions)

    def save(self, filepath: Path) -> None:
        """Save full bandit model using joblib."""
        data = {
            "arms": self.arms,
            "alpha": self.alpha,
            "context_dim": self.context_dim,
            "n_updates": self.n_updates,
            "is_fitted": self._is_fitted,
            "mab": self.mab if self._is_fitted else None,
        }
        joblib.dump(data, filepath)

    @classmethod
    def load(cls, filepath: Path) -> "LinUCBBandit":
        """Load full bandit model from joblib file."""
        data = joblib.load(filepath)
        bandit = cls(
            arms=data["arms"],
            alpha=data["alpha"],
            context_dim=data["context_dim"],
        )
        bandit.n_updates = data.get("n_updates", 0)
        bandit._is_fitted = data.get("is_fitted", False)
        if data.get("mab") is not None:
            bandit.mab = data["mab"]
        return bandit

    def to_dict(self) -> dict:
        """Serialize bandit state (metadata only, for backward compat)."""
        return {
            "arms": self.arms,
            "alpha": self.alpha,
            "context_dim": self.context_dim,
            "n_updates": self.n_updates,
            "is_fitted": self._is_fitted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LinUCBBandit":
        """Create bandit from dict (metadata only, no model weights)."""
        bandit = cls(
            arms=data["arms"],
            alpha=data["alpha"],
            context_dim=data["context_dim"],
        )
        bandit.n_updates = data.get("n_updates", 0)
        bandit._is_fitted = data.get("is_fitted", False)
        return bandit


class HierarchicalBandit:
    """
    Hierarchical bandit with global and per-user LinUCB models.
    
    - Global model learns from all users
    - Per-user models refine predictions for individual users
    - Blends predictions based on user's feedback history
    """

    def __init__(
        self,
        models_dir: str | Path,
        alpha: float = 1.0,
        min_user_updates: int = 10,
    ) -> None:
        """
        Initialize hierarchical bandit.

        Args:
            models_dir: Directory to save/load models.
            alpha: LinUCB exploration parameter.
            min_user_updates: Minimum updates before using per-user model.
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.alpha = alpha
        self.min_user_updates = min_user_updates
        
        # Load or create global model
        self.global_model = self._load_or_create_global()
        
        # Per-user models (lazy loaded)
        self.user_models: dict[str, LinUCBBandit] = {}

    def _load_or_create_global(self) -> LinUCBBandit:
        """Load global model from disk or create new one."""
        repo_id = os.getenv("HF_REPO_ID")
            
        if repo_id:
            print(f"Loading global bandit from Hugging Face Hub: {repo_id}...")
            try:
                from huggingface_hub import hf_hub_download
                model_path = hf_hub_download(repo_id=repo_id, filename="bandit/global_bandit.joblib")
                bandit = LinUCBBandit.load(Path(model_path))
                print(f"   Loaded global bandit from HF Hub with {bandit.n_updates} updates (full model)")
                return bandit
            except Exception as e:
                print(f"⚠ Failed to load global bandit from HF Hub: {e}")
                print("Falling back to local models...")

        # Try joblib first (full model)
        joblib_path = self.models_dir / "global_bandit.joblib"
        if joblib_path.exists():
            try:
                bandit = LinUCBBandit.load(joblib_path)
                print(f"   Loaded global bandit with {bandit.n_updates} updates (full model)")
                return bandit
            except Exception as e:
                print(f"   Could not load global bandit joblib: {e}")
        
        # Fallback to JSON (metadata only)
        json_path = self.models_dir / "global_bandit.json"
        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)
                print(f"   Loaded global bandit metadata ({data.get('n_updates', 0)} updates)")
                return LinUCBBandit.from_dict(data)
            except Exception as e:
                print(f"   Could not load global bandit json: {e}")
        
        return LinUCBBandit(alpha=self.alpha)

    def _save_global(self) -> None:
        """Save global model to disk using joblib."""
        joblib_path = self.models_dir / "global_bandit.joblib"
        self.global_model.save(joblib_path)

    def _load_user_model(self, user_id: str) -> LinUCBBandit | None:
        """Load per-user model from disk."""
        # Try joblib first
        joblib_path = self.models_dir / f"user_{user_id}.joblib"
        if joblib_path.exists():
            try:
                return LinUCBBandit.load(joblib_path)
            except Exception:
                pass
        
        # Fallback to JSON
        json_path = self.models_dir / f"user_{user_id}.json"
        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)
                return LinUCBBandit.from_dict(data)
            except Exception:
                pass
        return None

    def _save_user_model(self, user_id: str) -> None:
        """Save per-user model to disk using joblib."""
        if user_id in self.user_models:
            joblib_path = self.models_dir / f"user_{user_id}.joblib"
            self.user_models[user_id].save(joblib_path)

    def get_user_model(self, user_id: str) -> LinUCBBandit:
        """Get or create per-user model."""
        if user_id not in self.user_models:
            loaded = self._load_user_model(user_id)
            if loaded:
                self.user_models[user_id] = loaded
            else:
                self.user_models[user_id] = LinUCBBandit(alpha=self.alpha)
        return self.user_models[user_id]

    def select(
        self,
        user_id: str,
        context: np.ndarray,
        candidates: list[dict],
    ) -> tuple[int, float]:
        """
        Select the best candidate using hierarchical bandit.

        Args:
            user_id: User identifier.
            context: Context feature vector.
            candidates: List of candidate content items.

        Returns:
            Tuple of (selected_index, bandit_score).
        """
        if not candidates:
            raise ValueError("No candidates provided")

        # Try global model first
        try:
            global_idx, global_score = self.global_model.select(context, candidates)
        except Exception as e:
            print(f"Global model selection error: {e}")
            import random
            return random.randint(0, len(candidates) - 1), 0.5
        
        # Get user model
        user_model = self.get_user_model(user_id)
        
        # Blend if user has enough history
        if user_model.n_updates >= self.min_user_updates:
            try:
                user_idx, user_score = user_model.select(context, candidates)
                
                # Calculate blend weight
                blend = min(user_model.n_updates / 50, 0.7)
                
                # Use weighted selection
                if user_score * blend > global_score * (1 - blend):
                    return user_idx, user_score
            except Exception:
                pass
        
        return global_idx, global_score

    def update(
        self,
        user_id: str,
        context: np.ndarray,
        candidate: dict,
        reward: float,
    ) -> None:
        """
        Update both global and per-user models with reward.

        Args:
            user_id: User identifier.
            context: Context feature vector.
            candidate: The candidate that was shown.
            reward: Observed reward (0-1).
        """
        # Update global model
        try:
            self.global_model.update(context, candidate, reward)
            self._save_global()
        except Exception as e:
            print(f"Global model update error: {e}")
        
        # Update per-user model
        try:
            user_model = self.get_user_model(user_id)
            user_model.update(context, candidate, reward)
            self._save_user_model(user_id)
        except Exception as e:
            print(f"User model update error: {e}")

    def warm_start_user(
        self,
        user_id: str,
        selected_items: list[dict],
        context: np.ndarray | None = None,
    ) -> None:
        """
        Warm-start user model with onboarding selections.

        Args:
            user_id: User identifier.
            selected_items: List of items user selected during onboarding.
            context: Optional context (uses neutral context if not provided).
        """
        if not selected_items:
            return
            
        if context is None:
            # Neutral context
            context = np.zeros(CONTEXT_DIM)
            context[0] = 0.3  # Neutral stress
            context[5] = 1.0  # Neutral emotion
        
        user_model = self.get_user_model(user_id)
        
        # Build training data from selections
        decisions = []
        rewards = []
        contexts = []
        
        for item in selected_items:
            arm = user_model._get_arm_from_candidate(item)
            decisions.append(arm)
            rewards.append(1)  # Selection = positive
            contexts.append(context)
        
        if decisions:
            contexts_array = np.array(contexts)
            user_model.warm_start(decisions, rewards, contexts_array)
            self._save_user_model(user_id)

    def close(self) -> None:
        """Save all models and clean up."""
        self._save_global()
        for user_id in self.user_models:
            self._save_user_model(user_id)


def build_context_features(
    stress_score: float,
    emotion: str,
    birth_year: int | None = None,
    user_positive_rate: float = 0.5,
) -> np.ndarray:
    """
    Build context feature vector from user state.

    Args:
        stress_score: Stress level (0-1).
        emotion: Detected emotion.
        birth_year: User's birth year (for age-based context).
        user_positive_rate: User's historical positive feedback rate.

    Returns:
        Context feature vector (12 dimensions).
    """
    features = []
    
    # Stress (1 feature)
    features.append(stress_score)
    
    # Emotion one-hot (7 features)
    emotions = ["anger", "fear", "joy", "love", "neutral", "sadness", "surprise"]
    for e in emotions:
        features.append(1.0 if emotion == e else 0.0)
    
    # User's historical positive rate (1 feature)
    features.append(user_positive_rate)

    # Birth Year (Normalized) (1 feature)
    # Normalize around 2000 with a scale of 40 years (range ~1960-2040)
    if birth_year:
        norm_birth_year = (birth_year - 2000) / 40.0
    else:
        norm_birth_year = 0.0  # Default to 2000
    features.append(norm_birth_year)
    
    # Pad to CONTEXT_DIM
    while len(features) < CONTEXT_DIM:
        features.append(0.0)
    
    return np.array(features[:CONTEXT_DIM], dtype=np.float32)


def calculate_reward(
    brings_back_memories: bool,
) -> float:
    """
    Calculate reward from user feedback.

    Args:
        brings_back_memories: Primary signal from user feedback.

    Returns:
        Reward (0-1).
    """
    # Simple binary reward for now
    # Can be expanded to include other immediate signals like rating/like/share
    return 1.0 if brings_back_memories else 0.0


# =============================================================================
# Genre Normalization
# =============================================================================

MOVIE_GENRE_MAP: dict[str, str] = {
    "drama": "drama",
    "comedy": "comedy",
    "action": "action",
    "adventure": "action",
    "romance": "romance",
    "thriller": "thriller",
    "horror": "thriller",
    "crime": "thriller",
    "sci-fi": "action",
    "science fiction": "action",
    "animation": "comedy",
    "family": "comedy",
    "fantasy": "action",
    "mystery": "thriller",
    "war": "drama",
    "western": "action",
    "documentary": "other_movie",
    "musical": "comedy",
    "history": "drama",
}

SONG_GENRE_MAP: dict[str, str] = {
    "pop": "pop",
    "rock": "rock",
    "alternative": "rock",
    "indie": "rock",
    "hip hop": "hiphop",
    "hip-hop": "hiphop",
    "rap": "hiphop",
    "r&b": "rnb",
    "rnb": "rnb",
    "soul": "rnb",
    "country": "country",
    "folk": "country",
    "blues": "rnb",
    "electronic": "pop",
    "dance": "pop",
    "edm": "pop",
    "jazz": "other_song",
    "classical": "other_song",
    "metal": "rock",
    "punk": "rock",
    "reggae": "other_song",
    "latin": "pop",
}


def normalize_movie_genre(raw: str) -> str:
    """Normalize movie genre to one of 6 categories."""
    if not raw:
        return "other_movie"
    # Handle both string and list formats
    if isinstance(raw, list):
        first_genre = raw[0].lower().strip() if raw else ""
    else:
        first_genre = str(raw).split("|")[0].lower().strip()
    return MOVIE_GENRE_MAP.get(first_genre, "other_movie")


def normalize_song_genre(raw: str) -> str:
    """Normalize song genre to one of 6 categories."""
    if not raw:
        return "other_song"
    genre = str(raw).lower().strip()
    return SONG_GENRE_MAP.get(genre, "other_song")


# =============================================================================
# Nostalgia Scoring
# =============================================================================

def age_nostalgia(
    age_at_release: int,
    peak_age: float = 13.0,
    width: float = 8.0,
    prebirth_decay: float = 0.03,
) -> float:
    """
    Age-based nostalgia score.
    
    - Post-birth: Gaussian centered at peak_age (reminiscence bump)
    - Pre-birth: Exponential decay from birth point
    
    Args:
        age_at_release: User's age when content was released (can be negative)
        peak_age: Peak nostalgia age (default 13, based on psychology research)
        width: Gaussian width (default 8)
        prebirth_decay: Decay rate for pre-birth content (default 0.03)
    
    Returns:
        Age nostalgia score (0-1)
    """
    if age_at_release >= 0:
        return math.exp(-((age_at_release - peak_age) ** 2) / (2 * width ** 2))
    else:
        birth_score = math.exp(-((0 - peak_age) ** 2) / (2 * width ** 2))
        return birth_score * math.exp(-prebirth_decay * abs(age_at_release))


def popularity_score(rating_count: float, max_count: float) -> float:
    """
    Log-scaled popularity score to prevent mega-hits from dominating.
    
    Args:
        rating_count: Number of ratings for this content
        max_count: Maximum rating count in dataset
    
    Returns:
        Popularity score (0-1)
    """
    if rating_count <= 0 or max_count <= 0:
        return 0.0
    return math.log1p(rating_count) / math.log1p(max_count)


def nostalgia_score(
    birth_year: int,
    release_year: int,
    rating_count: float,
    max_count: float,
    use_linear: bool = False,
) -> float:
    """
    Combined nostalgia score. Popularity BOOSTS but cannot CREATE nostalgia.
    
    Formula: personal * (0.7 + 0.3 * pop) + cultural
    - personal: age-based nostalgia (lived experience)
    - cultural: popularity boost for pre-birth content (inherited memory)
    
    Note: Recency filtering (10-year minimum) is handled at the recommender level,
    so all content passed here is already guaranteed to be old enough.
    
    Args:
        birth_year: User's birth year
        release_year: Content release year
        rating_count: Number of ratings for this content
        max_count: Maximum rating count in dataset
        use_linear: If True, use linear scaling (value/max) instead of log scaling.
                    Use for pre-normalized scores like Spotify popularity (0-100).
    
    Returns:
        Nostalgia score (0-1)
    """
    age_at_release = release_year - birth_year

    age_score = age_nostalgia(age_at_release)
    
    # Use linear scaling for pre-normalized scores (e.g., Spotify popularity 0-100)
    # Use log scaling for raw counts (e.g., MovieLens rating_count)
    if use_linear:
        pop_score = min(1.0, rating_count / max_count) if max_count > 0 else 0.0
    else:
        pop_score = popularity_score(rating_count, max_count)

    # Personal nostalgia (lived experience)
    personal = age_score

    # Cultural nostalgia (only for pre-birth content)
    cultural = pop_score * 0.4 if age_at_release < 0 else 0.0

    # Final score: popularity boosts but doesn't create nostalgia
    final = personal * (0.7 + 0.3 * pop_score) + cultural

    return round(min(1.0, max(0.0, final)), 3)

