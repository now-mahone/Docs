# Test inbound email forwarding
import requests

key = 're_eS8p2qd5_H3siiEWh4dTkDcRiTag19Z9F'

# Check domain status
print("=== Domain Status ===")
r = requests.get('https://api.resend.com/domains', headers={'Authorization': f'Bearer {key}'})
d = r.json()['data'][0]
print(f"Domain: {d['name']}")
print(f"Receiving: {d['capabilities']['receiving']}")
print("Records:")
for rec in d['records']:
    print(f"  {rec['record']}: {rec['status']}")

# Send test email to devon@kerne.ai
print("\n=== Sending Test Email ===")
email_data = {
    "from": "Kerne Protocol <team@kerne.ai>",
    "to": ["devon@kerne.ai"],
    "subject": "Inbound Forward Test - 2026-02-19 7:06 PM MT",
    "html": "<h1>Test Email</h1><p>This tests inbound forwarding from devon@kerne.ai to liamlakevold@gmail.com</p><p>Timestamp: 2026-02-19 7:06 PM MT</p>"
}

r = requests.post('https://api.resend.com/emails', 
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json=email_data)

result = r.json()
print(f"Status: {r.status_code}")
print(f"Result: {result}")