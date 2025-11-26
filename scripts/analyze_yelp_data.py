"""
Phân tích dữ liệu Yelp Dataset để đánh giá khả năng sử dụng cho hệ thống recommendation
"""

import pandas as pd
import numpy as np

print("="*80)
print("PHÂN TÍCH DỮ LIỆU YELP DATASET")
print("="*80)

# 1. Businesses data
print("\n1️⃣ BUSINESSES DATA (Items/Experiences)")
print("-"*80)
businesses_df = pd.read_csv('../data/businesses.csv')
print(f"Tổng số businesses: {len(businesses_df):,}")
print(f"Columns: {businesses_df.columns.tolist()}")
print(f"\nSample businesses:")
print(businesses_df[['name', 'categories', 'stars', 'review_count', 'city']].head(10))

# Categories analysis
all_categories = businesses_df['categories'].str.split(', ').explode()
print(f"\nTổng số unique categories: {all_categories.nunique()}")
print(f"Top 10 categories phổ biến:")
print(all_categories.value_counts().head(10))

# 2. User-Item-Ratings data
print("\n\n2️⃣ USER-ITEM-RATING DATA (Raw)")
print("-"*80)
ratings_df = pd.read_csv('../data/user_item_ratings_sample.csv')
print(f"Tổng số reviews: {len(reviews_df):,}")
print(f"Columns: {reviews_df.columns.tolist()}")
print(f"\nRating distribution:")
print(reviews_df['stars'].value_counts().sort_index())

print(f"Tổng số interactions: {len(ratings_df):,}")
print(f"Unique users: {ratings_df['user_id'].nunique():,}")
print(f"Unique items (businesses): {ratings_df['item_id'].nunique():,}")
print(f"\nRating distribution:")
print(ratings_df['rating'].value_counts().sort_index())

# 3. Processed ratings (with encoding)
print("\n\n3️⃣ PROCESSED RATINGS (Label Encoded)")
print("-"*80)
processed_df = pd.read_csv('../data/processed_ratings.csv')
print(f"Tổng số interactions: {len(processed_df):,}")
print(f"Unique users: {processed_df['user_id'].nunique():,}")
print(f"Unique items: {processed_df['item_id'].nunique():,}")
print(f"User indices: 0 to {processed_df['user_idx'].max()}")
print(f"Item indices: 0 to {processed_df['item_idx'].max()}")

# 4. Data quality analysis
print("\n\n4️⃣ DATA QUALITY ANALYSIS")
print("-"*80)

# Sparsity
sparsity = 1 - (len(ratings_df) / (ratings_df['user_id'].nunique() * ratings_df['item_id'].nunique()))
print(f"Data sparsity: {sparsity*100:.2f}%")

# User activity
user_counts = ratings_df.groupby('user_id').size()
print(f"\nUser activity:")
print(f"  - Min interactions/user: {user_counts.min()}")
print(f"  - Max interactions/user: {user_counts.max()}")
print(f"  - Mean interactions/user: {user_counts.mean():.2f}")
print(f"  - Median interactions/user: {user_counts.median():.0f}")

# Item popularity
item_counts = ratings_df.groupby('item_id').size()
print(f"\nItem (business) popularity:")
print(f"  - Min interactions/item: {item_counts.min()}")
print(f"  - Max interactions/item: {item_counts.max()}")
print(f"  - Mean interactions/item: {item_counts.mean():.2f}")
print(f"  - Median interactions/item: {item_counts.median():.0f}")

# 5. Recommendation suitability assessment
print("\n\n5️⃣ ĐÁNH GIÁ KHẢ NĂNG SỬ DỤNG CHO HỆ THỐNG RECOMMENDATION")
print("="*80)

print("\n✅ ƯU ĐIỂM:")
print("  1. Dữ liệu thật từ Yelp - chất lượng cao, đa dạng")
print(f"  2. {len(ratings_df):,} interactions - đủ lớn để train CF model")
print(f"  3. {ratings_df['user_id'].nunique():,} users - đủ để tạo user-user similarity")
print(f"  4. {ratings_df['item_id'].nunique():,} businesses - đa dạng")
print("  5. Có sẵn business metadata (categories, location, stars)")
print("  6. Ratings từ 1-5 stars - explicit feedback rõ ràng")
print("  7. Đã có processed_ratings.csv với label encoding sẵn")

print("\n⚠️  LƯU Ý:")
print(f"  1. Sparsity cao ({sparsity*100:.1f}%) - cần xử lý cold start")
print("  2. Dữ liệu Yelp là businesses (restaurants, shops) không phải experiences")
print("  3. Cần mapping sang domain 'experiences' nếu muốn giống Airbnb")

print("\n🎯 KHUYẾN NGHỊ:")
print("  ✓ CÓ THỂ SỬ DỤNG cho hệ thống recommendation")
print("  ✓ Phù hợp cho Collaborative Filtering")
print("  ✓ Nên filter categories phù hợp với 'experiences':")
print("    - Tours")
print("    - Activities & Entertainment") 
print("    - Food & Restaurants (dining experiences)")
print("    - Arts & Culture")
print("    - Sports & Recreation")
print("    - Nightlife")

print("\n💡 NEXT STEPS:")
print("  1. Filter businesses theo categories phù hợp với experiences")
print("  2. Sử dụng processed_ratings.csv để train CF model")
print("  3. Convert interaction types: rating 5,4 → booking, rating 3 → wishlist")
print("  4. Train model tương tự như đã làm với cf_train.csv")

print("\n" + "="*80)
