# 🚨 LỖI: MongoDB Chưa Chạy

## Nguyên nhân:
Server FastAPI cần kết nối MongoDB để start, nhưng MongoDB chưa được cài đặt hoặc chưa chạy.

```
Error: localhost:27017: [WinError 10061] 
No connection could be made because the target machine actively refused it
```

---

## ✅ GIẢI PHÁP

### Option 1: Cài MongoDB Community (Local) - Khuyến nghị cho Dev

#### Bước 1: Download MongoDB
```
https://www.mongodb.com/try/download/community
```
- Chọn **Windows**
- Version: **7.0** (latest)
- Package: **MSI**

#### Bước 2: Cài đặt
1. Chạy file .msi vừa download
2. Chọn **Complete**
3. ✅ Tick **"Install MongoDB as a Service"**
4. ✅ Tick **"Install MongoDB Compass"** (GUI tool)
5. Click **Install**

#### Bước 3: Start MongoDB
```powershell
# Start MongoDB service
net start MongoDB

# Verify đang chạy
Get-Service MongoDB
```

#### Bước 4: Start lại FastAPI Server
```powershell
python -m uvicorn main:app --reload --port 8000
```

---

### Option 2: MongoDB Atlas (Cloud) - Free Tier

Nếu không muốn cài local, dùng cloud:

#### Bước 1: Tạo account
1. Đăng ký miễn phí: https://www.mongodb.com/cloud/atlas/register
2. Chọn **FREE** tier (M0)
3. Chọn region gần bạn (Singapore recommended)

#### Bước 2: Create Cluster
1. Click **"Build a Database"**
2. Chọn **FREE (M0)**
3. Chọn Provider: **AWS** hoặc **Google Cloud**
4. Chọn Region: **Singapore (ap-southeast-1)**
5. Cluster Name: `Recommend`
6. Click **Create**

#### Bước 3: Setup Database Access
1. **Database Access** → **Add New Database User**
   - Username: `admin`
   - Password: `Admin123!` (hoặc generate)
   - Role: **Atlas Admin**
   - Click **Add User**

2. **Network Access** → **Add IP Address**
   - Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - Click **Confirm**

#### Bước 4: Get Connection String
1. Click **Connect** trên cluster
2. Chọn **"Connect your application"**
3. Driver: **Python**
4. Copy connection string, ví dụ:
```
mongodb+srv://admin:<password>@recommend.xxxxx.mongodb.net/
```

#### Bước 5: Update .env
Mở file `.env`, thay đổi:
```env
# Từ:
MONGODB_URL=mongodb://localhost:27017

# Thành (thay <password> bằng password thật):
MONGODB_URL=mongodb+srv://admin:Admin123!@recommend.xxxxx.mongodb.net/
MONGODB_DB_NAME=recommend_experiences
```

#### Bước 6: Start Server
```powershell
python -m uvicorn main:app --reload --port 8000
```

---

## 🔍 Verify MongoDB Đang Chạy

### Local MongoDB:
```powershell
# Check service
Get-Service MongoDB

# Connect với mongosh
mongosh

# Hoặc dùng MongoDB Compass
```

### MongoDB Atlas:
- Vào Atlas Dashboard
- Cluster phải có status **"ACTIVE"**
- Màu xanh là đang chạy

---

## 🎯 Sau Khi MongoDB Chạy

Server sẽ start thành công:
```
✓ Connected to MongoDB: localhost:27017
✓ Connected to Redis: localhost:6379 (optional)
✓ Application started successfully
INFO: Uvicorn running on http://127.0.0.1:8000
```

Test API:
```
http://localhost:8000/docs
http://localhost:8000/api/recommendations/test
```

---

## 💡 TIPS

### Nếu dùng MongoDB Local:
- MongoDB Compass rất hữu ích để xem data
- Start MongoDB cùng Windows: `sc config MongoDB start=auto`

### Nếu dùng MongoDB Atlas:
- Miễn phí 512MB storage
- Tự động backup
- Không cần bảo trì
- Có thể share với team dễ dàng

---

## 🐛 Lỗi Thường Gặp

### 1. "Service MongoDB not found"
→ MongoDB chưa cài hoặc chưa được install as service
→ Reinstall MongoDB và tick "Install as Service"

### 2. "Authentication failed" (Atlas)
→ Check username/password đúng chưa
→ Check IP whitelist (0.0.0.0/0)

### 3. "Network timeout" (Atlas)
→ Check internet connection
→ Firewall có block không

---

**🎊 Sau khi MongoDB chạy, server sẽ start ngay!**

Chọn Option 1 (Local) nếu bạn:
- Đang dev local
- Muốn full control
- Có data lớn

Chọn Option 2 (Atlas) nếu bạn:
- Muốn test nhanh
- Không muốn cài thêm software
- Làm việc trên nhiều máy
