# TEST SCRIPT - Experience Recommendation System
# Chay: .\test_api.ps1

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  EXPERIENCE RECOMMENDATION SYSTEM - API TEST" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# 1. HEALTH CHECK
Write-Host ">> 1. Health Check" -ForegroundColor Yellow
try {
    $health = curl "$baseUrl/api/test/health" | ConvertFrom-Json
    Write-Host "  [OK] Status: $($health.status)" -ForegroundColor Green
    Write-Host "  [OK] Message: $($health.message)" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
    exit 1
}

# 2. POPULAR EXPERIENCES
Write-Host "`n>> 2. Get Popular Experiences (top 5)" -ForegroundColor Yellow
try {
    $popular = curl "$baseUrl/api/test/popular?top_k=5" | ConvertFrom-Json
    Write-Host "  [OK] Found: $($popular.total) experiences" -ForegroundColor Green
    
    $popular.experiences | ForEach-Object {
        Write-Host "    * $($_.name)" -ForegroundColor White
        Write-Host "      Location: $($_.city), $($_.state)" -ForegroundColor Gray
        Write-Host "      Rating: $($_.stars) stars ($($_.review_count) reviews)" -ForegroundColor Gray
    }
    
    # Luu ID de test
    $testExpId = $popular.experiences[0].id
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
}

# 3. CREATE INTERACTIONS
Write-Host "`n>> 3. Create User Interactions" -ForegroundColor Yellow
$testUserId = "test_user_$(Get-Random -Maximum 9999)"
Write-Host "  Test User ID: $testUserId" -ForegroundColor Cyan

try {
    # View interaction
    $body1 = @{
        user_id = $testUserId
        experience_id = $testExpId
        interaction_type = "view"
    } | ConvertTo-Json
    
    $int1 = Invoke-RestMethod -Uri "$baseUrl/api/test/interaction" -Method POST -Body $body1 -ContentType "application/json"
    Write-Host "  [OK] Created: view interaction" -ForegroundColor Green
    
    # Click interaction
    $body2 = @{
        user_id = $testUserId
        experience_id = $popular.experiences[1].id
        interaction_type = "click"
    } | ConvertTo-Json
    
    $int2 = Invoke-RestMethod -Uri "$baseUrl/api/test/interaction" -Method POST -Body $body2 -ContentType "application/json"
    Write-Host "  [OK] Created: click interaction" -ForegroundColor Green
    
    # Wishlist interaction
    $body3 = @{
        user_id = $testUserId
        experience_id = $popular.experiences[2].id
        interaction_type = "wishlist"
        rating = 5.0
    } | ConvertTo-Json
    
    $int3 = Invoke-RestMethod -Uri "$baseUrl/api/test/interaction" -Method POST -Body $body3 -ContentType "application/json"
    Write-Host "  [OK] Created: wishlist interaction with 5 star rating" -ForegroundColor Green
    
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
}

# 4. GET USER INTERACTIONS
Write-Host "`n>> 4. Get User Interactions" -ForegroundColor Yellow
try {
    $userInteractions = curl "$baseUrl/api/test/user/$testUserId/interactions" | ConvertFrom-Json
    Write-Host "  [OK] Total interactions: $($userInteractions.total)" -ForegroundColor Green
    
    $userInteractions.interactions | ForEach-Object {
        $ratingText = if ($_.rating) { " | Rating: $($_.rating) stars" } else { "" }
        Write-Host "    * $($_.interaction_type)$ratingText" -ForegroundColor White
        Write-Host "      Experience: $($_.experience_id)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
}

# 5. GET RECOMMENDATIONS
Write-Host "`n>> 5. Get Personalized Recommendations" -ForegroundColor Yellow
try {
    $recs = curl "$baseUrl/api/test/recommendations/$testUserId?top_k=10" | ConvertFrom-Json
    Write-Host "  [OK] Total recommendations: $($recs.total)" -ForegroundColor Green
    
    $recs.recommendations | Select-Object -First 5 | ForEach-Object {
        Write-Host "    * $($_.name)" -ForegroundColor White
        Write-Host "      $($_.city), $($_.state) | $($_.stars) stars ($($_.review_count) reviews)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
}

# 6. DELETE INTERACTION
Write-Host "`n>> 6. Delete Interaction" -ForegroundColor Yellow
try {
    $deleteResult = Invoke-RestMethod -Uri "$baseUrl/api/test/interaction/$testUserId/$testExpId" -Method DELETE
    Write-Host "  [OK] $($deleteResult.message)" -ForegroundColor Green
    
    # Verify deletion
    $afterDelete = curl "$baseUrl/api/test/user/$testUserId/interactions" | ConvertFrom-Json
    Write-Host "  [OK] Interactions after delete: $($afterDelete.total)" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Failed: $_" -ForegroundColor Red
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  TEST COMPLETED SUCCESSFULLY" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan
