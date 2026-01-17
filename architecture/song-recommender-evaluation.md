# Song Content-Based Recommender: Nostalgia-Focused Evaluation

## 1. Introduction

This document presents the evaluation methodology for the nostalgia-focused song recommendation system. Unlike traditional recommender evaluation that measures self-consistency (embedding similarity, genre precision), this system is evaluated on **what humans actually remember**—temporal context, emotional feel, and cultural associations.

## 2. Evaluation Philosophy

### 2.1 Core Principle

> **Never evaluate on features that are heavily weighted in the embedding.**

Evaluating on embedding features (e.g., genre precision when genre is in the embedding) only measures self-consistency, not recommendation quality. Instead, we evaluate on:

1. **Holdout features** - Not used in embedding generation
2. **Tolerance bands** - "Same era" not "same year"
3. **Human memory patterns** - What triggers nostalgia

### 2.2 Feature Classification

| Category            | Features                             | In Embedding?  | Evaluated?         |
| ------------------- | ------------------------------------ | -------------- | ------------------ |
| **Anchor**          | year, genre                          | Yes (moderate) | Loosely (±5 years) |
| **Style**           | valence, energy, tempo, acousticness | Yes            | Tolerance bands    |
| **Evaluation-Only** | popularity, duration, artists        | **No**         | Primary metrics    |

## 3. Evaluation Metrics

### 3.1 Era Recall (HEADLINE METRIC)

**Definition:** Percentage of recommendations within ±5 years of the query track.

$$\text{Era Recall} = \frac{|\{r : |year_r - year_q| \leq 5\}|}{K}$$

**Why it matters:**

- Nostalgia is time-anchored—humans remember music in **eras**, not exact years
- Strong nostalgic response requires temporal coherence
- ±5 years captures an "era" (e.g., early 2000s, late 90s)

**Interpretation:**

- ≥70%: Excellent era coherence
- 50-70%: Acceptable
- <50%: Poor temporal alignment

### 3.2 Popularity Drift

**Definition:** Mean difference in popularity between query and recommendations.

$$\text{Popularity Drift} = \frac{1}{K} \sum_{i=1}^{K} (popularity_{r_i} - popularity_q)$$

**Why it matters:**

- Nostalgia works best with a mix of remembered favorites AND forgotten songs
- Slightly negative drift indicates good discovery potential
- Zero drift suggests overly safe recommendations

**Interpretation:**

- -15 to 0: Ideal—recommends slightly less popular songs for discovery
- 0 to +10: Neutral—similar popularity
- > +10: Generic—only recommending top hits

### 3.3 Artist/Scene Continuity

**Definition:** Percentage of recommendations sharing at least one artist with query.

$$\text{Artist Continuity} = \frac{|\{r : artists_r \cap artists_q \neq \emptyset\}|}{K}$$

**Why it matters:**

- People remember **scenes and phases**, not just genres
- Same artist from that era triggers strong nostalgia
- Too high (>50%) indicates lack of diversity

**Interpretation:**

- 20-40%: Ideal balance of familiarity and discovery
- > 50%: Too repetitive
- <10%: Missing scene context

### 3.4 Mood Consistency

**Definition:** Percentage of recommendations within tolerance bands for mood features.

A recommendation is "mood consistent" if at least 2 of 3 conditions hold:

- $|valence_r - valence_q| \leq 0.15$
- $|energy_r - energy_q| \leq 0.15$
- $|danceability_r - danceability_q| \leq 0.15$

**Why it matters:**

- Nostalgia has emotional texture
- Similar "feel" matters more than exact audio match
- Tolerance bands avoid the "99.9% similarity" trap

**Interpretation:**

- ≥60%: Strong mood coherence
- 40-60%: Acceptable
- <40%: Inconsistent emotional feel

### 3.5 Duration Familiarity

**Definition:** Percentage of recommendations within ±15 seconds of query duration.

$$\text{Duration Familiarity} = \frac{|\{r : |duration_r - duration_q| \leq 15s\}|}{K}$$

**Why it matters:**

- Song duration is era-specific (2010s songs tend to be shorter)
- Similar duration reflects cultural context
- Not a primary metric, but adds texture

**Interpretation:**

- ≥50%: Strong era signal
- 30-50%: Acceptable
- <30%: Era mismatch (not critical)

## 4. Results

The model achieved the following results on 100 random queries with 10 recommendations each:

| Metric                      | Value            | Status |
| --------------------------- | ---------------- | ------ |
| Era Recall (±5 years)       | _Run evaluation_ | —      |
| Popularity Drift (mean Δ)   | _Run evaluation_ | —      |
| Artist/Scene Continuity     | _Run evaluation_ | —      |
| Mood Consistency (±0.15)    | _Run evaluation_ | —      |
| Duration Familiarity (±15s) | _Run evaluation_ | —      |

> [!NOTE]
> Run the evaluation script to generate actual metrics:
>
> ```bash
> python song_evaluation.py
> ```

## 5. Metrics NOT Used

The following traditional metrics are **explicitly excluded**:

| ❌ Metric               | Why Excluded                                    |
| ----------------------- | ----------------------------------------------- |
| Genre Precision         | Genre is in embedding—measures self-consistency |
| Embedding Distance      | Self-consistency metric                         |
| Audio Cosine Similarity | Optimized directly, not externally valid        |
| Exact Year Match        | Era matters, not exact year                     |

These metrics answer "are embeddings close?" not "does this feel nostalgic?"

## 6. Technical Implementation

### 6.1 Model Artifacts

| File                      | Description                             |
| ------------------------- | --------------------------------------- |
| `audio_scaler.joblib`     | StandardScaler for style audio features |
| `genre_encoder.joblib`    | OneHotEncoder for anchor genre          |
| `tfidf_vectorizer.joblib` | TfidfVectorizer for niche genres        |
| `training_config.joblib`  | Feature weights and configuration       |
| `evaluation_results.json` | Nostalgia metrics output                |

### 6.2 Feature Weights (Training)

| Feature Type   | Weight | Rationale                               |
| -------------- | ------ | --------------------------------------- |
| Year           | 1.5×   | Anchor—important but not over-optimized |
| Genre          | 1.2×   | Category anchor                         |
| Audio Features | 1.0×   | Style—captures sonic feel               |
| Niche Genres   | 0.8×   | Scene context                           |

### 6.3 Evaluation Parameters

| Parameter          | Value       |
| ------------------ | ----------- |
| Era Window         | ±5 years    |
| Mood Tolerance     | ±0.15       |
| Duration Tolerance | ±15 seconds |
| Queries            | 100         |
| Recommendations    | 10          |

## 7. Conclusion

This nostalgia-focused evaluation methodology represents a paradigm shift from traditional recommender metrics. By evaluating on **what humans remember** rather than embedding consistency, we obtain honest, meaningful measurements of recommendation quality for nostalgic experiences.

The key insight: a 70% era recall is more meaningful than 99% genre precision, because era recall measures something independent of the embedding optimization objective.

## References

1. Juslin, P. N., & Västfjäll, D. (2008). Emotional responses to music: The need to consider underlying mechanisms. Behavioral and Brain Sciences, 31(5), 559-575.

2. Janata, P., Tomic, S. T., & Rakowski, S. K. (2007). Characterisation of music-evoked autobiographical memories. Memory, 15(8), 845-860.

3. Barrett, F. S., et al. (2010). Music-evoked nostalgia: Affect, memory, and personality. Emotion, 10(3), 390-403.
