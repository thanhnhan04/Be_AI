"""
Huấn luyện mô hình Implicit ALS (Alternating Least Squares)
Thuật toán được sử dụng bởi Netflix, Spotify cho Top-N recommendations
Tối ưu cho dữ liệu sparse và implicit feedback
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from scipy.sparse import csr_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImplicitALS:
    """
    Implementation của Implicit ALS algorithm
    Dựa trên paper "Collaborative Filtering for Implicit Feedback Datasets" (Hu et al., 2008)
    """
    
    def __init__(self, factors=100, regularization=0.01, iterations=15, alpha=40):
        """
        Args:
            factors: Số chiều latent factors
            regularization: Lambda cho L2 regularization
            iterations: Số vòng lặp alternating
            alpha: Confidence scaling parameter
        """
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.alpha = alpha
        
        self.user_factors = None
        self.item_factors = None
        
    def fit(self, user_items):
        """
        Huấn luyện model trên user-item matrix
        
        Args:
            user_items: scipy.sparse matrix (n_users × n_items) với confidence values
        """
        n_users, n_items = user_items.shape
        
        # Khởi tạo latent factors với giá trị ngẫu nhiên nhỏ
        self.user_factors = np.random.normal(0, 0.01, (n_users, self.factors)).astype(np.float32)
        self.item_factors = np.random.normal(0, 0.01, (n_items, self.factors)).astype(np.float32)
        
        logger.info(f"Bắt đầu training ALS: {n_users} users, {n_items} items")
        logger.info(f"Factors={self.factors}, Regularization={self.regularization}, Iterations={self.iterations}")
        
        # Convert sang CSR format cho efficient row access
        Cui = user_items.tocsr().astype(np.float32)
        Ciu = user_items.T.tocsr().astype(np.float32)
        
        # Alternating Least Squares
        for iteration in range(self.iterations):
            # Fix item factors, solve cho user factors
            self._least_squares(Cui, self.user_factors, self.item_factors)
            
            # Fix user factors, solve cho item factors
            self._least_squares(Ciu, self.item_factors, self.user_factors)
            
            if (iteration + 1) % 5 == 0:
                logger.info(f"  Iteration {iteration + 1}/{self.iterations}")
        
        logger.info("✓ Training hoàn tất")
        
    def _least_squares(self, Cui, X, Y):
        """
        Solve least squares cho một bên (user hoặc item)
        
        Args:
            Cui: Confidence matrix (n × m)
            X: Factors cần update (n × factors)
            Y: Factors cố định (m × factors)
        """
        n_users = X.shape[0]
        YtY = Y.T.dot(Y)  # Pre-compute Y^T * Y
        
        for u in range(n_users):
            # Lấy items mà user u đã tương tác
            items = Cui[u].indices
            if len(items) == 0:
                continue
                
            # Confidence values
            Cu = Cui[u].data
            
            # Preference (binary: 1 nếu có tương tác)
            Pu = np.ones(len(items), dtype=np.float32)
            
            # Y_u: chỉ lấy item factors của items đã tương tác
            Y_u = Y[items]
            
            # Solve: (Y^T * C_u * Y + lambda * I) * x_u = Y^T * C_u * p_u
            # Với C_u là diagonal matrix với Cu values
            
            # A = Y^T * Y + lambda * I
            A = YtY + self.regularization * np.eye(self.factors, dtype=np.float32)
            
            # Cộng thêm (Cu - 1) * Y_i * Y_i^T cho mỗi item i user đã tương tác
            for i, confidence in enumerate(Cu):
                A += (confidence - 1) * np.outer(Y_u[i], Y_u[i])
            
            # b = Y^T * C_u * p_u = sum(Cu_i * Y_i)
            b = Y_u.T.dot(Cu * Pu)
            
            # Solve Ax = b
            X[u] = np.linalg.solve(A, b)
    
    def recommend(self, user_idx, user_items_row, N=2, filter_already_liked_items=True):
        """
        Tạo top-N recommendations cho user
        
        Args:
            user_idx: Index của user
            user_items_row: Row từ user-item matrix (để lọc items đã xem)
            N: Số lượng recommendations
            filter_already_liked_items: Có lọc items đã tương tác không
            
        Returns:
            (item_indices, scores): Arrays của item indices và scores
        """
        # Tính scores cho tất cả items
        scores = self.user_factors[user_idx].dot(self.item_factors.T)
        # Lọc items đã xem nếu cần
        if filter_already_liked_items:
            liked_items = user_items_row.indices
            scores[liked_items] = -np.inf
        # Lấy top-N (không vượt quá số lượng item)
        N = min(N, len(scores))
        if N == 0:
            return [], []
        top_items = np.argpartition(scores, -N)[-N:]
        top_items = top_items[np.argsort(-scores[top_items])]
        return top_items, scores[top_items]


def calculate_metrics(model, train_user_items, test_user_items, user_items_matrix, K=10):
    """
    Tính các metrics: Precision@K, Recall@K, NDCG@K, Hit Rate@K
    
    Args:
        model: Trained ALS model
        train_user_items: Dict {user_idx: set(item_idx)} từ train set
        test_user_items: Dict {user_idx: set(item_idx)} từ test set (chỉ items relevant)
        user_items_matrix: Sparse matrix (users × items)
        K: Top-K recommendations
    """
    precisions = []
    recalls = []
    ndcgs = []
    hits = []
    
    # Chỉ đánh giá users có items trong test set
    test_users = list(test_user_items.keys())
    
    for user_idx in test_users:
        # Lấy items đã tương tác trong train để loại trừ
        train_items = train_user_items.get(user_idx, set())
        
        # Lấy top-K recommendations (ALS tự động loại trừ items đã có trong ma trận)
        # recommend() trả về (item_ids, scores)
        recommended_items, scores = model.recommend(
            user_idx, 
            user_items_matrix[user_idx],
            N=K,
            filter_already_liked_items=True
        )
        
        # Items thực sự relevant trong test set
        relevant_items = test_user_items[user_idx]
        
        # Tính số lượng hits
        recommended_set = set(recommended_items)
            # Lấy top-N (không vượt quá số lượng item)
        N = min(N, len(scores))
        if N == 0:
            return [], []
            top_items = np.argpartition(scores, -N)[-N:]
            top_items = top_items[np.argsort(-scores[top_items])]
            return top_items, scores[top_items]
        precisions.append(precision)
        
        # Recall@K
        recall = hits_count / len(relevant_items) if len(relevant_items) > 0 else 0
        recalls.append(recall)
        
        # NDCG@K
        dcg = 0.0
        for i, item_idx in enumerate(recommended_items):
            if item_idx in relevant_items:
                dcg += 1.0 / np.log2(i + 2)
        
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_items), K)))
        ndcg = dcg / idcg if idcg > 0 else 0
        ndcgs.append(ndcg)
        
        # Hit Rate@K
        has_hit = 1 if hits_count > 0 else 0
        hits.append(has_hit)
    
    return {
        'precision': np.mean(precisions),
        'recall': np.mean(recalls),
        'ndcg': np.mean(ndcgs),
        'hit_rate': np.mean(hits)
    }


def main():
    """Pipeline huấn luyện Implicit ALS"""
    
    logger.info("=" * 80)
    logger.info("IMPLICIT ALS TRAINING PIPELINE - TOP-N RECOMMENDATIONS")
    logger.info("=" * 80)
    
    # Đường dẫn
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir.parent / "data"
    model_dir = script_dir.parent / "models"
    model_dir.mkdir(exist_ok=True)
    
    # ========== BƯỚC 1: Load và lọc dữ liệu ========== 
    logger.info("\n📊 BƯỚC 1: Load và lọc dữ liệu")
    
    df = pd.read_csv(data_dir / "processed_interactions.csv")
    logger.info(f"Tổng số tương tác (thô): {len(df)}")
    
    # Đổi tên cột
    df = df.rename(columns={'experience_id': 'item_id', 'rating': 'rating'})
    
    # Lọc dữ liệu - giữ active users và popular items
    MIN_USER_INTERACTIONS = 1
    MIN_ITEM_INTERACTIONS = 1
    
    logger.info(f"Lọc: Min user interactions={MIN_USER_INTERACTIONS}, Min item interactions={MIN_ITEM_INTERACTIONS}")
    
    iteration = 0
    prev_len = len(df)
    
    while True:
        iteration += 1
        user_counts = df['user_id'].value_counts()
        item_counts = df['item_id'].value_counts()
        
        valid_users = user_counts[user_counts >= MIN_USER_INTERACTIONS].index
        valid_items = item_counts[item_counts >= MIN_ITEM_INTERACTIONS].index
        
        df = df[df['user_id'].isin(valid_users) & df['item_id'].isin(valid_items)]
        
        if len(df) == prev_len:
            break
        prev_len = len(df)
    
    logger.info(f"✓ Lọc hoàn tất sau {iteration} vòng lặp")
    logger.info(f"  - Tương tác: {len(df)} (giữ {len(df)/252361*100:.1f}%)")
    logger.info(f"  - Users: {df['user_id'].nunique()}")
    logger.info(f"  - Items: {df['item_id'].nunique()}")
    logger.info(f"  - Mật độ: {len(df)/(df['user_id'].nunique()*df['item_id'].nunique())*100:.3f}%")
    
    # ========== BƯỚC 2: Chuyển sang Implicit Feedback ========== 
    logger.info("\n🔄 BƯỚC 2: Chuyển đổi sang Implicit Feedback")
    
    # CHIẾN LƯỢC: Rating ≥ 4 = 1 (positive feedback), ngược lại = 0
    # Sau đó apply confidence weighting
    RATING_THRESHOLD = 4.0
    
    # Tạo binary feedback
    df['implicit_feedback'] = (df['rating'] >= RATING_THRESHOLD).astype(int)
    
    # Confidence weighting: confidence = 1 + alpha * rating
    # Alpha cao hơn = tin tưởng rating cao hơn
    ALPHA = 10
    df['confidence'] = 1 + ALPHA * df['rating']
    
    logger.info(f"Ngưỡng rating: ≥{RATING_THRESHOLD} sao = positive feedback")
    logger.info(f"Alpha (confidence weight): {ALPHA}")
    logger.info(f"Positive feedback: {df['implicit_feedback'].sum()} / {len(df)} ({df['implicit_feedback'].mean()*100:.1f}%)")
    
    # ========== BƯỚC 3: Train/Test Split ========== 
    logger.info("\n✂️ BƯỚC 3: Chia Train/Test")
    
    # Split theo thời gian hoặc random
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    logger.info(f"Train: {len(train_df)} tương tác")
    logger.info(f"Test: {len(test_df)} tương tác")
    
    # ========== BƯỚC 4: Label Encoding ========== 
    logger.info("\n🏷️ BƯỚC 4: Mã hóa nhãn")
    
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    all_users = pd.concat([train_df['user_id'], test_df['user_id']]).unique()
    all_items = pd.concat([train_df['item_id'], test_df['item_id']]).unique()
    
    user_encoder.fit(all_users)
    item_encoder.fit(all_items)
    
    train_df['user_idx'] = user_encoder.transform(train_df['user_id'])
    train_df['item_idx'] = item_encoder.transform(train_df['item_id'])
    
    test_df['user_idx'] = user_encoder.transform(test_df['user_id'])
    test_df['item_idx'] = item_encoder.transform(test_df['item_id'])
    
    logger.info(f"✓ Đã mã hóa {len(user_encoder.classes_)} users, {len(item_encoder.classes_)} items")
    
    # Lưu encoders
    encoder_path = model_dir / "encoders_als.pkl"
    with open(encoder_path, 'wb') as f:
        pickle.dump({
            'user_encoder': user_encoder,
            'item_encoder': item_encoder
        }, f)
    logger.info(f"✓ Encoders đã lưu: {encoder_path}")
    
    # ========== BƯỚC 5: Tạo Sparse Matrix ========== 
    logger.info("\n🔢 BƯỚC 5: Tạo User-Item Sparse Matrix")
    
    n_users = len(user_encoder.classes_)
    n_items = len(item_encoder.classes_)
    
    # Tạo ma trận từ train data với confidence values
    user_items_matrix = csr_matrix(
        (train_df['confidence'].values, (train_df['user_idx'].values, train_df['item_idx'].values)),
        shape=(n_users, n_items),
        dtype=np.float32
    )
    
    logger.info(f"Ma trận shape: {user_items_matrix.shape}")
    logger.info(f"Non-zero entries: {user_items_matrix.nnz}")
    logger.info(f"Sparsity: {(1 - user_items_matrix.nnz / (n_users * n_items)) * 100:.2f}%")
    
    # ========== BƯỚC 6: Train ALS Model ========== 
    logger.info("\n🧠 BƯỚC 6: Huấn luyện Implicit ALS Model")
    
    # Hyperparameters tối ưu cho ALS
    model = ImplicitALS(
        factors=100,              # Số chiều latent factors
        regularization=0.05,      # L2 regularization
        iterations=15,            # Số vòng lặp alternating
        alpha=ALPHA               # Confidence scaling
    )
    
    logger.info(f"Cấu hình ALS:")
    logger.info(f"  - Factors: {model.factors}")
    logger.info(f"  - Regularization: {model.regularization}")
    logger.info(f"  - Iterations: {model.iterations}")
    logger.info(f"  - Alpha: {ALPHA}")
    
    # Train model
    logger.info("\nBắt đầu training...")
    model.fit(user_items_matrix)
    
    logger.info("✓ Training hoàn tất!")
    
    # ========== BƯỚC 7: Đánh giá Model ========== 
    logger.info("\n📈 BƯỚC 7: Đánh giá hiệu năng Model")
    
    # Chuẩn bị dữ liệu cho evaluation
    # Train user-items (để loại trừ khỏi recommendations)
    train_user_items = train_df.groupby('user_idx')['item_idx'].apply(set).to_dict()
    
    # Test user-items (chỉ lấy positive feedback)
    test_positive = test_df[test_df['implicit_feedback'] == 1]
    test_user_items = test_positive.groupby('user_idx')['item_idx'].apply(set).to_dict()
    
    logger.info(f"Test users với positive feedback: {len(test_user_items)}")
    logger.info(f"Tổng positive interactions trong test: {len(test_positive)}")
    
    # Tính metrics cho K = 5, 10, 20
    logger.info("\n📊 Kết quả Evaluation:")
    all_metrics = {}
    
    for K in [5, 10, 20]:
        logger.info(f"\nĐang đánh giá @{K}...")
        metrics = calculate_metrics(
            model, 
            train_user_items, 
            test_user_items, 
            user_items_matrix,
            K=K
        )
        
        all_metrics[f'precision@{K}'] = metrics['precision']
        all_metrics[f'recall@{K}'] = metrics['recall']
        all_metrics[f'ndcg@{K}'] = metrics['ndcg']
        all_metrics[f'hit_rate@{K}'] = metrics['hit_rate']
        
        logger.info(f"  Precision@{K}: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
        logger.info(f"  Recall@{K}: {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
        logger.info(f"  NDCG@{K}: {metrics['ndcg']:.4f}")
        logger.info(f"  Hit Rate@{K}: {metrics['hit_rate']:.4f} ({metrics['hit_rate']*100:.2f}%)")
    
    # ========== BƯỚC 8: Lưu Model ========== 
    logger.info("\n💾 BƯỚC 8: Lưu Model")
    
    # Lưu model (chỉ lưu factors, không lưu object để tránh pickle issues)
    model_path = model_dir / "als_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump({
            'user_factors': model.user_factors,
            'item_factors': model.item_factors
        }, f)
    logger.info(f"✓ Model đã lưu: {model_path}")
    
    # Lưu metadata
    metadata_path = model_dir / "als_metadata.json"
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'algorithm': 'Implicit ALS',
        'n_users': n_users,
        'n_items': n_items,
        'n_train_interactions': len(train_df),
        'n_test_interactions': len(test_df),
        'factors': model.factors,
        'regularization': model.regularization,
        'iterations': model.iterations,
        'alpha': ALPHA,
        'rating_threshold': RATING_THRESHOLD,
        'metrics': all_metrics
    }
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadata đã lưu: {metadata_path}")
    
    # ========== Tóm tắt ========== 
    logger.info("\n" + "=" * 80)
    logger.info("✅ IMPLICIT ALS TRAINING HOÀN TẤT")
    logger.info("=" * 80)
    logger.info("\n📁 Các file đã tạo:")
    logger.info(f"  - {model_path}")
    logger.info(f"  - {encoder_path}")
    logger.info(f"  - {metadata_path}")
    
    logger.info("\n📊 Hiệu năng Model:")
    for k, v in all_metrics.items():
        logger.info(f"  {k}: {v:.4f} ({v*100:.2f}%)")
    
    logger.info("=" * 80)
    
    return model, user_encoder, item_encoder, all_metrics


if __name__ == "__main__":
    model, user_enc, item_enc, metrics = main()
    
    # ========== VÍ DỤ: Lấy gợi ý cho user ========== 
    print("\n" + "="*80)
    print("VÍ DỤ: Top 10 gợi ý cho một user mẫu")
    print("="*80)
    
    try:
        # Lấy user đầu tiên từ encoder
        sample_user_id = user_enc.classes_[0]
        user_idx = user_enc.transform([sample_user_id])[0]
        
        # Load lại dữ liệu đã lọc (chỉ users/items trong encoder)
        script_dir = Path(__file__).resolve().parent
        data_dir = script_dir.parent / "data"
        df = pd.read_csv(data_dir / "processed_ratings.csv")
        df = df.rename(columns={'business_id': 'item_id', 'stars': 'rating'})
        
        # Lọc chỉ giữ users và items có trong encoder
        valid_users = set(user_enc.classes_)
        valid_items = set(item_enc.classes_)
        df = df[df['user_id'].isin(valid_users) & df['item_id'].isin(valid_items)]
        
        # Transform
        df['user_idx'] = user_enc.transform(df['user_id'])
        df['item_idx'] = item_enc.transform(df['item_id'])
        df['confidence'] = 1 + 10 * df['rating']
        
        n_users = len(user_enc.classes_)
        n_items = len(item_enc.classes_)
        
        user_items_matrix = csr_matrix(
            (df['confidence'].values, (df['user_idx'].values, df['item_idx'].values)),
            shape=(n_users, n_items),
            dtype=np.float32
        )
        
        # Lấy recommendations
        recommended_items, scores = model.recommend(
            user_idx, 
            user_items_matrix[user_idx],
            N=10,
            filter_already_liked_items=True
        )
        
        print(f"\nTop 10 gợi ý cho user {sample_user_id}:")
        for rank, (item_idx, score) in enumerate(zip(recommended_items, scores), 1):
            item_id = item_enc.inverse_transform([item_idx])[0]
            print(f"  {rank}. Item ID: {item_id} (confidence score: {score:.3f})")
            
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\nTop 10 gợi ý cho user {sample_user_id}:")
        for rank, (item_idx, score) in enumerate(zip(recommended_items, scores), 1):
            item_id = item_enc.inverse_transform([item_idx])[0]
            print(f"  {rank}. Experience ID: {item_id} (confidence score: {score:.3f})")
            
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
