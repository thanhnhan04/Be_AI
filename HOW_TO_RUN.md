# 🚀 CÁCH CHẠY DỰ ÁN

## ✅ Server đã chạy thành công!

```
🌐 Server: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
📖 ReDoc: http://localhost:8000/redoc
```

---

## 📋 QUICK START

### 1. Test API (không cần auth):
```bash
# Test recommendations
curl http://localhost:8000/api/recommendations/test

# Hoặc mở browser:
http://localhost:8000/api/recommendations/test
```

### 2. Xem API Documentation:
```
http://localhost:8000/docs
```

### 3. Test với user cụ thể:
```bash
curl "http://localhost:8000/api/recommendations/test?user_id=abc123&top_k=5"
```

---

## 🔐 FLOW ĐẦY ĐỦ (VỚI AUTH)

### Step 1: Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!",
    "full_name": "Test User"
  }'
```

### Step 2: Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!"
  }'
```

Nhận được `access_token`, copy nó!

### Step 3: Create Interaction
```bash
curl -X POST http://localhost:8000/api/interactions \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "experience_id": "507f1f77bcf86cd799439011",
    "interaction_type": "wishlist",
    "rating": 4.5
  }'
```

### Step 4: Get Recommendations
```bash
curl http://localhost:8000/api/recommendations \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🎯 CÁC ENDPOINTS CHÍNH

### 🔐 Authentication
- `POST /api/auth/register` - Đăng ký
- `POST /api/auth/login` - Login

### 📊 Interactions
- `POST /api/interactions` - Tạo interaction
- `GET /api/interactions` - Xem interactions

### 🎁 Recommendations
- `GET /api/recommendations` - Personalized (cần auth)
- `GET /api/recommendations/test` - Test (không cần auth) ✅
- `GET /api/recommendations/similar/{id}` - Similar experiences

### 🏋️ Training
- `POST /api/training/preprocess` - Preprocessing
- `POST /api/training/train` - Train model
- `POST /api/training/full-pipeline` - Full pipeline
- `GET /api/training/status` - Training status
- `GET /api/training/metrics` - Model metrics

---

## 📁 COLLECTION NAMES

Hiện tại code đang dùng:
- **Experiences**: `businesses` collection
- **Interactions**: `interactions` collection

Nếu MongoDB của bạn dùng tên khác, update trong:
`services/recommendation_service.py` (dòng 24-25)

---

## 🐛 LỖI THƯỜNG GẶP

### 1. MongoDB connection failed
```bash
# Start MongoDB
net start MongoDB
```

### 2. Redis connection failed
Redis là optional, bỏ qua cảnh báo này OK.

### 3. Model not found
```bash
# Check model files
ls models/

# Nếu không có:
python scripts/train_als_model.py
```

### 4. Collection not found
Update collection names trong `services/recommendation_service.py`

---

## 🎉 TEST NHANH

### Option 1: Browser
```
http://localhost:8000/docs
```
Dùng Swagger UI để test trực tiếp!

### Option 2: PowerShell
```powershell
# Test recommendations
Invoke-WebRequest -Uri "http://localhost:8000/api/recommendations/test?top_k=5" | Select-Object -ExpandProperty Content

# Test health
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content
```

### Option 3: Python
```python
import requests

# Test recommendations
response = requests.get('http://localhost:8000/api/recommendations/test', params={'top_k': 5})
print(response.json())
```

---

## 📊 MODEL HIỆN TẠI

Bạn đã có model trained:
- **File**: `models/als_model.pkl` (4.95 MB)
- **Encoders**: `models/encoders_als.pkl` (309 KB)
- **Performance**: Hit Rate@10 = 34.60%
- **Users**: 2,519
- **Items**: 9,862

---

## 🔄 ĐỂ TRAIN LẠI MODEL

```bash
# 1. Preprocessing (MongoDB → CSV)
curl -X POST http://localhost:8000/api/training/preprocess

# 2. Train model
curl -X POST http://localhost:8000/api/training/train

# Hoặc full pipeline:
curl -X POST http://localhost:8000/api/training/full-pipeline

# Check status:
curl http://localhost:8000/api/training/status
```

---

## ✨ NEXT STEPS

1. ✅ Server đang chạy
2. ✅ Test endpoint: http://localhost:8000/api/recommendations/test
3. 🔜 Integrate với React frontend
4. 🔜 Add more data
5. 🔜 Retrain model định kỳ

---

**🎊 Chúc mừng! Dự án đã chạy thành công!**
