# Experience Recommendation System - Collaborative Filtering

Hệ thống gợi ý trải nghiệm (experiences) sử dụng **Collaborative Filtering** với FastAPI, MongoDB, Redis - tương tự Airbnb Experiences.

## 🎯 Tính năng chính

- ✅ **Authentication**: JWT-based user authentication
- ✅ **Interaction Tracking**: Lưu hành vi user (view, click, wishlist, booking, rating)
- ✅ **Collaborative Filtering**: SVD Matrix Factorization algorithm
- ✅ **Batch Training**: Train model định kỳ với dữ liệu Yelp
- ✅ **Caching**: Redis cache cho recommendations
- ✅ **Data Analysis**: Phân tích 376K interactions từ Yelp dataset

## 📁 Cấu trúc dự án (Đã tổ chức lại)

```
Collabration/
├── .github/workflows/      # CI/CD workflows
├── auth/                   # Authentication (JWT, password hashing)
├── config/                 # Cấu hình (.env, settings)
├── data/                   # ✨ Dữ liệu training CSV (Yelp dataset)
│   ├── businesses.csv      # 150K businesses
│   ├── processed_ratings.csv  # 252K interactions (encoded)
│   └── user_item_ratings_sample.csv  # 376K raw interactions
├── database/               # MongoDB + Redis connection
├── models/                 # Data models & trained ML models
│   ├── cf_model.pkl       # Trained CF model
│   ├── encoders.pkl       # User/Item encoders
│   └── training_metadata.json  # Training metrics
├── recommender/            # CF algorithm (SVD, preprocessing, popularity)
├── routes/                 # API endpoints
├── schemas/                # Pydantic validation schemas
├── services/               # Business logic layer
├── scripts/                # ✨ Training & analysis scripts
│   ├── train_cf_model.py  # CF model training
│   └── analyze_yelp_data.py  # Data analysis
├── tests/                  # Unit tests
├── tmdb/                   # External API integration
├── logs/                   # Application logs
├── .env.sample            # Environment template
├── main.py                # FastAPI entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image
└── docker-compose.yml     # Multi-container setup
```

## 🔄 Workflow (7 Steps)

### Step 1: Lưu interaction vào DB
```bash
POST /api/interactions
{
  "movie_id": "...",
  "interaction_type": "wishlist",  # view/click/wishlist/booking/rating
  "rating": 4.5
}
```

### Step 2-3: Preprocessing & Label Encoding
- Tự động thực hiện khi train model
- Chuyển đổi interaction_type → rating (0-5)
- Encode user_id/movie_id → user_idx/item_idx
- Lưu encoders vào `models/encoders.pkl`

### Step 4: Train CF Model
```bash
POST /api/training/train-cf-model
```
- Train SVD model với interactions từ DB
- Chia train/test (80/20)
- Tính metrics (RMSE)

### Step 5: Lưu model
- Model → `models/cf_model.pkl`
- Encoders → `models/encoders.pkl`
- Metadata → `models/training_metadata.json`

### Step 6: Serve API Top-K
```bash
GET /api/recommendations?top_k=10
```
Response:
```json
{
  "user_id": "...",
  "recommendations": [
    {
      "movie_id": "...",
      "title": "Fight Club",
      "score": 4.8,
      "genres": ["Drama", "Thriller"]
    }
  ],
  "algorithm": "collaborative_filtering"
}
```

### Step 7: Frontend hiển thị
React/Vue/Angular render danh sách top-K recommendations.

## 🚀 Cài đặt

### 1. Clone repository
```bash
cd d:\PBL6\Collabration
```

### 2. Tạo virtual environment
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment
```bash
cp .env.sample .env
# Chỉnh sửa .env với các thông tin:
# - SECRET_KEY
# - MONGODB_URL
# - TMDB_API_KEY (optional)
```

### 5. Chạy với Docker (Recommended)
```bash
docker-compose up -d
```

Hoặc chạy thủ công:
```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Start Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Run FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

Sau khi chạy server, truy cập:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register` - Đăng ký user mới
- `POST /api/auth/login` - Login và nhận JWT token
- `GET /api/auth/me` - Thông tin user hiện tại

### Interactions (Step 1)
- `POST /api/interactions` - Lưu interaction mới
- `GET /api/interactions/my-interactions` - Lấy interactions của user
- `DELETE /api/interactions/{id}` - Xóa interaction

### Recommendations (Step 6)
- `GET /api/recommendations` - Top-K recommendations cho current user
- `GET /api/recommendations/{user_id}` - Recommendations cho user cụ thể

### Training (Step 4)
- `POST /api/training/train-cf-model` - Train CF model (async)
- `POST /api/training/train-cf-model-sync` - Train CF model (sync)

## 🧪 Testing

```bash
pytest tests/
```

## 📊 Collaborative Filtering Algorithm

Hệ thống sử dụng **Matrix Factorization** với SGD (Stochastic Gradient Descent):

```
Rating = global_mean + user_bias + item_bias + user_factors · item_factors
```

**Hyperparameters:**
- `n_factors`: 50 (latent dimensions)
- `n_epochs`: 20
- `learning_rate`: 0.005
- `regularization`: 0.02

## 🔄 Batch Training Schedule

Nên chạy training định kỳ:
- **Daily**: Cho hệ thống có nhiều interactions
- **2-3 ngày**: Cho hệ thống vừa phải
- **Weekly**: Cho hệ thống ít interactions

Sử dụng cron job hoặc scheduler:
```bash
# Crontab example (hàng ngày lúc 2AM)
0 2 * * * curl -X POST http://localhost:8000/api/training/train-cf-model
```

## ⚠️ Lưu ý

1. **Cold Start Problem**: 
   - User mới chưa có interactions → Dùng popularity-based recommendations
   - Cần tối thiểu 5 interactions để CF hoạt động tốt

2. **Interaction Types Weight**:
   - `booking`: 1.0 (cao nhất)
   - `wishlist`: 0.7
   - `click`: 0.3
   - `view`: 0.2

3. **Cache**:
   - Recommendations được cache 1 giờ
   - Tự động clear khi có interaction mới hoặc train model

4. **Realtime vs Batch**:
   - Hiện tại: Batch training (interactions mới không ảnh hưởng ngay)
   - Để realtime: Cần implement online learning hoặc hybrid approach

## 🛠️ Technologies

- **Backend**: FastAPI 0.104+
- **Database**: MongoDB (interactions, users, movies)
- **Cache**: Redis (recommendations cache)
- **ML**: NumPy, Pandas, Scikit-learn
- **Auth**: JWT (python-jose)
- **API**: TMDB API (movie data)

## 📈 Performance Tips

1. **Indexing**: Tạo indexes cho MongoDB
```javascript
db.interactions.createIndex({ "user_id": 1, "movie_id": 1 })
db.users.createIndex({ "username": 1 }, { unique: true })
db.movies.createIndex({ "tmdb_id": 1 }, { unique: true })
```

2. **Caching**: Sử dụng Redis cho recommendations
3. **Batch Size**: Train với batch khi có đủ data (>1000 interactions)

## 📝 License

MIT License

## 👥 Contributors

PBL6 Team

---

**Happy Coding! 🎬🍿**
