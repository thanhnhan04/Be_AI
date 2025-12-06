# Test script to verify auth_users and users collection separation

Write-Host "Testing Collection Separation..." -ForegroundColor Cyan

# Test 1: Register a new auth user
Write-Host "`n1. Registering new auth user..." -ForegroundColor Yellow
$registerBody = @{
    email = "test_auth@example.com"
    username = "test_auth_user"
    password = "test123456"
    full_name = "Test Auth User"
    preferences = @("Asian", "American")
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" `
    -Method POST `
    -Body $registerBody `
    -ContentType "application/json"

Write-Host "Registration Response:" -ForegroundColor Green
$registerResponse | ConvertTo-Json

# Test 2: Check auth_users collection count
Write-Host "`n2. Checking auth_users collection..." -ForegroundColor Yellow
docker exec -it experience-recommendation-mongodb mongosh recommend_experiences --eval "db.auth_users.countDocuments()"

# Test 3: Check auth_users collection has the new user
Write-Host "`n3. Finding user in auth_users..." -ForegroundColor Yellow
docker exec -it experience-recommendation-mongodb mongosh recommend_experiences --eval "db.auth_users.findOne({email: 'test_auth@example.com'})"

# Test 4: Sync a recommendation user (should go to users collection)
Write-Host "`n4. Syncing recommendation user..." -ForegroundColor Yellow
$syncBody = @{
    user_id = "TEST_RECOMMEND_USER_001"
    email = "test_recommend@example.com"
    username = "test_recommend"
    preferences = @("Asian", "Mexican")
} | ConvertTo-Json

$syncResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/sync/users" `
    -Method POST `
    -Body $syncBody `
    -ContentType "application/json" `
    -Headers @{ "X-Sync-Secret" = "your-sync-secret-key-change-in-production" }

Write-Host "Sync Response:" -ForegroundColor Green
$syncResponse | ConvertTo-Json

# Test 5: Check users collection count (should be 5491 now)
Write-Host "`n5. Checking users collection..." -ForegroundColor Yellow
docker exec -it experience-recommendation-mongodb mongosh recommend_experiences --eval "db.users.countDocuments()"

# Test 6: Verify the synced user in users collection
Write-Host "`n6. Finding synced user in users collection..." -ForegroundColor Yellow
docker exec -it experience-recommendation-mongodb mongosh recommend_experiences --eval "db.users.findOne({user_id: 'TEST_RECOMMEND_USER_001'})"

Write-Host "`nCollection Separation Test Complete!" -ForegroundColor Cyan
Write-Host "auth_users collection: For authentication (email/password)" -ForegroundColor Green
Write-Host "users collection: For recommendations (user_id from sync/Yelp)" -ForegroundColor Green
