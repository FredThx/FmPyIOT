import time, network

ssid = 'WIFI_THOME2'
password = '***REMOVED***'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)


max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print(f'waiting for connection... status = {wlan.status()}')
    time.sleep(1)
# Handle connection error
if wlan.status() != 3:
    raise RuntimeError(f'network connection failed, status= {wlan.status()}')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )