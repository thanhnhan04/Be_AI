"""
Data preprocessing for Collaborative Filtering
Step 2: Preprocess interaction table
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InteractionPreprocessor:
    """Preprocess raw interaction data for CF training"""
    
    # Interaction type weights
    INTERACTION_WEIGHTS = {
        'booking': 1.0,      # Highest signal
        'wishlist': 0.7,     # Strong interest
        'click': 0.3,        # Weak signal
        'view': 0.2          # Weakest signal
    }
    
    def __init__(self, min_user_interactions: int = 3, min_item_interactions: int = 3):
        """
        Args:
            min_user_interactions: Minimum interactions per user
            min_item_interactions: Minimum interactions per item
        """
        self.min_user_interactions = min_user_interactions
        self.min_item_interactions = min_item_interactions
        
    def preprocess(self, raw_interactions: list) -> pd.DataFrame:
        """
        Preprocess raw interaction logs
        
        Args:
            raw_interactions: List of interaction dictionaries from DB
            
        Returns:
            Clean DataFrame with [user_id, item_id, rating]
        """
        logger.info(f"Preprocessing {len(raw_interactions)} raw interactions")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_interactions)
        
        # Required columns
        required_cols = ['user_id', 'movie_id', 'interaction_type']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        
        # Rename for consistency
        df = df.rename(columns={'movie_id': 'item_id'})
        
        # Convert rating from interaction type
        df['rating'] = df['interaction_type'].map(self.INTERACTION_WEIGHTS)
        
        # If explicit rating exists, use it
        if 'rating' in df.columns and 'rating' != df['rating'].name:
            df['rating'] = df['rating'].fillna(
                df['interaction_type'].map(self.INTERACTION_WEIGHTS)
            )
        
        # Handle missing ratings (default to click weight)
        df['rating'].fillna(self.INTERACTION_WEIGHTS['click'], inplace=True)
        
        # Convert IDs to string for consistency
        df['user_id'] = df['user_id'].astype(str)
        df['item_id'] = df['item_id'].astype(str)
        
        logger.info(f"Initial interactions: {len(df)}")
        
        # Remove duplicates (keep latest interaction)
        if 'created_at' in df.columns:
            df = df.sort_values('created_at')
        df = df.drop_duplicates(subset=['user_id', 'item_id'], keep='last')
        logger.info(f"After removing duplicates: {len(df)}")
        
        # Filter users with minimum interactions
        user_counts = df['user_id'].value_counts()
        valid_users = user_counts[user_counts >= self.min_user_interactions].index
        df = df[df['user_id'].isin(valid_users)]
        logger.info(f"After filtering users (min {self.min_user_interactions}): {len(df)}")
        
        # Filter items with minimum interactions
        item_counts = df['item_id'].value_counts()
        valid_items = item_counts[item_counts >= self.min_item_interactions].index
        df = df[df['item_id'].isin(valid_items)]
        logger.info(f"After filtering items (min {self.min_item_interactions}): {len(df)}")
        
        # Select final columns
        final_df = df[['user_id', 'item_id', 'rating']].copy()
        
        # Normalize ratings to 0-5 scale if needed
        if final_df['rating'].max() <= 1.0:
            final_df['rating'] = final_df['rating'] * 5
        
        logger.info(
            f"Preprocessing complete: {len(final_df)} interactions, "
            f"{final_df['user_id'].nunique()} users, "
            f"{final_df['item_id'].nunique()} items"
        )
        
        return final_df
    
    def get_user_interacted_items(
        self,
        user_id: str,
        interactions_df: pd.DataFrame
    ) -> list:
        """Get list of items a user has interacted with"""
        user_items = interactions_df[
            interactions_df['user_id'] == user_id
        ]['item_id'].tolist()
        return user_items
    
    def aggregate_interactions(
        self,
        interactions_df: pd.DataFrame,
        method: str = 'max'
    ) -> pd.DataFrame:
        """
        Aggregate multiple interactions for same user-item pair
        
        Args:
            interactions_df: Raw interactions
            method: 'max', 'mean', or 'sum'
        """
        agg_func = {
            'max': 'max',
            'mean': 'mean',
            'sum': 'sum'
        }.get(method, 'max')
        
        aggregated = interactions_df.groupby(
            ['user_id', 'item_id']
        )['rating'].agg(agg_func).reset_index()
        
        return aggregated
