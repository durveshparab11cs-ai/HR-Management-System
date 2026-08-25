import urllib.request, json, sys, time
time.sleep(1)
try:
    r = urllib.request.urlopen('http://localhost:8000/coordinator/api/get-gps', timeout=5, data=b'{}')
    j = json.loads(r.read())
    print("SUCCESS" if j.get('success') else "FAIL")
    print(json.dumps(j))
except Exception as e:
    print(f"ERROR: {e}")
