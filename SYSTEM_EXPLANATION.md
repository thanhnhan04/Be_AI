# 🎯 CƠ CHẾ HOẠT ĐỘNG CỦA HỆ THỐNG RECOMMENDATION

## 📋 Tổng Quan

Hệ thống sử dụng **Collaborative Filtering** với thuật toán **ALS (Alternating Least Squares)** để gợi ý experiences (địa điểm, hoạt động) cho người dùng dựa trên lịch sử tương tác.

---

## 🔄 QUY TRÌNH 7 BƯỚC

### **BƯỚC 1: Thu Thập Tương Tác** 📊
```
User → Frontend → POST /api/interactions
```

**Dữ liệu gửi lên:**
```json
{
  "experience_id": "Pns2l4eNsfO8kk83dixA6A",
  "interaction_type": "view",  // view, click, wishlist, booking, rating, completed
  "rating": 4.5  // optional, chỉ khi interaction_type = "rating"
}
```

**Quy đổi Implicit Rating:**
- `view` → 1.0 điểm
- `click` → 2.0 điểm  
- `wishlist` → 3.0 điểm
- `booking` → 5.0 điểm
- `rating` → 1-5 điểm (explicit)
- `completed` → 5.0 điểm

**Lưu vào MongoDB:**
```javascript
{
  user_id: "user123",
  business_id: "exp456", 
  interaction_type: "booking",
  rating: 5.0,
  timestamp: "2025-11-27T10:30:00"
}
```

---

### **BƯỚC 2: Tiền Xử Lý Dữ Liệu** 🔧
```
POST /api/training/preprocess
```

**Chức năng:**
1. Đọc tất cả interactions từ MongoDB
2. Gộp nhiều tương tác của cùng user-experience → rating trung bình
3. Xuất ra file CSV: `data/processed_ratings.csv`

**Kết quả CSV:**
```csv
user_id,business_id,rating
user_001,exp_123,4.5
user_001,exp_456,3.0
user_002,exp_123,5.0
```

---

### **BƯỚC 3: Mã Hóa Labels** 🏷️

**Vấn đề:** 
- User ID là string (`user_abc123`)
- Experience ID là string (`exp_xyz789`)
- ALS cần integer indices (0, 1, 2, ...)

**Giải pháp:** Sử dụng `LabelEncoder`
```python
user_encoder = LabelEncoder()
item_encoder = LabelEncoder()

# Chuyển đổi
"user_abc" → 0
"user_xyz" → 1
"exp_123"  → 0
"exp_456"  → 1
```

**Lưu trữ:**
- `models/encoders_als.pkl` → để mapping ngược lại sau này

---

### **BƯỚC 4: Huấn Luyện ALS Model** 🤖
```
POST /api/training/train
```

#### **4.1 Tạo User-Item Matrix**
```
        exp_0  exp_1  exp_2  exp_3
user_0   4.5    0.0    3.0    0.0
user_1   0.0    5.0    0.0    2.0
user_2   3.0    0.0    0.0    4.5
```
- Matrix rất **sparse** (nhiều giá trị 0)
- Sử dụng `scipy.sparse.csr_matrix` để tiết kiệm bộ nhớ

#### **4.2 Thuật Toán ALS**

**Khái niệm:**
- Mỗi user → 1 vector ẩn (latent vector) 100 chiều
- Mỗi item → 1 vector ẩn 100 chiều
- Rating dự đoán = `user_vector · item_vector` (dot product)

**Quá trình training:**
```python
# Khởi tạo ngẫu nhiên
user_factors = random(n_users × 100)
item_factors = random(n_items × 100)

# Lặp 15 lần
for iteration in range(15):
    # Bước 1: Fix item_factors, optimize user_factors
    # Giải phương trình least squares
    
    # Bước 2: Fix user_factors, optimize item_factors
    # Giải phương trình least squares
```

**Confidence Weighting:**
```python
confidence = 1 + alpha × rating
# rating=5 → confidence=201 (alpha=40)
# rating=1 → confidence=41
```
→ Rating cao hơn có trọng số lớn hơn

#### **4.3 Đánh Giá Model**

**Metrics:**
```
Hit Rate@10 = 34.60%
→ Trong top-10 gợi ý, 34.6% có ít nhất 1 item user thích
```

**Lưu model:**
```python
# models/als_model.pkl
{
  'user_factors': ndarray (2519 × 100),
  'item_factors': ndarray (9862 × 100)
}
```

---

### **BƯỚC 5: Lưu Model & Encoders** 💾

**Files được tạo:**
```
models/
├── als_model.pkl (4.95 MB)
│   ├── user_factors: 2519 users × 100 features
│   └── item_factors: 9862 items × 100 features
│
└── encoders_als.pkl (309 KB)
    ├── user_encoder: string → int mapping
    └── item_encoder: string → int mapping
```

---

### **BƯỚC 6: Serving API - Tạo Recommendations** 🚀

```
GET /api/recommendations?top_k=10
```

#### **Flow xử lý:**

**1. Load model một lần khi server start**
```python
model_data = pickle.load('models/als_model.pkl')
encoders = pickle.load('models/encoders_als.pkl')
```

**2. Khi user request:**
```python
user_id = "user_abc123"

# Kiểm tra cache Redis
cache_key = f"recommendations:{user_id}:10"
if redis.exists(cache_key):
    return redis.get(cache_key)  # Trả về ngay

# Nếu không có cache
```

**3. Xử lý Cold Start (User mới)**
```python
if user_id not in user_encoder.classes_:
    # User chưa có trong training data
    # → Trả về Popular experiences (theo rating + review_count)
    return get_popular_experiences(top_k=10)
```

**4. Collaborative Filtering (User đã biết)**
```python
# Map user_id → user_idx
user_idx = user_encoder.transform(["user_abc123"])[0]  # → 42

# Lấy user vector
user_vec = user_factors[42]  # shape: (100,)

# Tính scores cho TẤT CẢ items
scores = item_factors @ user_vec  # shape: (9862,)
# scores[i] = similarity giữa user và item i

# Ví dụ:
# scores = [2.3, 4.8, 1.2, 5.1, 3.9, ...]
#           exp0  exp1  exp2  exp3  exp4

# Sắp xếp và lấy top-K
top_indices = np.argsort(scores)[-10:][::-1]
# top_indices = [3, 1, 4, 7, 12, 20, 35, 8, 15, 22]

# Map indices → experience_ids
top_exp_ids = item_encoder.inverse_transform(top_indices)
# ["exp_xyz", "exp_abc", "exp_def", ...]

# Lấy scores tương ứng
top_scores = scores[top_indices]
# [5.1, 4.8, 3.9, 3.7, 3.5, ...]
```

**5. Fetch chi tiết từ MongoDB**
```python
experiences = []
for exp_id, score in zip(top_exp_ids, top_scores):
    exp = await db.businesses.find_one({"business_id": exp_id})
    experiences.append({
        "experience_id": exp_id,
        "name": exp['name'],
        "categories": exp['categories'],
        "stars": exp['stars'],
        "score": float(score)  # ALS confidence score
    })
```

**6. Lưu vào cache**
```python
await redis.set(cache_key, json.dumps(result), ex=3600)  # Cache 1h
```

**7. Trả về JSON**
```json
{
  "user_id": "user_abc123",
  "recommendations": [
    {
      "experience_id": "exp_xyz",
      "name": "Grand Canyon Adventure",
      "categories": "Tours, Outdoor",
      "stars": 4.8,
      "score": 5.1
    },
    ...
  ],
  "total": 10,
  "generated_at": "2025-11-27T10:45:30",
  "model": "ALS Collaborative Filtering"
}
```

---

### **BƯỚC 7: Frontend Display** 🎨

```jsx
// React Component
const RecommendationList = () => {
  const [recommendations, setRecommendations] = useState([]);
  
  useEffect(() => {
    fetch('/api/recommendations?top_k=10', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setRecommendations(data.recommendations));
  }, []);
  
  return (
    <div className="recommendations">
      {recommendations.map(exp => (
        <ExperienceCard 
          key={exp.experience_id}
          name={exp.name}
          stars={exp.stars}
          score={exp.score}
        />
      ))}
    </div>
  );
};
```

---

## 🔑 ĐIỂM QUAN TRỌNG

### **1. Implicit vs Explicit Feedback**

**Explicit:** User đánh giá trực tiếp (rating 1-5 sao)
```
user_001 rate exp_123: ⭐⭐⭐⭐ (4 stars)
```

**Implicit:** User tương tác nhưng không rating
```
user_001 viewed exp_123 → confidence = 1.0
user_001 booked exp_456 → confidence = 5.0
```

→ Hệ thống dùng **cả hai** nhưng tập trung vào **implicit** (nhiều data hơn)

---

### **2. Cold Start Problem**

**Vấn đề:** User mới chưa có interaction → không thể dùng CF

**Giải pháp:**
1. **Popularity-based:** Top experiences theo rating × review_count
2. **Content-based:** Gợi ý theo categories yêu thích (nếu có profile)
3. **Hybrid:** Kết hợp cả hai

Trong code hiện tại:
```python
if user_id not in user_encoder.classes_:
    return await self._get_popular_experiences(db, top_k)
```

---

### **3. Matrix Factorization**

**Ý tưởng:**
```
Rating Matrix (sparse)  →  User Matrix  ×  Item Matrix
   2519 × 9862                2519×100      100×9862

[4.5  0  3  0  ...]     [0.2 0.1 ...]   [0.3 0.5 ...]
[0  5  0  2  ...]    =  [0.1 0.3 ...]  ×[0.1 0.2 ...]
[3  0  0  4.5...]       [0.4 0.2 ...]   [0.4 0.1 ...]
                                         [...      ]
```

**Lợi ích:**
- Giảm chiều từ 9862 → 100 features
- Học được "ẩn danh" patterns (users thích outdoor cũng thích adventure)
- Dự đoán được ratings chưa có (missing values)

---

### **4. Confidence Weighting**

```python
confidence = 1 + alpha × rating

# alpha = 40
booking (rating=5) → confidence = 1 + 40×5 = 201
view (rating=1)    → confidence = 1 + 40×1 = 41
```

→ Model "tin tưởng" hành vi booking gấp 5 lần view

---

### **5. Caching Strategy**

```
User request → Check Redis
              ├─ HIT  → Return (< 10ms)
              └─ MISS → ALS predict → Save to Redis → Return (~ 200ms)
```

**Cache key:** `recommendations:{user_id}:{top_k}`  
**TTL:** 1 hour

→ Giảm tải cho ALS model, tăng tốc response

---

## 📊 VÍ DỤ CỤ THỂ

### **Scenario: User "Alice" vào hệ thống**

**1. Alice đăng ký tài khoản**
```
POST /api/auth/register
→ user_id = "alice_123" (MongoDB ObjectId)
```

**2. Alice xem vài experiences**
```
POST /api/interactions
{
  "experience_id": "grand_canyon_tour",
  "interaction_type": "view"
}
→ Rating = 1.0, lưu vào MongoDB
```

**3. Alice thích và add wishlist**
```
POST /api/interactions
{
  "experience_id": "grand_canyon_tour",
  "interaction_type": "wishlist"
}
→ Rating = 3.0 (ghi đè 1.0 cũ)
```

**4. Alice book tour**
```
POST /api/interactions
{
  "experience_id": "grand_canyon_tour",
  "interaction_type": "booking"
}
→ Rating = 5.0 (ghi đè 3.0)
```

**5. Sau 1 tuần, admin retrain model**
```
POST /api/training/preprocess → CSV
POST /api/training/train → ALS model mới
→ "alice_123" giờ có trong user_encoder
```

**6. Alice quay lại, request recommendations**
```
GET /api/recommendations?top_k=10

Backend:
1. Load model
2. alice_123 → user_idx = 2520 (user mới)
3. user_vec = user_factors[2520]
4. scores = item_factors @ user_vec
5. Top-10: [Yellowstone, Zion, Yosemite, ...]
   → Vì Alice thích Grand Canyon (outdoor tour)
   → Model học được pattern: outdoor tours similar nhau
6. Return JSON
```

**7. Frontend hiển thị**
```
🏔️ Gợi ý cho bạn:
- Yellowstone National Park Tour ⭐4.9 (Score: 5.2)
- Zion Canyon Adventure ⭐4.7 (Score: 4.8)
- Yosemite Hiking Trip ⭐4.8 (Score: 4.6)
...
```

---

## 🛠️ KỸ THUẬT SỬ DỤNG

### **1. Thuật toán:** 
- **ALS (Alternating Least Squares)** - Hu et al., 2008
- Dùng bởi Netflix, Spotify, YouTube

### **2. Libraries:**
- `numpy`: Matrix operations
- `scipy.sparse`: Sparse matrix (tiết kiệm RAM)
- `sklearn.preprocessing`: LabelEncoder
- `pickle`: Serialize model

### **3. Database:**
- **MongoDB**: Lưu interactions, experiences (NoSQL - flexible schema)
- **Redis**: Cache recommendations (in-memory - fast)

### **4. API:**
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **JWT**: Authentication tokens

---

## 🎯 TÓM TẮT WORKFLOW

```
USER INTERACTION
    ↓
[MongoDB] interactions collection
    ↓
PREPROCESS → CSV file
    ↓
LABEL ENCODING → user_idx, item_idx
    ↓
ALS TRAINING → user_factors, item_factors
    ↓
SAVE MODEL → als_model.pkl, encoders_als.pkl
    ↓
LOAD MODEL khi server start
    ↓
USER REQUEST /api/recommendations
    ↓
CHECK REDIS CACHE
    ↓
ALS PREDICTION (user_vec · item_vec)
    ↓
TOP-K SORTING
    ↓
FETCH DETAILS từ MongoDB
    ↓
CACHE RESULT in Redis
    ↓
RETURN JSON to Frontend
    ↓
FRONTEND DISPLAY
```

---

## 📚 TÀI LIỆU THAM KHẢO

1. **Paper gốc:** "Collaborative Filtering for Implicit Feedback Datasets" (Hu et al., 2008)
2. **Netflix Prize:** Matrix Factorization techniques
3. **Spotify Recommendations:** Implicit ALS for music
4. **Code:** `scripts/train_als_model.py` - Implementation chi tiết

---

## ❓ FAQ

**Q: Tại sao dùng ALS thay vì Deep Learning?**  
A: ALS nhanh hơn, ít data hơn, explainable hơn, đủ tốt cho most cases

**Q: Làm sao biết model tốt hay xấu?**  
A: Hit Rate@10 = 34.6% → Trong top-10, có 34.6% cơ hội user thích ít nhất 1 item

**Q: User mới không có data thì sao?**  
A: Trả về Popular experiences (theo stars × review_count)

**Q: Làm sao update model khi có data mới?**  
A: Gọi `POST /api/training/train` → Model retrain và replace cũ

**Q: Redis cache bao lâu?**  
A: 1 giờ (3600s), có thể config trong `.env`

---

🎉 **Chúc bạn hiểu rõ hệ thống!**
