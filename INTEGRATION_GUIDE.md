# 🔌 HƯỚNG DẪN TÍCH HỢP HỆ THỐNG RECOMMENDATION VÀO EXPERIENCE PLATFORM

## 📋 Tổng Quan Tích Hợp

Hướng dẫn này giúp bạn tích hợp hệ thống AI Recommendation vào hệ thống Experience hiện tại của bạn.

---

## 🎯 YÊU CẦU HỆ THỐNG

### **Backend Experience của bạn cần có:**
- ✅ Database lưu experiences (MongoDB/PostgreSQL/MySQL)
- ✅ User authentication system
- ✅ API endpoints cho experiences
- ✅ Tracking user interactions (view, click, bookmark, etc.)

### **Recommendation System cần:**
- ✅ MongoDB (đã cài)
- ✅ Python 3.8+ (đã có 3.13)
- ✅ FastAPI server (đang chạy port 8000)

---

## 🏗️ KIẾN TRÚC TÍCH HỢP

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vue/Angular)              │
│  - Experience List                                           │
│  - Experience Detail                                         │
│  - Recommendation Widget                                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─────────────────┬─────────────────────────────┐
               │                 │                             │
               ▼                 ▼                             ▼
┌──────────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  EXPERIENCE BACKEND  │  │  AUTH SERVICE   │  │  RECOMMENDATION API  │
│  (Your System)       │  │  (Your System)  │  │  (This AI System)    │
│                      │  │                 │  │                      │
│  - CRUD Experiences  │  │  - Login        │  │  - GET /recommend    │
│  - Search/Filter     │  │  - Register     │  │  - POST /interact    │
│  - Booking           │  │  - JWT Token    │  │  - POST /train       │
└──────┬───────────────┘  └────────┬────────┘  └──────┬───────────────┘
       │                           │                    │
       ▼                           ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                         DATABASES                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Experiences DB  │  │  Users DB    │  │  Interactions   │ │
│  │ (Your DB)       │  │  (Your DB)   │  │  (MongoDB)      │ │
│  └─────────────────┘  └──────────────┘  └─────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 CẤU TRÚC DỮ LIỆU CẦN ĐỒNG BỘ

### **1. Collection `experiences` trong MongoDB**

**Cách 1: Sync từ DB của bạn sang MongoDB (Recommended)**
```python
# Script sync từ PostgreSQL/MySQL → MongoDB
import pymongo
import psycopg2  # hoặc mysql.connector

# Connect to your DB
your_db = psycopg2.connect(...)
cursor = your_db.cursor()
cursor.execute("SELECT id, name, category, rating, review_count FROM experiences")

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
db = mongo_client["recommend_experiences"]

# Sync data
for row in cursor:
    db.experiences.update_one(
        {"business_id": row[0]},  # experience_id
        {"$set": {
            "business_id": row[0],
            "name": row[1],
            "categories": row[2],
            "stars": row[3],
            "review_count": row[4]
        }},
        upsert=True
    )
```

**Cách 2: Webhook realtime (Advanced)**
```python
# Trong Experience Backend của bạn
# Mỗi khi create/update experience → gọi API này

import httpx

async def sync_experience_to_recommendation(experience_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:8000/api/sync/experience",
            json={
                "business_id": experience_data["id"],
                "name": experience_data["name"],
                "categories": experience_data["category"],
                "stars": experience_data["rating"],
                "review_count": experience_data["review_count"]
            }
        )
```

### **2. Collection `interactions` tracking**

**Khi user tương tác với experience, gọi API:**
```javascript
// Frontend code
const trackInteraction = async (experienceId, interactionType) => {
  const token = localStorage.getItem('jwt_token');
  
  await fetch('http://localhost:8000/api/interactions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      experience_id: experienceId,
      interaction_type: interactionType  // 'view', 'click', 'wishlist', 'booking'
    })
  });
};

// Sử dụng
trackInteraction('exp_123', 'view');      // User xem experience
trackInteraction('exp_123', 'click');     // User click vào detail
trackInteraction('exp_123', 'wishlist');  // User add to wishlist
trackInteraction('exp_123', 'booking');   // User book experience
```

---

## 🔐 XÁC THỰC (AUTHENTICATION)

### **Option 1: Shared JWT (Recommended)**

**Bước 1:** Cấu hình cùng SECRET_KEY
```env
# File .env của Recommendation System
SECRET_KEY="same_secret_key_with_your_main_system"
ALGORITHM="HS256"
```

**Bước 2:** Frontend gửi cùng 1 JWT token
```javascript
// Token từ hệ thống Experience của bạn
const token = localStorage.getItem('jwt_token');

// Gửi cho cả 2 backends
await fetch('https://your-experience-api.com/api/experiences', {
  headers: { 'Authorization': `Bearer ${token}` }
});

await fetch('http://localhost:8000/api/recommendations', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### **Option 2: Separate Authentication**

**Bước 1:** User login vào hệ thống Experience → lấy token
```javascript
const loginResponse = await fetch('https://your-api.com/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password })
});
const mainToken = loginResponse.token;
```

**Bước 2:** Dùng mainToken để lấy recommendation token
```javascript
const recResponse = await fetch('http://localhost:8000/api/auth/exchange-token', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${mainToken}` }
});
const recToken = recResponse.token;
```

---

## 🎨 FRONTEND INTEGRATION

### **1. Component: Recommendation Widget**

```jsx
// RecommendationWidget.jsx
import React, { useEffect, useState } from 'react';

const RecommendationWidget = ({ userId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const token = localStorage.getItem('jwt_token');
        const response = await fetch(
          'http://localhost:8000/api/recommendations?top_k=10',
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        const data = await response.json();
        setRecommendations(data.recommendations);
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [userId]);

  if (loading) return <div>Loading recommendations...</div>;

  return (
    <div className="recommendation-widget">
      <h2>🎯 Gợi ý cho bạn</h2>
      <div className="recommendation-grid">
        {recommendations.map(exp => (
          <ExperienceCard
            key={exp.experience_id}
            id={exp.experience_id}
            name={exp.name}
            rating={exp.stars}
            categories={exp.categories}
            aiScore={exp.score}
          />
        ))}
      </div>
    </div>
  );
};

export default RecommendationWidget;
```

### **2. Tracking User Interactions**

```jsx
// ExperienceDetail.jsx
import { useEffect } from 'react';
import { trackInteraction } from '../services/recommendation';

const ExperienceDetail = ({ experienceId }) => {
  // Track view khi user vào trang
  useEffect(() => {
    trackInteraction(experienceId, 'view');
  }, [experienceId]);

  const handleAddToWishlist = () => {
    // Thêm vào wishlist trong DB của bạn
    addToWishlist(experienceId);
    
    // Track cho recommendation system
    trackInteraction(experienceId, 'wishlist');
  };

  const handleBooking = () => {
    // Xử lý booking trong hệ thống của bạn
    processBooking(experienceId);
    
    // Track cho recommendation system
    trackInteraction(experienceId, 'booking');
  };

  return (
    <div>
      <h1>{experience.name}</h1>
      <button onClick={handleAddToWishlist}>💙 Wishlist</button>
      <button onClick={handleBooking}>🎟️ Book Now</button>
    </div>
  );
};
```

### **3. Service Layer**

```javascript
// services/recommendation.js
const RECOMMENDATION_API = 'http://localhost:8000/api';

export const trackInteraction = async (experienceId, interactionType, rating = null) => {
  try {
    const token = localStorage.getItem('jwt_token');
    const response = await fetch(`${RECOMMENDATION_API}/interactions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        experience_id: experienceId,
        interaction_type: interactionType,
        rating: rating
      })
    });
    
    if (!response.ok) {
      console.warn('Failed to track interaction');
    }
  } catch (error) {
    // Silent fail - không ảnh hưởng UX
    console.error('Interaction tracking error:', error);
  }
};

export const getRecommendations = async (topK = 10) => {
  const token = localStorage.getItem('jwt_token');
  const response = await fetch(
    `${RECOMMENDATION_API}/recommendations?top_k=${topK}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.json();
};
```

---

## 🔄 DATA SYNCHRONIZATION

### **Script 1: Initial Data Import**

```python
# scripts/import_from_your_db.py
"""
Import experiences từ database hiện tại sang MongoDB
Chạy 1 lần khi setup
"""
import pymongo
import psycopg2  # hoặc mysql.connector, hoặc SQLAlchemy

# Config
YOUR_DB_CONFIG = {
    'host': 'localhost',
    'database': 'experience_db',
    'user': 'postgres',
    'password': 'your_password'
}

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "recommend_experiences"

def import_experiences():
    # Connect to your database
    conn = psycopg2.connect(**YOUR_DB_CONFIG)
    cursor = conn.cursor()
    
    # Connect to MongoDB
    mongo_client = pymongo.MongoClient(MONGO_URL)
    db = mongo_client[MONGO_DB]
    
    # Query experiences
    cursor.execute("""
        SELECT 
            id,
            name,
            category,
            rating,
            review_count,
            city,
            state
        FROM experiences
        WHERE is_active = true
    """)
    
    count = 0
    for row in cursor:
        db.businesses.update_one(
            {"business_id": str(row[0])},
            {"$set": {
                "business_id": str(row[0]),
                "name": row[1],
                "categories": row[2],
                "stars": float(row[3]) if row[3] else 0.0,
                "review_count": int(row[4]) if row[4] else 0,
                "city": row[5],
                "state": row[6]
            }},
            upsert=True
        )
        count += 1
        if count % 100 == 0:
            print(f"Imported {count} experiences...")
    
    print(f"✅ Imported {count} experiences successfully!")
    
    cursor.close()
    conn.close()
    mongo_client.close()

if __name__ == "__main__":
    import_experiences()
```

### **Script 2: Incremental Sync (Daily/Hourly)**

```python
# scripts/sync_experiences_daily.py
"""
Sync experiences mới/updated từ DB → MongoDB
Chạy theo schedule (cron job/celery)
"""
from datetime import datetime, timedelta
import pymongo
import psycopg2

def sync_updated_experiences(last_sync_time):
    conn = psycopg2.connect(**YOUR_DB_CONFIG)
    cursor = conn.cursor()
    
    mongo_client = pymongo.MongoClient(MONGO_URL)
    db = mongo_client[MONGO_DB]
    
    # Query experiences updated sau last_sync_time
    cursor.execute("""
        SELECT id, name, category, rating, review_count
        FROM experiences
        WHERE updated_at > %s
    """, (last_sync_time,))
    
    count = 0
    for row in cursor:
        db.businesses.update_one(
            {"business_id": str(row[0])},
            {"$set": {
                "business_id": str(row[0]),
                "name": row[1],
                "categories": row[2],
                "stars": float(row[3]),
                "review_count": int(row[4]),
                "synced_at": datetime.now()
            }},
            upsert=True
        )
        count += 1
    
    print(f"✅ Synced {count} updated experiences")
    
    cursor.close()
    conn.close()
    mongo_client.close()

# Chạy mỗi giờ
if __name__ == "__main__":
    last_sync = datetime.now() - timedelta(hours=1)
    sync_updated_experiences(last_sync)
```

---

## 🔧 BACKEND INTEGRATION

### **Option 1: Microservices (Recommended)**

```
┌──────────────────┐         ┌──────────────────────┐
│ Experience API   │         │ Recommendation API   │
│ (Port 3000)      │◄───────►│ (Port 8000)          │
│                  │  HTTP   │                      │
│ - CRUD Exp       │         │ - GET recommend      │
│ - Booking        │         │ - POST interaction   │
│ - Search         │         │ - POST train         │
└──────────────────┘         └──────────────────────┘
```

**Gọi từ Experience Backend:**
```python
# experience_backend/services/recommendation.py
import httpx

RECOMMENDATION_API = "http://localhost:8000/api"

async def get_recommendations_for_user(user_id: str, top_k: int = 10):
    """Lấy recommendations từ AI service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RECOMMENDATION_API}/recommendations",
            params={"top_k": top_k},
            headers={"X-User-ID": user_id}  # hoặc JWT token
        )
        return response.json()

async def track_user_interaction(user_id: str, exp_id: str, action: str):
    """Track interaction vào recommendation system"""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{RECOMMENDATION_API}/interactions",
            json={
                "experience_id": exp_id,
                "interaction_type": action
            },
            headers={"X-User-ID": user_id}
        )
```

### **Option 2: Single Backend với SDK**

```python
# experience_backend/app.py
from fastapi import FastAPI
from recommendation_sdk import RecommendationClient

app = FastAPI()
rec_client = RecommendationClient("http://localhost:8000")

@app.get("/api/experiences/{exp_id}")
async def get_experience(exp_id: str, user_id: str):
    # Lấy experience từ DB của bạn
    experience = await db.experiences.find_one({"id": exp_id})
    
    # Track view
    await rec_client.track("view", user_id, exp_id)
    
    # Lấy similar experiences
    similar = await rec_client.get_similar(exp_id, top_k=5)
    
    return {
        "experience": experience,
        "similar_experiences": similar
    }
```

---

## 📅 TRAINING & RETRAINING

### **Setup 1: Manual Retrain (Khi có đủ data mới)**

```bash
# Khi có 1000+ interactions mới
curl -X POST http://localhost:8000/api/training/preprocess
curl -X POST http://localhost:8000/api/training/train
```

### **Setup 2: Scheduled Retrain (Tự động)**

**Cron Job (Linux/Mac):**
```bash
# Retrain mỗi tuần (Sunday 2 AM)
0 2 * * 0 curl -X POST http://localhost:8000/api/training/train
```

**Windows Task Scheduler:**
```powershell
# Tạo task chạy mỗi tuần
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
$action = New-ScheduledTaskAction -Execute "curl" -Argument "-X POST http://localhost:8000/api/training/train"
Register-ScheduledTask -TaskName "RetrainALS" -Trigger $trigger -Action $action
```

**Celery (Python):**
```python
# tasks.py
from celery import Celery
import httpx

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def retrain_recommendation_model():
    """Retrain model hàng tuần"""
    client = httpx.Client()
    
    # Preprocess
    client.post('http://localhost:8000/api/training/preprocess')
    
    # Train
    response = client.post('http://localhost:8000/api/training/train')
    
    return response.json()

# Schedule: Mỗi Sunday 2 AM
app.conf.beat_schedule = {
    'retrain-weekly': {
        'task': 'tasks.retrain_recommendation_model',
        'schedule': crontab(hour=2, minute=0, day_of_week=0)
    }
}
```

---

## 🚀 DEPLOYMENT

### **Production Setup**

**1. Deploy Recommendation API:**
```bash
# Docker
docker build -t recommendation-api .
docker run -d -p 8000:8000 \
  -e MONGODB_URL="mongodb://mongo:27017" \
  -e SECRET_KEY="your_production_secret" \
  recommendation-api

# hoặc với Docker Compose
docker-compose up -d
```

**2. Reverse Proxy (Nginx):**
```nginx
# /etc/nginx/sites-available/your-domain
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    # Experience API
    location /api/experiences {
        proxy_pass http://localhost:3000;
    }

    # Recommendation API
    location /api/recommendations {
        proxy_pass http://localhost:8000;
    }
    
    location /api/interactions {
        proxy_pass http://localhost:8000;
    }
}
```

**3. Environment Variables:**
```env
# Production .env
MONGODB_URL=mongodb://production-mongo:27017
MONGODB_DB_NAME=recommend_experiences
SECRET_KEY=your_super_secret_key_production
REDIS_HOST=production-redis
REDIS_PORT=6379
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DEBUG=False
```

---

## ✅ CHECKLIST TÍCH HỢP

### **Phase 1: Setup (1-2 ngày)**
- [ ] Cài đặt MongoDB local
- [ ] Import experiences từ DB của bạn → MongoDB
- [ ] Test Recommendation API với Postman/curl
- [ ] Cấu hình CORS cho frontend domain

### **Phase 2: Authentication (1 ngày)**
- [ ] Setup shared SECRET_KEY hoặc token exchange
- [ ] Test authentication flow
- [ ] Verify JWT token từ frontend → backend

### **Phase 3: Frontend Integration (2-3 ngày)**
- [ ] Tạo RecommendationWidget component
- [ ] Implement interaction tracking (view, click, wishlist, booking)
- [ ] Test recommendations hiển thị đúng
- [ ] Handle loading states & errors

### **Phase 4: Data Sync (1-2 ngày)**
- [ ] Viết script sync experiences (initial + incremental)
- [ ] Setup cron job/scheduled task
- [ ] Test data consistency

### **Phase 5: Training (1 ngày)**
- [ ] Thu thập ít nhất 500+ interactions
- [ ] Chạy training lần đầu
- [ ] Verify model metrics (Hit Rate@10)
- [ ] Setup auto-retrain schedule

### **Phase 6: Testing & Optimization (2-3 ngày)**
- [ ] A/B test recommendations vs random
- [ ] Monitor API response time
- [ ] Setup Redis caching
- [ ] Load testing

### **Phase 7: Production Deploy (1-2 ngày)**
- [ ] Deploy Docker containers
- [ ] Setup Nginx reverse proxy
- [ ] Configure production environment
- [ ] Monitor logs & errors

**Total: ~10-14 ngày**

---

## 📞 API ENDPOINTS CHO INTEGRATION

### **1. Get Recommendations**
```
GET /api/recommendations?top_k=10
Authorization: Bearer {jwt_token}

Response:
{
  "user_id": "user_123",
  "recommendations": [...],
  "total": 10,
  "model": "ALS"
}
```

### **2. Track Interaction**
```
POST /api/interactions
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "experience_id": "exp_456",
  "interaction_type": "view",
  "rating": 4.5  // optional
}

Response: {"status": "success"}
```

### **3. Get Similar Experiences**
```
GET /api/recommendations/similar/{experience_id}?top_k=5
Authorization: Bearer {jwt_token}

Response:
{
  "experience_id": "exp_456",
  "similar": [...]
}
```

### **4. Retrain Model**
```
POST /api/training/train
Authorization: Bearer {admin_token}

Response:
{
  "status": "success",
  "metrics": {
    "hit_rate": 0.346
  }
}
```

---

## 🐛 TROUBLESHOOTING

### **Problem 1: CORS Error**
```
Error: Access to fetch has been blocked by CORS policy
```
**Solution:**
```env
# .env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### **Problem 2: Empty Recommendations**
```
{"recommendations": [], "total": 0}
```
**Solution:**
- Check MongoDB có data không
- Verify model đã train chưa
- Check user_id có trong training data không

### **Problem 3: Slow Response**
```
Response time > 2 seconds
```
**Solution:**
- Enable Redis caching
- Optimize MongoDB indexes
- Use CDN for API

---

## 📚 RESOURCES

- **API Documentation:** http://localhost:8000/docs
- **Code Examples:** `examples/` folder
- **Training Guide:** `SYSTEM_EXPLANATION.md`
- **Support:** Create GitHub issue

---

🎉 **Chúc bạn tích hợp thành công!**
