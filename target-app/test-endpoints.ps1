# Target Application 接口测试脚本

$baseUrl = "http://localhost:8080"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Target Application - Endpoint Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 测试正常接口
Write-Host "[1] Testing Normal Endpoint..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$baseUrl/api/normal" -Method Get
Write-Host "Status: $($response.status)" -ForegroundColor Green
Write-Host ""

# 2. 查看问题开关状态
Write-Host "[2] Checking Problem Switches..." -ForegroundColor Yellow
$switches = Invoke-RestMethod -Uri "$baseUrl/api/admin/problems/switches" -Method Get
$switches | ConvertTo-Json
Write-Host ""

# 3. 启用内存泄漏
Write-Host "[3] Enabling Memory Leak..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$baseUrl/api/admin/problems/switches/MEMORY_LEAK/enable" -Method Post
Write-Host "Memory leak enabled" -ForegroundColor Green
Write-Host ""

# 4. 触发内存泄漏（3次）
Write-Host "[4] Triggering Memory Leak (3 times)..." -ForegroundColor Yellow
for ($i = 1; $i -le 3; $i++) {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/leak/memory" -Method Get
    Write-Host "  Request $i - Cache Size: $($result.cacheSizeMB) MB, Used Memory: $($result.usedMemoryMB) MB"
    Start-Sleep -Seconds 1
}
Write-Host ""

# 5. 查看内存状态
Write-Host "[5] Checking Memory Status..." -ForegroundColor Yellow
$memStatus = Invoke-RestMethod -Uri "$baseUrl/api/leak/memory/status" -Method Get
$memStatus | ConvertTo-Json
Write-Host ""

# 6. 启用慢 SQL
Write-Host "[6] Enabling Slow SQL..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$baseUrl/api/admin/problems/switches/SLOW_SQL/enable" -Method Post
Write-Host "Slow SQL enabled" -ForegroundColor Green
Write-Host ""

# 7. 触发慢 SQL
Write-Host "[7] Triggering Slow SQL..." -ForegroundColor Yellow
$sqlResult = Invoke-RestMethod -Uri "$baseUrl/api/slow/sql" -Method Get
Write-Host "Duration: $($sqlResult.durationMs) ms, Users: $($sqlResult.userCount)" -ForegroundColor Green
Write-Host ""

# 8. 查看健康检查
Write-Host "[8] Checking Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/actuator/health" -Method Get
    $health | ConvertTo-Json
} catch {
    Write-Host "Health check failed (expected if multiple problems active)" -ForegroundColor Red
}
Write-Host ""

# 9. 重置内存泄漏
Write-Host "[9] Resetting Memory Leak..." -ForegroundColor Yellow
$resetResult = Invoke-RestMethod -Uri "$baseUrl/api/leak/memory/reset" -Method Post
Write-Host "Released: $($resetResult.releasedMB) MB" -ForegroundColor Green
Write-Host ""

# 10. 禁用所有问题
Write-Host "[10] Disabling All Problems..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "$baseUrl/api/admin/problems/switches/MEMORY_LEAK/disable" -Method Post | Out-Null
Invoke-RestMethod -Uri "$baseUrl/api/admin/problems/switches/SLOW_SQL/disable" -Method Post | Out-Null
Write-Host "All problems disabled" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
