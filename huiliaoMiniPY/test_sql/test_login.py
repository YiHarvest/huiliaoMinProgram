import urllib.request
import json
import traceback

try:
    req = urllib.request.Request(
        'http://127.0.0.1:3161/api/wxapp/login',
        data=json.dumps({'code': 'test_code'}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    resp = urllib.request.urlopen(req, timeout=30)
    print('Status:', resp.status)
    print('Response:', resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    print('Response:', e.read().decode())
except Exception as e:
    print('Error:', type(e).__name__, str(e))
    traceback.print_exc()