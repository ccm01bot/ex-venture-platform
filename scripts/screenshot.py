#!/usr/bin/env python3
import sys, json, base64, urllib.request
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

resp = urllib.request.urlopen("http://127.0.0.1:9222/json")
tabs = json.loads(resp.read())
for tab in tabs:
    if "notebooklm.google.com/notebook" in tab.get("url", ""):
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"])
        ws.send(json.dumps({"id":1,"method":"Page.captureScreenshot","params":{"format":"png"}}))
        r = json.loads(ws.recv())
        data = r.get("result",{}).get("data","")
        if data:
            with open("/tmp/morningbrief/live_screenshot.png","wb") as f:
                f.write(base64.b64decode(data))
            print("Screenshot saved")
        ws.close()
        break
