"""
Recommendation Service
Step 6: Serve API Top-K recommendation
"""

import os
import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from bson import ObjectId

from database import get_database, get_redis, EXPERIENCES_COLLECTION, INTERACTIONS_COLLECTION
from recommender import CollaborativeFilteringModel, InteractionPreprocessor, PopularityRecommender
from schemas import RecommendationItem, RecommendationResponse
from config import settings
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating recommendations"""
    
    def __init__(self):
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        self.cf_model: Optional[CollaborativeFilteringModel] = None
        self.popularity_model: Optional[PopularityRecommender] = None
        self.preprocessor = InteractionPreprocessor(
            min_user_interactions=settings.MIN_INTERACTIONS_FOR_CF,
            min_item_interactions=3
        )
        
        # Try to load existing model
        self._load_models()
    
    def _load_models(self):
        """Load trained models from disk"""
        model_path = self.model_dir / "cf_model.pkl"
        encoder_path = self.model_dir / "encoders.pkl"
        
        if model_path.exists() and encoder_path.exists():
            try:
                self.cf_model = CollaborativeFilteringModel.load(
                    str(model_path),
                    str(encoder_path)
                )
                logger.info("✓ Loaded CF model from disk")
            except Exception as e:
                logger.error(f"Failed to load CF model: {e}")
                self.cf_model = None
        else:
            logger.warning("CF model not found, will use popularity-based recommendations")
    
    async def get_recommendations(
        self,
        user_id: str,
        top_k: int = 10,
        exclude_watched: bool = True
    ) -> RecommendationResponse:
        """
        Get top-K recommendations for a user
        
        This is the main API endpoint (Step 6)
        """
        db = get_database()
        redis_client = get_redis()
        
        # Check cache first
        cache_key = f"recommendations:{user_id}:{top_k}"
        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for user {user_id}")
                    data = json.loads(cached)
                    return RecommendationResponse(**data)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Get user's interacted items
        exclude_items = []
        if exclude_watched:
            interactions = await db[INTERACTIONS_COLLECTION].find(
                {"user_id": ObjectId(user_id)}
            ).to_list(length=None)
            exclude_items = [str(i['movie_id']) for i in interactions]
        
        # Try CF model first
        recommendations = []
        algorithm = "popularity"
        
        if self.cf_model and self.cf_model.is_trained:
            try:
                cf_recs = self.cf_model.recommend_for_user(
                    user_id=user_id,
                    top_k=top_k,
                    exclude_items=exclude_items
                )
                
                if len(cf_recs) >= top_k // 2:  # If we get reasonable results
                    recommendations = cf_recs
                    algorithm = "collaborative_filtering"
                    logger.info(f"CF recommendations for user {user_id}: {len(cf_recs)} items")
            except Exception as e:
                logger.warning(f"CF model failed: {e}, falling back to popularity")
        
        # Fallback to popularity if CF fails or insufficient results
        if not recommendations:
            if not self.popularity_model:
                await self._train_popularity_model()
            
            if self.popularity_model:
                recommendations = self.popularity_model.recommend(
                    top_k=top_k,
                    exclude_items=exclude_items
                )
                algorithm = "popularity"
        
        # Fetch experience details
        experience_ids = [ObjectId(exp_id) for exp_id, _ in recommendations[:top_k]]
        experiences = await db[EXPERIENCES_COLLECTION].find(
            {"_id": {"$in": experience_ids}}
        ).to_list(length=None)
        
        # Create experience lookup
        experience_map = {str(e['_id']): e for e in experiences}
        
        # Build response
        recommendation_items = []
        for exp_id, score in recommendations[:top_k]:
            exp = experience_map.get(exp_id)
            if exp:
                recommendation_items.append(
                    RecommendationItem(
                        experience_id=exp_id,
                        title=exp['title'],
                        score=score,
                        image_url=exp.get('image_urls', [None])[0] if exp.get('image_urls') else None,
                        category=exp.get('category', ''),
                        rating=exp.get('rating', 0.0),
                        price=exp.get('price', 0.0),
                        duration_hours=exp.get('duration_hours'),
                        location=exp.get('location', {}),
                        description=exp.get('description')
                    )
                )
        
        response = RecommendationResponse(
            user_id=user_id,
            recommendations=recommendation_items,
            algorithm=algorithm
        )
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    response.model_dump_json()
                )
            except Exception as e:
                logger.warning(f"Failed to cache recommendations: {e}")
        
        return response
    
    async def _train_popularity_model(self):
        """Train popularity model as fallback"""
        try:
            db = get_database()
            
            # Get all interactions
            interactions = await db[INTERACTIONS_COLLECTION].find().to_list(length=None)
            
            if not interactions:
                logger.warning("No interactions found for popularity model")
                return
            
            # Convert to DataFrame
            import pandas as pd
            interactions_df = pd.DataFrame([
                {
                    'user_id': str(i['user_id']),
                    'item_id': str(i['experience_id']),
                    'rating': i.get('rating', 1.0)
                }
                for i in interactions
            ])
            
            # Get experiences
            experiences = await db[EXPERIENCES_COLLECTION].find().to_list(length=None)
            experiences_df = pd.DataFrame(experiences)
            
            self.popularity_model = PopularityRecommender()
            self.popularity_model.calculate_popularity(interactions_df, movies_df)
            
            logger.info("✓ Popularity model trained")
        except Exception as e:
            logger.error(f"Failed to train popularity model: {e}")
    
    async def train_cf_model(self) -> dict:
        """
        Train CF model from scratch (Step 4: Train CF model)
        This is called periodically (batch job)
        """
        db = get_database()
        
        # Step 2: Fetch and preprocess interactions
        logger.info("Fetching interactions from database...")
        interactions = await db[INTERACTIONS_COLLECTION].find().to_list(length=None)
        
        if not interactions:
            raise ValueError("No interactions found in database")
        
        # Convert to proper format
        interactions_list = [
            {
                'user_id': str(i['user_id']),
                'experience_id': str(i['experience_id']),
                'interaction_type': i.get('interaction_type', 'click'),
                'rating': i.get('rating'),
                'created_at': i.get('created_at')
            }
            for i in interactions
        ]
        
        # Step 2: Preprocess
        logger.info("Preprocessing interactions...")
        clean_df = self.preprocessor.preprocess(interactions_list)
        
        if len(clean_df) < 10:
            raise ValueError("Not enough clean interactions to train model")
        
        # Step 4: Train CF model
        logger.info("Training CF model...")
        self.cf_model = CollaborativeFilteringModel(
            n_factors=50,
            n_epochs=20,
            learning_rate=0.005,
            regularization=0.02
        )
        
        metrics = self.cf_model.train(clean_df)
        
        # Step 5: Save model and encoders
        model_path = self.model_dir / "cf_model.pkl"
        encoder_path = self.model_dir / "encoders.pkl"
        
        self.cf_model.save(str(model_path), str(encoder_path))
        
        # Save training metadata
        metadata = {
            'trained_at': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'n_interactions': len(clean_df),
            'n_users': clean_df['user_id'].nunique(),
            'n_items': clean_df['item_id'].nunique()
        }
        
        with open(self.model_dir / "training_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Clear cache
        redis_client = get_redis()
        if redis_client:
            try:
                # Clear all recommendation cache
                keys = await redis_client.keys("recommendations:*")
                if keys:
                    await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached recommendations")
            except Exception as e:
                logger.warning(f"Failed to clear cache: {e}")
        
        logger.info("✓ CF model training complete")
        return metrics


# Singleton instance
recommendation_service = RecommendationService()
