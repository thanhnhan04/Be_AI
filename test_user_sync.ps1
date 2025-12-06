# Test User Sync API

$headers = @{
    "X-Sync-Secret" = "your-sync-secret-key-change-in-production"
    "Content-Type" = "application/json"
}

# 1. Create new user
Write-Host "`n========== TEST 1: CREATE USER ==========" -ForegroundColor Cyan
$body = @{
    user_id = "test_sync_user_001"
    email = "testsync@example.com"
    username = "testsync"
    full_name = "Test Sync User"
    preferences = @("Italian", "Asian", "Vegetarian")
    metadata = @{
        source = "test_script"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/sync/users" -Method Post -Headers $headers -Body $body
$response | ConvertTo-Json
Start-Sleep -Seconds 1

# 2. Update user (same user_id)
Write-Host "`n========== TEST 2: UPDATE USER ==========" -ForegroundColor Cyan
$body = @{
    user_id = "test_sync_user_001"
    email = "updated@example.com"
    preferences = @("Italian", "Asian", "Vegetarian", "Mexican")
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/sync/users" -Method Post -Headers $headers -Body $body
$response | ConvertTo-Json
Start-Sleep -Seconds 1

# 3. Get user
Write-Host "`n========== TEST 3: GET USER ==========" -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/sync/users/test_sync_user_001" -Method Get -Headers $headers
$response | ConvertTo-Json
Start-Sleep -Seconds 1

# 4. Verify in MongoDB
Write-Host "`n========== TEST 4: CHECK IN MONGODB ==========" -ForegroundColor Cyan
docker exec -it experience-recommendation-mongodb mongosh recommend_experiences --eval "db.users.findOne({user_id: 'test_sync_user_001'})"

# 5. Delete user
Write-Host "`n========== TEST 5: DELETE USER ==========" -ForegroundColor Yellow
$confirm = Read-Host "Delete test user? (y/n)"
if ($confirm -eq "y") {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/sync/users/test_sync_user_001" -Method Delete -Headers $headers
    $response | ConvertTo-Json
}

Write-Host "`n========== TESTS COMPLETED ==========" -ForegroundColor Green
