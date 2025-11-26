"""
Training Collaborative Filtering Model for Experience Recommendation (Airbnb-style)
Steps 2-6: Create Interaction Table → Label Encoding → Train CF → Evaluate → Save Model
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from scipy.sparse import csr_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import precision_score, recall_score
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CollaborativeFilteringSVD:
    """
    Collaborative Filtering using Matrix Factorization with SVD
    For experience/activity recommendation (Airbnb-style)
    """
    
    def __init__(
        self,
        n_factors: int = 50,
        n_epochs: int = 20,
        learning_rate: float = 0.005,
        regularization: float = 0.02
    ):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = learning_rate
        self.reg = regularization
        
        # Model parameters
        self.user_factors = None
        self.item_factors = None
        self.user_bias = None
        self.item_bias = None
        self.global_mean = None
        
        self.n_users = 0
        self.n_items = 0
        
    def _initialize_parameters(self, n_users: int, n_items: int):
        """Initialize latent factors and biases"""
        self.n_users = n_users
        self.n_items = n_items
        
        # Initialize with small random values
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))
        self.user_bias = np.zeros(n_users)
        self.item_bias = np.zeros(n_items)
        
    def _predict_single(self, user_idx: int, item_idx: int) -> float:
        """Predict rating for single user-item pair"""
        if user_idx >= self.n_users or item_idx >= self.n_items:
            return self.global_mean
        
        prediction = (
            self.global_mean +
            self.user_bias[user_idx] +
            self.item_bias[item_idx] +
            np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        )
        
        # Clip to valid range [0, 1]
        return np.clip(prediction, 0, 1)
    
    def _sgd_step(self, user_idx: int, item_idx: int, rating: float):
        """Single SGD update step"""
        # Compute prediction and error
        pred = self._predict_single(user_idx, item_idx)
        error = rating - pred
        
        # Update biases
        self.user_bias[user_idx] += self.lr * (error - self.reg * self.user_bias[user_idx])
        self.item_bias[item_idx] += self.lr * (error - self.reg * self.item_bias[item_idx])
        
        # Update latent factors
        user_factors_old = self.user_factors[user_idx].copy()
        self.user_factors[user_idx] += self.lr * (
            error * self.item_factors[item_idx] - self.reg * self.user_factors[user_idx]
        )
        self.item_factors[item_idx] += self.lr * (
            error * user_factors_old - self.reg * self.item_factors[item_idx]
        )
        
        return error ** 2
    
    def fit(self, user_indices: np.ndarray, item_indices: np.ndarray, ratings: np.ndarray):
        """
        Train the CF model using SGD
        
        Args:
            user_indices: Array of user indices
            item_indices: Array of item indices
            ratings: Array of ratings (0-1 scale)
        """
        n_users = int(user_indices.max() + 1)
        n_items = int(item_indices.max() + 1)
        
        logger.info(f"Training CF model: {n_users} users, {n_items} items, {len(ratings)} interactions")
        
        # Initialize parameters
        self._initialize_parameters(n_users, n_items)
        self.global_mean = ratings.mean()
        
        # Training loop
        n_samples = len(ratings)
        indices = np.arange(n_samples)
        
        for epoch in range(self.n_epochs):
            # Shuffle data
            np.random.shuffle(indices)
            
            train_loss = 0
            for idx in indices:
                loss = self._sgd_step(
                    int(user_indices[idx]),
                    int(item_indices[idx]),
                    ratings[idx]
                )
                train_loss += loss
            
            rmse = np.sqrt(train_loss / n_samples)
            
            if (epoch + 1) % 5 == 0:
                logger.info(f"Epoch {epoch + 1}/{self.n_epochs} - RMSE: {rmse:.4f}")
        
        logger.info("✓ Training completed")
        
    def predict(self, user_indices: np.ndarray, item_indices: np.ndarray) -> np.ndarray:
        """Predict ratings for user-item pairs"""
        predictions = np.array([
            self._predict_single(int(u), int(i))
            for u, i in zip(user_indices, item_indices)
        ])
        return predictions
    
    def recommend_for_user(self, user_idx: int, top_k: int = 10, exclude_items: set = None) -> list:
        """
        Get top-K recommendations for a user
        
        Returns:
            List of (item_idx, predicted_score) tuples
        """
        if user_idx >= self.n_users:
            return []
        
        if exclude_items is None:
            exclude_items = set()
        
        # Predict scores for all items
        scores = []
        for item_idx in range(self.n_items):
            if item_idx not in exclude_items:
                score = self._predict_single(user_idx, item_idx)
                scores.append((item_idx, score))
        
        # Sort by score and return top-K
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def calculate_precision_at_k(predictions: dict, test_interactions: dict, k: int = 10) -> float:
    """
    Calculate Precision@K
    
    Args:
        predictions: {user_idx: [(item_idx, score), ...]}
        test_interactions: {user_idx: set(item_idx)}
        k: Number of recommendations
    
    Returns:
        Average Precision@K across all users
    """
    precisions = []
    
    for user_idx, recommended_items in predictions.items():
        if user_idx not in test_interactions:
            continue
        
        # Get top-K recommendations
        top_k_items = [item_idx for item_idx, score in recommended_items[:k]]
        
        # Get actual test items for this user
        actual_items = test_interactions[user_idx]
        
        # Calculate precision
        if len(top_k_items) > 0:
            hits = len(set(top_k_items) & actual_items)
            precision = hits / k
            precisions.append(precision)
    
    return np.mean(precisions) if precisions else 0.0


def calculate_recall_at_k(predictions: dict, test_interactions: dict, k: int = 10) -> float:
    """Calculate Recall@K"""
    recalls = []
    
    for user_idx, recommended_items in predictions.items():
        if user_idx not in test_interactions:
            continue
        
        top_k_items = [item_idx for item_idx, score in recommended_items[:k]]
        actual_items = test_interactions[user_idx]
        
        if len(actual_items) > 0:
            hits = len(set(top_k_items) & actual_items)
            recall = hits / len(actual_items)
            recalls.append(recall)
    
    return np.mean(recalls) if recalls else 0.0


def main():
    """Main training pipeline - Steps 2 to 6"""
    
    logger.info("=" * 80)
    logger.info("COLLABORATIVE FILTERING TRAINING PIPELINE - EXPERIENCE RECOMMENDATION")
    logger.info("=" * 80)
    
    # Paths
    data_dir = Path("../data")
    model_dir = Path("../models")
    model_dir.mkdir(exist_ok=True)
    
    # ========== STEP 2: Create Interaction Table ========== 
    logger.info("\n📊 STEP 2: Load Yelp Interaction Data (processed_ratings.csv)")
    
    # Load Yelp data (already has user_id, business_id, stars, user_idx, item_idx)
    df = pd.read_csv(data_dir / "processed_ratings.csv")
    logger.info(f"Total interactions: {len(df)}")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # Rename columns to standard format
    df = df.rename(columns={'business_id': 'item_id', 'stars': 'rating'})
    
    # Train/Test split (80/20)
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    logger.info(f"Train set: {len(train_df)} interactions")
    logger.info(f"Test set: {len(test_df)} interactions")
    
    # Select necessary columns
    train_interactions = train_df[['user_id', 'item_id', 'rating']].copy()
    test_interactions = test_df[['user_id', 'item_id', 'rating']].copy()
    
    logger.info(f"✓ Interaction table created")
    logger.info(f"  - Users: {train_interactions['user_id'].nunique()}")
    logger.info(f"  - Items: {train_interactions['item_id'].nunique()}")
    logger.info(f"  - Rating distribution:\n{train_interactions['rating'].value_counts().sort_index()}")
    
    # ========== STEP 3: Label Encoding ========== 
    logger.info("\n🏷️  STEP 3: Label Encoding (user_id/item_id → indices)")
    
    # Create encoders
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    # Fit on train + test to ensure coverage
    all_users = pd.concat([train_interactions['user_id'], test_interactions['user_id']]).unique()
    all_items = pd.concat([train_interactions['item_id'], test_interactions['item_id']]).unique()
    
    user_encoder.fit(all_users)
    item_encoder.fit(all_items)
    
    # Transform
    train_interactions['user_idx'] = user_encoder.transform(train_interactions['user_id'])
    train_interactions['item_idx'] = item_encoder.transform(train_interactions['item_id'])
    
    test_interactions['user_idx'] = user_encoder.transform(test_interactions['user_id'])
    test_interactions['item_idx'] = item_encoder.transform(test_interactions['item_id'])
    
    logger.info(f"✓ Label encoding completed")
    logger.info(f"  - Unique users encoded: {len(user_encoder.classes_)}")
    logger.info(f"  - Unique items encoded: {len(item_encoder.classes_)}")
    
    # Save encoders
    encoder_path = model_dir / "encoders.pkl"
    with open(encoder_path, 'wb') as f:
        pickle.dump({
            'user_encoder': user_encoder,
            'item_encoder': item_encoder
        }, f)
    logger.info(f"✓ Encoders saved to {encoder_path}")
    
    # ========== STEP 4: Train CF Model (SVD) ========== 
    logger.info("\n🧠 STEP 4: Train Collaborative Filtering Model (SVD)")
    
    # Prepare training data
    user_indices = train_interactions['user_idx'].values
    item_indices = train_interactions['item_idx'].values
    ratings = train_interactions['rating'].values
    
    # Initialize and train model
    cf_model = CollaborativeFilteringSVD(
        n_factors=50,
        n_epochs=20,
        learning_rate=0.005,
        regularization=0.02
    )
    
    cf_model.fit(user_indices, item_indices, ratings)
    
    # ========== STEP 5: Evaluate Precision@K ========== 
    logger.info("\n📈 STEP 5: Evaluate Model Performance (Precision@K, Recall@K)")
    
    # Get test interactions grouped by user
    test_user_items = test_interactions.groupby('user_idx')['item_idx'].apply(set).to_dict()
    
    # Get train interactions to exclude from recommendations
    train_user_items = train_interactions.groupby('user_idx')['item_idx'].apply(set).to_dict()
    
    # Generate recommendations for all test users
    predictions = {}
    for user_idx in test_user_items.keys():
        exclude = train_user_items.get(user_idx, set())
        recommendations = cf_model.recommend_for_user(user_idx, top_k=20, exclude_items=exclude)
        predictions[user_idx] = recommendations
    
    # Calculate metrics
    metrics = {}
    for k in [5, 10, 20]:
        precision = calculate_precision_at_k(predictions, test_user_items, k=k)
        recall = calculate_recall_at_k(predictions, test_user_items, k=k)
        metrics[f'precision@{k}'] = precision
        metrics[f'recall@{k}'] = recall
        logger.info(f"  Precision@{k}: {precision:.4f} | Recall@{k}: {recall:.4f}")
    
    # Calculate RMSE on test set
    test_predictions = cf_model.predict(
        test_interactions['user_idx'].values,
        test_interactions['item_idx'].values
    )
    test_rmse = np.sqrt(np.mean((test_predictions - test_interactions['rating'].values) ** 2))
    metrics['test_rmse'] = test_rmse
    logger.info(f"  Test RMSE: {test_rmse:.4f}")
    
    # ========== STEP 6: Save Model ========== 
    logger.info("\n💾 STEP 6: Save Model and Metadata")
    
    # Save model
    model_path = model_dir / "cf_model.pkl"
    model_data = {
        'user_factors': cf_model.user_factors,
        'item_factors': cf_model.item_factors,
        'user_bias': cf_model.user_bias,
        'item_bias': cf_model.item_bias,
        'global_mean': cf_model.global_mean,
        'n_users': cf_model.n_users,
        'n_items': cf_model.n_items,
        'n_factors': cf_model.n_factors,
        'trained_at': datetime.now().isoformat()
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    logger.info(f"✓ Model saved to {model_path}")
    
    # Save metadata
    metadata_path = model_dir / "training_metadata.json"
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'n_users': int(cf_model.n_users),
        'n_items': int(cf_model.n_items),
        'n_train_interactions': len(train_interactions),
        'n_test_interactions': len(test_interactions),
        'n_factors': cf_model.n_factors,
        'n_epochs': cf_model.n_epochs,
        'learning_rate': cf_model.lr,
        'regularization': cf_model.reg,
        'metrics': {k: float(v) for k, v in metrics.items()}
    }
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadata saved to {metadata_path}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Model files created:")
    logger.info(f"  - {model_path}")
    logger.info(f"  - {encoder_path}")
    logger.info(f"  - {metadata_path}")
    logger.info("\nModel Performance:")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")
    logger.info("=" * 80)
    
    return cf_model, user_encoder, item_encoder, metrics


if __name__ == "__main__":
    model, user_enc, item_enc, metrics = main()
    
    # Example: Get recommendations for a user
    print("\n" + "="*80)
    print("EXAMPLE: Get recommendations for user_id = 1")
    print("="*80)
    
    user_id = 1
    try:
        user_idx = user_enc.transform([user_id])[0]
        recommendations = model.recommend_for_user(user_idx, top_k=10)
        
        print(f"\nTop 10 recommendations for user {user_id}:")
        for rank, (item_idx, score) in enumerate(recommendations, 1):
            item_id = item_enc.inverse_transform([item_idx])[0]
            print(f"  {rank}. Experience ID: {item_id} (predicted score: {score:.3f})")
    except Exception as e:
        print(f"Error: {e}")
