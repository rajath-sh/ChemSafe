
import requests

res = requests.get('http://127.0.0.1:8000/api/users', headers={'X-Dev-Role': 'admin'})
users = res.json()
uu_user = next((u for u in users if u['email'] == 'u@gmail.com'), None)
print('uu user:', uu_user)

res = requests.get('http://127.0.0.1:8000/api/incidents', headers={'X-Dev-Role': 'admin', 'X-Dev-User-Id': 'USR-bd4023ae5dd84f81'})
incidents = res.json()
open_incident = next((i for i in incidents if i['status'] != 'resolved'), None)
if not open_incident:
    res = requests.post('http://127.0.0.1:8000/api/incidents', json={'lab_id': 'LAB-1', 'title': 'Test 2', 'severity': 'high', 'description': 'desc'}, headers={'X-Dev-Role': 'admin', 'X-Dev-User-Id': 'USR-bd4023ae5dd84f81'})
    open_incident = res.json()

print('Assigning incident:', open_incident['incident_id'])
res = requests.patch('http://127.0.0.1:8000/api/incidents/' + open_incident['incident_id'], json={'assigned_staff_id': uu_user['user_id']}, headers={'X-Dev-Role': 'admin', 'X-Dev-User-Id': 'USR-bd4023ae5dd84f81'})
print('Patch status:', res.status_code)

res = requests.get('http://127.0.0.1:8000/api/notifications?unread_only=false', headers={'X-Dev-Role': uu_user['role'], 'X-Dev-User-Id': uu_user['user_id']})
print('Notifications:', res.json())

