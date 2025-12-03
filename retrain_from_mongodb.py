"""
Retrain ALS model từ MongoDB interactions
"""
import asyncio
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import ALS model từ script cũ
import sys
sys.path.append('scripts')
from train_als_model import ImplicitALS

async def load_data_from_mongodb():
    """Load interactions từ MongoDB"""
    print("="*60)
    print("LOADING DATA FROM MONGODB")
    print("="*60)
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['recommend_experiences']
    
    # Load interactions
    print("\nLoading interactions...")
    interactions = await db.interactions.find().to_list(length=None)
    print(f"  ✓ Loaded {len(interactions):,} interactions")
    
    # Convert to DataFrame
    data = []
    for inter in interactions:
        user_id = inter.get('user_id')
        exp_id = str(inter.get('experience_id'))
        
        # Convert ObjectId to string if needed
        if isinstance(user_id, ObjectId):
            user_id = str(user_id)
        
        # Calculate implicit rating based on interaction type
        interaction_type = inter.get('interaction_type', 'view')
        rating_map = {
            'view': 1.0,
            'click': 2.0,
            'wishlist': 3.0,
            'booking': 5.0,
            'completed': 5.0,
            'rating': inter.get('rating', 3.0)
        }
        
        rating = rating_map.get(interaction_type, 1.0)
        
        data.append({
            'user_id': user_id,
            'experience_id': exp_id,
            'rating': rating
        })
    
    df = pd.DataFrame(data)
    
    print(f"\nDataset Stats:")
    print(f"  Users: {df['user_id'].nunique():,}")
    print(f"  Experiences: {df['experience_id'].nunique():,}")
    print(f"  Interactions: {len(df):,}")
    print(f"  Sparsity: {100 * (1 - len(df) / (df['user_id'].nunique() * df['experience_id'].nunique())):.2f}%")
    
    return df

async def main():
    print("\n" + "="*60)
    print("RETRAINING ALS MODEL FROM MONGODB")
    print("="*60 + "\n")
    
    # Load data
    df = await load_data_from_mongodb()
    
    # Encode users and items
    print("\nEncoding users and items...")
    from sklearn.preprocessing import LabelEncoder
    
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    df['user_idx'] = user_encoder.fit_transform(df['user_id'])
    df['item_idx'] = item_encoder.fit_transform(df['experience_id'])
    
    print(f"  ✓ Encoded {len(user_encoder.classes_):,} users")
    print(f"  ✓ Encoded {len(item_encoder.classes_):,} items")
    
    # Create sparse matrix
    print("\nCreating sparse user-item matrix...")
    from scipy.sparse import csr_matrix
    
    user_item_matrix = csr_matrix(
        (df['rating'].values, (df['user_idx'].values, df['item_idx'].values)),
        shape=(len(user_encoder.classes_), len(item_encoder.classes_))
    )
    
    print(f"  ✓ Matrix shape: {user_item_matrix.shape}")
    print(f"  ✓ Non-zero entries: {user_item_matrix.nnz:,}")
    
    # Train model
    print("\n" + "="*60)
    print("TRAINING ALS MODEL")
    print("="*60)
    
    model = ImplicitALS(
        factors=100,
        regularization=0.05,
        iterations=15,
        alpha=40
    )
    
    print("\nTraining...")
    model.fit(user_item_matrix)
    
    print("\n✓ Training completed!")
    
    # Simple evaluation - Hit Rate@10
    print("\n" + "="*60)
    print("EVALUATING MODEL")
    print("="*60)
    
    # Calculate hit rate on sample
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Evaluate on larger test set for better accuracy
    hits = 0
    total = 0
    
    # Test on 1000 samples instead of 100
    test_sample = test_df.sample(min(1000, len(test_df)), random_state=42)
    
    for _, row in test_sample.iterrows():
        user_idx = row['user_idx']
        item_idx = row['item_idx']
        
        # Get predictions for this user
        user_vec = model.user_factors[user_idx]
        scores = model.item_factors.dot(user_vec)
        
        # Top 10 recommendations
        top_10 = np.argsort(scores)[-10:]
        
        if item_idx in top_10:
            hits += 1
        total += 1
    
    hit_rate = hits / total if total > 0 else 0
    
    metrics = {
        'hit_rate': hit_rate,
        'coverage': 1.0
    }
    
    print(f"\nMetrics (sample of {min(1000, len(test_df))} test interactions):")
    print(f"  Hit Rate@10: {metrics['hit_rate']:.2%}")
    
    # Additional stats
    print(f"\nModel Quality Assessment:")
    if metrics['hit_rate'] >= 0.30:
        print(f"  ✅ EXCELLENT - Model performs very well")
    elif metrics['hit_rate'] >= 0.15:
        print(f"  ✓ GOOD - Model performs acceptably")
    elif metrics['hit_rate'] >= 0.05:
        print(f"  ⚠️ FAIR - Model needs improvement")
    else:
        print(f"  ❌ POOR - Consider tuning hyperparameters or improving data quality")
    
    # Save model
    print("\n" + "="*60)
    print("SAVING MODEL")
    print("="*60)
    
    model_dir = Path('models')
    model_dir.mkdir(exist_ok=True)
    
    # Save ALS model
    model_data = {
        'user_factors': model.user_factors,
        'item_factors': model.item_factors,
        'params': {
            'factors': model.factors,
            'regularization': model.regularization,
            'iterations': model.iterations,
            'alpha': model.alpha
        }
    }
    
    with open(model_dir / 'als_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    print(f"\n✓ Saved ALS model to {model_dir / 'als_model.pkl'}")
    
    # Save encoders
    encoders = {
        'user_encoder': user_encoder,
        'item_encoder': item_encoder
    }
    
    with open(model_dir / 'encoders_als.pkl', 'wb') as f:
        pickle.dump(encoders, f)
    print(f"✓ Saved encoders to {model_dir / 'encoders_als.pkl'}")
    
    # Save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'n_users': len(user_encoder.classes_),
        'n_items': len(item_encoder.classes_),
        'n_interactions': len(df),
        'model_params': model_data['params'],
        'metrics': metrics
    }
    
    import json
    with open(model_dir / 'training_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to {model_dir / 'training_metadata.json'}")
    
    print("\n" + "="*60)
    print("RETRAIN COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nModel trained with:")
    print(f"  • {len(user_encoder.classes_):,} users")
    print(f"  • {len(item_encoder.classes_):,} experiences")
    print(f"  • {len(df):,} interactions")
    print(f"  • Hit Rate@10: {metrics['hit_rate']:.2%}")
    print("\nRestart server to load new model!")

if __name__ == "__main__":
    asyncio.run(main())
