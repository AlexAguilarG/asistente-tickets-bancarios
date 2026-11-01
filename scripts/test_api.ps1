param([string]$BaseUrl = "http://localhost:8080")
Invoke-RestMethod -Method Get -Uri "$BaseUrl/healthz"
Invoke-RestMethod -Method Get -Uri "$BaseUrl/readyz"
$body = @{ text = "Mi transferencia no llegó al destinatario" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/predict" -ContentType "application/json" -Body $body
