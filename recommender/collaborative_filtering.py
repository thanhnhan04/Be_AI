"""
Collaborative Filtering Recommendation System
Using SVD (Singular Value Decomposition) or ALS (Alternating Least Squares)
"""

import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from scipy.sparse import csr_matrix
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CollaborativeFilteringModel:
    """
    Collaborative Filtering model using matrix factorization
    Supports both SVD and ALS algorithms
    """
    
    def __init__(
        self,
        n_factors: int = 50,
        n_epochs: int = 20,
        learning_rate: float = 0.005,
        regularization: float = 0.02,
        algorithm: str = "svd"  # 'svd' or 'als'
    ):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.algorithm = algorithm
        
        # Model parameters
        self.user_factors = None
        self.item_factors = None
        self.user_bias = None
        self.item_bias = None
        self.global_mean = None
        
        # Encoders
        self.user_encoder = LabelEncoder()
        self.item_encoder = LabelEncoder()
        
        # Metadata
        self.n_users = 0
        self.n_items = 0
        self.is_trained = False
        
    def _init_parameters(self, n_users: int, n_items: int):
        """Initialize model parameters"""
        self.n_users = n_users
        self.n_items = n_items
        
        # Initialize with small random values
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))
        self.user_bias = np.zeros(n_users)
        self.item_bias = np.zeros(n_items)
        
    def _sgd_step(self, user_idx: int, item_idx: int, rating: float) -> float:
        """Perform one SGD step"""
        # Prediction
        pred = (
            self.global_mean +
            self.user_bias[user_idx] +
            self.item_bias[item_idx] +
            np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        )
        
        # Error
        error = rating - pred
        
        # Update biases
        self.user_bias[user_idx] += self.learning_rate * (
            error - self.regularization * self.user_bias[user_idx]
        )
        self.item_bias[item_idx] += self.learning_rate * (
            error - self.regularization * self.item_bias[item_idx]
        )
        
        # Update factors
        user_factors_old = self.user_factors[user_idx].copy()
        self.user_factors[user_idx] += self.learning_rate * (
            error * self.item_factors[item_idx] -
            self.regularization * self.user_factors[user_idx]
        )
        self.item_factors[item_idx] += self.learning_rate * (
            error * user_factors_old -
            self.regularization * self.item_factors[item_idx]
        )
        
        return error ** 2
    
    def train(self, interactions_df: pd.DataFrame) -> Dict[str, float]:
        """
        Train the CF model
        
        Args:
            interactions_df: DataFrame with columns [user_id, item_id, rating]
            
        Returns:
            Training metrics
        """
        logger.info(f"Training CF model with {len(interactions_df)} interactions")
        
        # Encode user and item IDs
        interactions_df['user_idx'] = self.user_encoder.fit_transform(
            interactions_df['user_id']
        )
        interactions_df['item_idx'] = self.item_encoder.fit_transform(
            interactions_df['item_id']
        )
        
        # Initialize parameters
        n_users = interactions_df['user_idx'].nunique()
        n_items = interactions_df['item_idx'].nunique()
        self._init_parameters(n_users, n_items)
        
        # Calculate global mean
        self.global_mean = interactions_df['rating'].mean()
        
        # Split train/test
        train_df, test_df = train_test_split(
            interactions_df, test_size=0.2, random_state=42
        )
        
        logger.info(f"Train set: {len(train_df)}, Test set: {len(test_df)}")
        
        # Training loop
        best_test_rmse = float('inf')
        
        for epoch in range(self.n_epochs):
            # Shuffle training data
            train_df = train_df.sample(frac=1).reset_index(drop=True)
            
            # Train
            train_loss = 0
            for _, row in train_df.iterrows():
                loss = self._sgd_step(
                    int(row['user_idx']),
                    int(row['item_idx']),
                    row['rating']
                )
                train_loss += loss
            
            train_rmse = np.sqrt(train_loss / len(train_df))
            
            # Evaluate on test set
            test_predictions = []
            test_actuals = []
            for _, row in test_df.iterrows():
                pred = self.predict_single(
                    int(row['user_idx']),
                    int(row['item_idx'])
                )
                test_predictions.append(pred)
                test_actuals.append(row['rating'])
            
            test_rmse = np.sqrt(
                np.mean((np.array(test_predictions) - np.array(test_actuals)) ** 2)
            )
            
            if test_rmse < best_test_rmse:
                best_test_rmse = test_rmse
            
            if (epoch + 1) % 5 == 0:
                logger.info(
                    f"Epoch {epoch + 1}/{self.n_epochs} - "
                    f"Train RMSE: {train_rmse:.4f}, Test RMSE: {test_rmse:.4f}"
                )
        
        self.is_trained = True
        
        return {
            'train_rmse': float(train_rmse),
            'test_rmse': float(test_rmse),
            'best_test_rmse': float(best_test_rmse),
            'n_users': n_users,
            'n_items': n_items,
            'n_interactions': len(interactions_df)
        }
    
    def predict_single(self, user_idx: int, item_idx: int) -> float:
        """Predict rating for a single user-item pair"""
        if user_idx >= self.n_users or item_idx >= self.n_items:
            return self.global_mean
        
        pred = (
            self.global_mean +
            self.user_bias[user_idx] +
            self.item_bias[item_idx] +
            np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        )
        
        return pred
    
    def recommend_for_user(
        self,
        user_id: str,
        top_k: int = 10,
        exclude_items: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Generate top-K recommendations for a user
        
        Args:
            user_id: Original user ID
            top_k: Number of recommendations
            exclude_items: Items to exclude (already interacted)
            
        Returns:
            List of (item_id, predicted_score) tuples
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet")
        
        # Check if user exists in training data
        if user_id not in self.user_encoder.classes_:
            logger.warning(f"User {user_id} not found in training data")
            return []
        
        # Encode user ID
        user_idx = self.user_encoder.transform([user_id])[0]
        
        # Get all items
        all_items = self.item_encoder.classes_
        
        # Predict scores for all items
        predictions = []
        for item_id in all_items:
            # Skip excluded items
            if exclude_items and item_id in exclude_items:
                continue
            
            item_idx = self.item_encoder.transform([item_id])[0]
            score = self.predict_single(user_idx, item_idx)
            predictions.append((item_id, float(score)))
        
        # Sort by score and return top-K
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:top_k]
    
    def save(self, model_path: str, encoder_path: str):
        """Save model and encoders to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        # Save model parameters
        model_data = {
            'user_factors': self.user_factors,
            'item_factors': self.item_factors,
            'user_bias': self.user_bias,
            'item_bias': self.item_bias,
            'global_mean': self.global_mean,
            'n_users': self.n_users,
            'n_items': self.n_items,
            'n_factors': self.n_factors,
            'algorithm': self.algorithm,
            'is_trained': self.is_trained
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save encoders
        encoder_data = {
            'user_encoder': self.user_encoder,
            'item_encoder': self.item_encoder
        }
        
        with open(encoder_path, 'wb') as f:
            pickle.dump(encoder_data, f)
        
        logger.info(f"Model saved to {model_path} and {encoder_path}")
    
    @classmethod
    def load(cls, model_path: str, encoder_path: str) -> 'CollaborativeFilteringModel':
        """Load model and encoders from disk"""
        # Load model parameters
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Load encoders
        with open(encoder_path, 'rb') as f:
            encoder_data = pickle.load(f)
        
        # Create instance
        model = cls(
            n_factors=model_data['n_factors'],
            algorithm=model_data['algorithm']
        )
        
        # Restore parameters
        model.user_factors = model_data['user_factors']
        model.item_factors = model_data['item_factors']
        model.user_bias = model_data['user_bias']
        model.item_bias = model_data['item_bias']
        model.global_mean = model_data['global_mean']
        model.n_users = model_data['n_users']
        model.n_items = model_data['n_items']
        model.is_trained = model_data['is_trained']
        
        model.user_encoder = encoder_data['user_encoder']
        model.item_encoder = encoder_data['item_encoder']
        
        logger.info(f"Model loaded from {model_path}")
        return model
