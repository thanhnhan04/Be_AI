# 🎯 Experience Recommendation System - Tổng Quan Hệ Thống

## 📋 Mô Tả
Hệ thống recommendation AI độc lập, nhận data từ server chính và trả về top experiences được recommend cho user dựa trên ALS Collaborative Filtering model.

---

## 🔄 Luồng Hoạt Động

### 1️⃣ **Nhận Data Từ Server Chính**

#### **Sync User Mới**
```http
POST /api/sync/users
Body: {
  "user_id": "user123",
  "email": "user@example.com",  // optional
  "preferences": []              // optional
}
```

#### **Sync Experience Mới**
```http
POST /api/experiences
Body: {
  "name": "Restaurant ABC",
  "city": "Ho Chi Minh",
  "stars": 4.5,
  "categories": "Food, Asian"
}
```

#### **Sync User Interaction**
```http
POST /api/interactions
Body: {
  "user_id": "user123",
  "experience_id": "exp456",
  "interaction_type": "view|click|wishlist|booking",
  "rating": 4.5  // optional
}
```

**→ Server tự động lưu vào MongoDB**

---

### 2️⃣ **Get Recommendations**

#### **Request từ Server Chính**
```http
GET /api/recommendations/user/{user_id}?top_k=10
```

#### **Response Logic:**

**A. User Đã Có Trong Model (Old User):**
- Load ALS model đã train
- Tính similarity scores với tất cả experiences
- Trả về top-K experiences có score cao nhất
```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "experience_id": "exp456",
      "name": "Restaurant ABC",
      "location": "Ho Chi Minh",
      "score": 0.85,
      "reason": "Based on your preferences"
    }
  ],
  "model": "ALS Collaborative Filtering"
}
```

**B. User Mới (New User - Cold Start):**
- Phát hiện user_id không có trong model
- Tự động fallback về **Popular Experiences**
- Trả về top experiences có review_count cao nhất
```json
{
  "user_id": "new_user_999",
  "recommendations": [
    {
      "name": "Popular Restaurant",
      "review_count": 5000,
      "average_rating": 4.8,
      "reason": "Popular experience"
    }
  ],
  "model": "Popularity-based"
}
```

---

### 3️⃣ **Auto Retrain Model (Mỗi 6 Giờ)**

#### **Scheduler Background Job:**
```python
# Chạy tự động mỗi 6 giờ
retrain_job():
  1. Load interactions từ MongoDB
  2. Preprocess data (user_id, experience_id → ratings)
  3. Train ALS model mới
  4. Save model + encoders
  5. Clear cache → Model mới được apply
```

#### **Mapping Interaction → Rating:**
- `view`: 1.0
- `click`: 2.0
- `wishlist`: 3.0
- `booking`: 5.0
- `rating`: user's explicit rating (1-5)

#### **Model Files:**
- `models/als_model.pkl` - ALS model factors
- `models/encoders_als.pkl` - User & Item encoders
- `models/training_metadata.json` - Metadata

---

## 🗄️ Database Structure

### **MongoDB Collections:**

#### **1. users**
```json
{
  "_id": ObjectId,
  "user_id": "user123",        // From main server
  "email": "user@example.com",
  "preferences": [],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### **2. experiences**
```json
{
  "_id": ObjectId,
  "experience_id": "exp456",   // Unique ID (from Yelp or generated)
  "name": "Restaurant ABC",
  "city": "Ho Chi Minh",
  "stars": 4.5,
  "review_count": 1234,
  "categories": "Food, Asian",
  "price": 100000
}
```

#### **3. interactions**
```json
{
  "_id": ObjectId,
  "user_id": "user123",
  "experience_id": "exp456",        // String for model training
  "experience_ref": ObjectId,       // Reference to experiences._id
  "interaction_type": "booking",
  "rating": 5.0,
  "created_at": ISODate
}
```

---

## 🚀 API Endpoints

### **User Sync APIs**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sync/users` | Tạo/update user |
| GET | `/api/sync/users/{user_id}` | Get user info |
| DELETE | `/api/sync/users/{user_id}` | Xóa user |

### **Experience APIs**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/experiences` | Tạo experience mới |

### **Interaction APIs**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/interactions` | Lưu user interaction |
| GET | `/api/interactions/user/{user_id}` | Get user interactions |

### **Recommendation APIs**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recommendations/user/{user_id}` | Get personalized recommendations |
| GET | `/api/recommendations/similar/{exp_id}` | Get similar experiences |

---

## ⚙️ Cấu Hình

### **Environment Variables (.env)**
```bash
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=recommend_experiences

# Redis (Cache)
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key
```

### **Model Hyperparameters**
```python
# ALS Model Config
factors = 100              # Latent factors
regularization = 0.05
iterations = 15
alpha = 40                 # Confidence weighting
```

---

## 🐳 Docker Deployment

### **Containers:**
1. **MongoDB** (port 27018) - Data storage
2. **Redis** (port 6379) - Cache layer
3. **Backend** (port 8000) - FastAPI server

### **Start:**
```bash
docker-compose up -d --build
```

### **Check Logs:**
```bash
docker-compose logs backend --tail 50
```

---

## 📊 Model Performance

**Current Metrics:**
- **Users in Model:** 5,490
- **Experiences in Model:** 20,127
- **Total Interactions:** 252,361
- **Hit Rate@10:** 10.60%

**Auto Retrain:**
- Frequency: Every 6 hours
- Trigger: APScheduler background job
- Process: `retrain_from_mongodb.py`

---

## ✅ Checklist Hoàn Thiện

### **✅ Data Reception (Nhận từ server chính)**
- [x] Sync user API
- [x] Sync experience API
- [x] Sync interaction API
- [x] Auto save to MongoDB

### **✅ Recommendation Logic**
- [x] ALS Collaborative Filtering
- [x] Cold start handling (Popular experiences)
- [x] New user detection
- [x] Score calculation & ranking

### **✅ Auto Training**
- [x] Scheduler (6h interval)
- [x] Load data from MongoDB
- [x] Retrain ALS model
- [x] Auto model reload

### **✅ API Responses**
- [x] Personalized recommendations (old users)
- [x] Popular recommendations (new users)
- [x] Similar experiences
- [x] JSON format chuẩn

### **✅ Database**
- [x] MongoDB collections (users, experiences, interactions)
- [x] Proper indexing
- [x] Data consistency

### **✅ Deployment**
- [x] Docker containers
- [x] Environment config
- [x] Logging system

---

## 🔍 Testing

### **Test New User (Cold Start):**
```bash
# User không có trong DB → Popular experiences
curl "http://localhost:8000/api/recommendations/user/new_user_999?top_k=5"
```

### **Test Existing User:**
```bash
# User có trong model → Personalized recommendations
curl "http://localhost:8000/api/recommendations/user/OyoGAe7OKpv6SyGZT5g77Q?top_k=5"
```

### **Test Sync:**
```bash
# Sync user mới
curl -X POST "http://localhost:8000/api/sync/users" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user_001"}'
```

---

## 📈 Flow Diagram

```
Server Chính
    │
    ├─→ POST /api/sync/users ────→ MongoDB (users)
    │
    ├─→ POST /api/experiences ───→ MongoDB (experiences)
    │
    └─→ POST /api/interactions ──→ MongoDB (interactions)
                                         │
                                         ▼
                              [APScheduler: 6h/lần]
                                         │
                                         ▼
                              retrain_from_mongodb.py
                                         │
                                         ▼
                              Train ALS Model → Save
                                         │
                                         ▼
                    GET /api/recommendations/user/{id}
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                    User in Model?              User NOT in Model?
                          │                             │
                    [ALS Prediction]           [Popular Experiences]
                          │                             │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                              Return top-K experiences
                                         │
                                         ▼
                                  Server Chính
```

---

## 🎯 Kết Luận

**Hệ thống đã HOÀN THIỆN với đầy đủ tính năng:**

✅ Nhận data từ server chính (users, experiences, interactions)  
✅ Tự động lưu vào MongoDB  
✅ Trả recommendations cho user (personalized hoặc popular)  
✅ Xử lý new user (cold start) tự động  
✅ Auto retrain model mỗi 6 giờ  
✅ Model mới được apply tự động  
✅ Không cần authentication (server-to-server)  

**Ready for production! 🚀**
