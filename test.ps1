# Health check
Invoke-RestMethod -Uri "https://yes-app.dqlb47.easypanel.host/health"

# Create mailboxes test
$body = @{
    domain = "test.com"
    sender_name = "John Doe" 
    password = "TestPass123!"
    variations = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://yes-app.dqlb47.easypanel.host/create-mailboxes" -Method POST -Body $body -ContentType "application/json"