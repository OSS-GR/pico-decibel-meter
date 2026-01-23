import os
from secret import SSID_NAME, PASSWORD

def do_connect():
    import machine, network, time
    led = machine.Pin("LED", machine.Pin.OUT, value=0)
    wlan = network.WLAN()
    wlan.active(True)

    if not wlan.isconnected():
        print('connecting to network...')
        start = time.ticks_ms()
        wlan.connect(SSID_NAME, PASSWORD)
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 10000:
                raise TimeoutError("Timed out waiting to connect to Wi-Fi")
            led.on()
            time.sleep(0.2)
            led.off()
            machine.idle()
    
    led.on()
    time.sleep(1)
    led.off()
    print('network config:', wlan.ipconfig('addr4'))


if __name__ == "__main__":
    try:
        do_connect()
    except Exception as e:
        import sys
        print("Error while connecting to Wi-Fi:")
        sys.print_exception(e)