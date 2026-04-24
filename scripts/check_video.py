#!/usr/bin/env python3
import sys, json, base64, urllib.request
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

resp = urllib.request.urlopen("http://127.0.0.1:9222/json")
tabs = json.loads(resp.read())
for tab in tabs:
    if "notebooklm.google.com/notebook" in tab.get("url", ""):
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"])
        # Reload the page
        ws.send(json.dumps({"id":1,"method":"Page.reload"}))
        ws.recv()
        import time; time.sleep(8)

        # Screenshot
        ws.send(json.dumps({"id":2,"method":"Page.captureScreenshot","params":{"format":"png"}}))
        r = json.loads(ws.recv())
        data = r.get("result",{}).get("data","")
        if data:
            with open("/tmp/morningbrief/live_refreshed.png","wb") as f:
                f.write(base64.b64decode(data))

        # Check Studio panel text
        ws.send(json.dumps({"id":3,"method":"Runtime.evaluate","params":{
            "expression": """(() => {
                const text = document.body.innerText;
                const studio = text.substring(text.indexOf('Studio'));
                return studio.substring(0, 500);
            })()""",
            "returnByValue": True
        }}))
        r = json.loads(ws.recv())
        val = r.get("result",{}).get("result",{}).get("value","")
        print("Studio panel text:")
        print(val)

        ws.close()
        break
