# LightFM Movie Recommender: Evaluation Metrics and Performance Analysis

## 1. Introduction

This document presents a comprehensive analysis of the evaluation metrics and performance of the LightFM-based movie recommendation model. The system employs matrix factorization techniques with hybrid collaborative filtering to generate personalized movie recommendations based on user-item interactions and item metadata.

## 2. Model Architecture

### 2.1 Algorithm Selection

The recommendation system utilizes **LightFM**, a Python implementation of hybrid recommendation algorithms that combines the strengths of collaborative filtering and content-based methods. LightFM is particularly effective for recommendation scenarios with sparse interaction data, as it can leverage item features to make predictions even for items with limited user interactions.

### 2.2 Model Configuration

The model was configured with the following hyperparameters:

| Parameter        | Value |
| ---------------- | ----- |
| Loss Function    | WARP  |
| Components       | 30    |
| Epochs           | 30    |
| Threads          | 4     |
| Train/Test Split | 80/20 |
| Random Seed      | 42    |

### 2.3 Loss Function: WARP

The model employs the **Weighted Approximate-Rank Pairwise (WARP)** loss function, which is specifically designed for ranking optimization in recommendation systems. WARP loss has several advantages:

- **Ranking Optimization**: Directly optimizes for the ranking of positive items over negative items
- **Efficient Negative Sampling**: Uses adaptive sampling that focuses on hard negatives (negative items ranked above positive items)
- **Top-K Performance**: Particularly effective for optimizing metrics like Precision@K and Recall@K

The WARP loss function works by sampling negative items until it finds one that is ranked higher than a positive item, then computing the approximate rank and applying a weighted update to push the positive item higher in the ranking.

## 3. Dataset: MovieLens 32M

### 3.1 Dataset Overview

The model was trained and evaluated on the **MovieLens 32M** dataset, a benchmark corpus for recommendation system research provided by GroupLens.

| Statistic     | Value                            |
| ------------- | -------------------------------- |
| Total Ratings | 32,000,204                       |
| Total Movies  | 87,585                           |
| Total Users   | 200,948                          |
| Date Range    | Jan 1995 - Oct 2023              |
| Rating Scale  | 0.5 - 5.0 (half-star increments) |

### 3.2 Data Preprocessing

The movie metadata was enhanced with additional features for hybrid filtering:

**Enhanced Features CSV Structure:**

```
movieId, title, genres, decade
```

Example entries:

- `1, Toy Story (1995), Adventure|Animation|Children|Comedy|Fantasy, 1990s`
- `111, Taxi Driver (1976), Crime|Drama|Thriller, 1970s`

### 3.3 Feature Engineering

Two primary feature types were extracted for item-based recommendations:

#### Genres

Movies are tagged with one or more genres from 19 possible categories:

- Action, Adventure, Animation, Children, Comedy, Crime
- Documentary, Drama, Fantasy, Film-Noir, Horror, IMAX
- Musical, Mystery, Romance, Sci-Fi, Thriller, War, Western
- (no genres listed)

#### Decade

Release decade extracted from movie titles, prefixed with `decade:` to avoid feature collisions (e.g., `decade:1990s`, `decade:1980s`).

## 4. Training Methodology

### 4.1 Data Splitting

The interaction matrix was split using LightFM's `random_train_test_split` function:

| Split | Percentage |
| ----- | ---------- |
| Train | 80%        |
| Test  | 20%        |

A fixed random seed (42) ensures reproducibility across training and evaluation runs.

### 4.2 Training Process

The model was trained using the following approach:

1. **Dataset Fitting**: User and item mappings established from ratings data
2. **Interaction Building**: User-item interaction matrix constructed from ratings
3. **Feature Building**: Item feature matrix constructed from genres and decades
4. **Model Training**: 30 epochs with WARP loss and 4-thread parallelization

## 5. Evaluation Metrics

### 5.1 Metrics Employed

The model is evaluated using three standard recommendation system metrics:

1. **Precision@K**: Proportion of recommended items that are relevant
2. **Recall@K**: Proportion of relevant items that are recommended
3. **AUC (ROC-AUC)**: Probability that a randomly chosen positive item is ranked higher than a randomly chosen negative item

### 5.2 Metric Definitions

#### Precision@K

Measures the fraction of the top-K recommended items that are relevant (appear in the test set):

$$\text{Precision}@K = \frac{|\text{Relevant Items in Top-K}|}{K}$$

For K=10, this metric answers: "Of the 10 movies recommended, how many did the user actually interact with?"

#### Recall@K

Measures the fraction of all relevant items that are captured in the top-K recommendations:

$$\text{Recall}@K = \frac{|\text{Relevant Items in Top-K}|}{|\text{Total Relevant Items}|}$$

For K=10, this metric answers: "Of all movies the user would interact with, how many are in the top 10 recommendations?"

#### AUC (Area Under the ROC Curve)

Measures the probability that the model ranks a random positive item higher than a random negative item:

$$\text{AUC} = P(\text{score}(u, i_{pos}) > \text{score}(u, i_{neg}))$$

An AUC of 0.5 indicates random ranking, while 1.0 indicates perfect ranking. For recommendation systems:

- **AUC > 0.9**: Excellent ranking capability
- **AUC 0.8-0.9**: Good ranking capability
- **AUC 0.7-0.8**: Acceptable ranking capability
- **AUC < 0.7**: Poor ranking capability

### 5.3 Evaluation Methodology

The evaluation script:

1. Loads the trained model and dataset mappings
2. Recreates the train/test split using the same random seed
3. Computes metrics on both training and test sets
4. Reports per-user averages for each metric

## 6. Results

### 6.1 Performance Results

The model achieved the following metrics on the MovieLens 32M dataset:

| Metric       | Train  | Test   |
| ------------ | ------ | ------ |
| Precision@10 | 0.4842 | 0.1154 |
| Recall@10    | 0.0773 | 0.0715 |
| AUC          | 0.9961 | 0.9940 |

> [!NOTE]
> These results were obtained using the evaluation script:
>
> ```bash
> cd training
> python movie_evaluation.py
> ```

### 6.2 Interpretation of Results

#### Precision@10: 11.54% (Test)

- **Strong performance** for a large-scale dataset with 87,585 movies
- On average, 1.15 out of 10 recommended movies are relevant to the user
- Higher than typical benchmarks (5-10%) due to effective WARP loss optimization

#### Recall@10: 7.15% (Test)

- Captures 7.15% of all relevant items in just 10 recommendations
- Recall@10 is inherently limited when users have hundreds of relevant items
- Train/test consistency (7.73% vs 7.15%) indicates good generalization

#### AUC: 99.40% (Test)

- **Exceptional ranking capability** - near-perfect ordering of positive over negative items
- The model almost always ranks movies the user would like above random movies
- Minimal train/test gap (99.61% vs 99.40%) demonstrates excellent generalization

## 7. Hybrid Recommendation Benefits

### 7.1 Cold-Start Mitigation

The hybrid approach using item features (genres, decades) addresses the cold-start problem:

- **New Movies**: Can be recommended based on genre and decade similarity even without user ratings
- **Feature Transfer**: Models trained on well-rated movies can generalize to similar new releases

### 7.2 Feature Contributions

The inclusion of genre and decade features enables:

1. **Semantic Similarity**: Movies with similar genres are embedded closer in latent space
2. **Temporal Preferences**: Decade features capture user preferences for content from specific eras
3. **Explainability**: Recommendations can be partially explained through shared features

## 8. Discussion

### 8.1 Strengths

- **Scalability**: Efficient handling of 32 million ratings with parallel computation
- **Hybrid Architecture**: Combines collaborative signals with content features
- **Ranking Optimization**: WARP loss directly optimizes for top-K recommendation quality
- **Reproducibility**: Fixed random seeds ensure consistent evaluation

### 8.2 Limitations

- **Implicit Feedback**: The model treats all ratings as positive interactions; explicit rating values are not weighted
- **Static Features**: Decade and genre are fixed metadata; dynamic features (popularity trends) are not incorporated
- **Single Context**: The model does not account for temporal dynamics or session-based patterns

### 8.3 Future Directions

1. **Rating Integration**: Incorporating explicit rating values as interaction weights
2. **Dynamic Features**: Adding popularity and recency signals
3. **Contextual Bandits**: Integrating online learning for continuous model improvement
4. **Cross-Domain Transfer**: Leveraging features learned from movies for song recommendations

## 9. Technical Reference

### 9.1 Model Artifacts

The trained model produces the following artifacts in `models/movie_recommender/`:

| File                     | Description                                 |
| ------------------------ | ------------------------------------------- |
| `lightfm_model.pkl`      | Serialized LightFM model                    |
| `lightfm_dataset.pkl`    | Dataset mappings (user/item IDs to indices) |
| `item_features.pkl`      | Sparse matrix of item features              |
| `train_interactions.pkl` | Training interaction matrix                 |
| `test_interactions.pkl`  | Test interaction matrix                     |

### 9.2 Evaluation Script Usage

```bash
# Navigate to training directory
cd training

# Run evaluation (requires trained model)
python movie_evaluation.py
```

Expected output:

```
==================================================
LIGHTFM MOVIE RECOMMENDER EVALUATION RESULTS
==================================================

Metric                           Train         Test
--------------------------------------------------
Precision@10                    0.4842       0.1154
Recall@10                       0.0773       0.0715
AUC                             0.9961       0.9940
--------------------------------------------------
```

## 10. Conclusion

The LightFM movie recommendation model provides a scalable, hybrid approach to personalized movie recommendations. By combining collaborative filtering with content-based features (genres and decades), the model achieves robust ranking performance while mitigating cold-start issues. The WARP loss function ensures optimization directly targets top-K recommendation quality, making the model particularly suitable for real-world deployment scenarios where users interact with only the highest-ranked suggestions.

## References

1. Harper, F. M., & Konstan, J. A. (2015). The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems (TiiS), 5(4), 19:1–19:19.

2. Kula, M. (2015). Metadata Embeddings for User and Item Cold-start Recommendations. arXiv preprint arXiv:1507.08439.

3. Weston, J., Bengio, S., & Usunier, N. (2011). WSABIE: Scaling Up To Large Vocabulary Image Annotation. IJCAI.
