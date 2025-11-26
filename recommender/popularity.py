"""
Popularity-based recommendation (cold start fallback)
"""

import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PopularityRecommender:
    """Simple popularity-based recommender for cold start"""
    
    def __init__(self, time_decay_days: int = 30):
        """
        Args:
            time_decay_days: Number of days to consider for popularity
        """
        self.time_decay_days = time_decay_days
        self.popular_items = []
        
    def calculate_popularity(
        self,
        interactions_df: pd.DataFrame,
        movies_df: pd.DataFrame
    ) -> List[Tuple[str, float]]:
        """
        Calculate item popularity scores
        
        Args:
            interactions_df: User interactions
            movies_df: Movie metadata
            
        Returns:
            List of (item_id, popularity_score) tuples
        """
        # Count interactions per item
        item_counts = interactions_df['item_id'].value_counts()
        
        # Get average ratings if available
        if 'rating' in interactions_df.columns:
            avg_ratings = interactions_df.groupby('item_id')['rating'].mean()
        else:
            avg_ratings = pd.Series(index=item_counts.index, data=1.0)
        
        # Combine count and rating (weighted)
        popularity_scores = (
            0.7 * (item_counts / item_counts.max()) +
            0.3 * (avg_ratings / avg_ratings.max())
        )
        
        # Sort by popularity
        self.popular_items = [
            (str(item_id), float(score))
            for item_id, score in popularity_scores.sort_values(ascending=False).items()
        ]
        
        logger.info(f"Calculated popularity for {len(self.popular_items)} items")
        return self.popular_items
    
    def recommend(
        self,
        top_k: int = 10,
        exclude_items: List[str] = None
    ) -> List[Tuple[str, float]]:
        """Get top-K popular items"""
        if exclude_items is None:
            exclude_items = []
        
        recommendations = [
            (item_id, score)
            for item_id, score in self.popular_items
            if item_id not in exclude_items
        ]
        
        return recommendations[:top_k]
