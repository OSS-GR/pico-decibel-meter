import machine
import utime
import urequests
import sys
import ujson

class DBMeter():

###############################################
    # Constants 
    # I2C address
    PCBARTISTS_DBM = 0x48

    # Registers
    I2C_REG_VERSION		= 0x00
    I2C_REG_ID3			= 0x01
    I2C_REG_ID2			= 0x02
    I2C_REG_ID1			= 0x03
    I2C_REG_ID0			= 0x04
    I2C_REG_SCRATCH		= 0x05
    I2C_REG_CONTROL		= 0x06
    I2C_REG_TAVG_HIGH	= 0x07
    I2C_REG_TAVG_LOW	= 0x08
    I2C_REG_RESET		= 0x09
    I2C_REG_DECIBEL		= 0x0A
    I2C_REG_MIN			= 0x0B
    I2C_REG_MAX			= 0x0C
    I2C_REG_THR_MIN     = 0x0D
    I2C_REG_THR_MAX     = 0x0E
    I2C_REG_HISTORY_0	= 0x14
    I2C_REG_HISTORY_99	= 0x77

    # Notifications
    LAST_NOTIFICATION = 0 # 
    NOTIFICATION_COOLDOWN = 90 # seconds

###############################################

    def __init__(self):
        # Initialize I2C with pins
        # Using I2C1 bus with GP2 (SDA) and GP3 (SCL)
        self.i2c = machine.I2C(1,
                        scl=machine.Pin(3),
                        sda=machine.Pin(2),
                        freq=100000)

    ###############################################
    # Functions

    def reg_write(self, addr, reg, data):
        """
        Write bytes to the specified register.
        """
        
        # Construct message
        msg = bytearray()
        msg.append(data)
        
        # Write out message to register
        self.i2c.writeto_mem(addr, reg, msg)
        
    def reg_read(self, addr, reg, nbytes=1):
        """
        Read byte(s) from specified register. If nbytes > 1, read from consecutive
        registers.
        """
        
        # Check to make sure caller is asking for 1 or more bytes
        if nbytes < 1:
            return bytearray()
        
        # Request data from specified register(s) over I2C
        data = self.i2c.readfrom_mem(addr, reg, nbytes)
        
        return data
    
    @property
    def current_decibel(self):
        """
        Read the current sound level in decibels (dB SPL) from the meter.

        :return: Current sound level as integer
        """
        try:
            data = self.reg_read(self.PCBARTISTS_DBM, self.I2C_REG_DECIBEL)
            self._decibel_value = int.from_bytes(data, "big")
            return self._decibel_value
        except Exception as e:
            print(f"DBMeter Error - Failed to read I2C register: {type(e).__name__}: {e}")
            return 0
        
    @property
    def notification_cooldown(self):
        """
        Docstring for notification_cooldown
        
        :param self: Description

        :return: Whether cooldown since last notification is over
        """
        time_since_last_cooldown = round( (utime.ticks_diff(utime.ticks_ms(),self.LAST_NOTIFICATION)) / 1000 ) # seconds
        print(time_since_last_cooldown)
        return time_since_last_cooldown > self.NOTIFICATION_COOLDOWN

    
    def notify(self,body = None, title = None):
        """
        data = f"You are being too loud: {self._decibel_value}db".encode("utf-8")
        headers = {
            "Title": "Shhhhhh....",
            "Priority": "urgent",
            "Tags": "warning,loudspeaker"
        }
        print("Alerting user of noise disturbance.")
        urequests.post("https://ntfy.oss.house/volume_alerts", data=data, headers=headers)
        """
        try:
            assert self.notification_cooldown, "Cooldown period is not over"
            response = urequests.post(
                url="http://ntfy.oss.house/push",
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                },
                data=ujson.dumps({
                    "body": body or f"You are being too loud: {self._decibel_value}db",
                    "device_key": "47ms9y4nmKRTkKodctcWdR",
                    "title": title or "Noise Alert",
                    # "sound": "minuet",
                    "badge": 1,
                    "icon": "https://cdn-icons-png.flaticon.com/512/1320/1320548.png", # Red Siren Light
                    "group": "noise-alert",
                    # "url": "https://mritd.com"
                })
            )
            self.LAST_NOTIFICATION = utime.ticks_ms()
            print('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            print('Response HTTP Response Body: {content}'.format(
                content=response.content))
        except OSError as e:
            print(f'HTTP Request failed: {e}')
        except AssertionError as e:
            print(f"Error: {e}")

###############################################
# Main
if __name__=="__main__":
    db_meter = DBMeter()

    # Read device ID to make sure that we can communicate with the ADXL343
    data = db_meter.reg_read(db_meter.PCBARTISTS_DBM, db_meter.I2C_REG_VERSION)
    print("dbMeter VERSION = 0x{:02x}".format(int.from_bytes(data, "big")))

    data = db_meter.reg_read(db_meter.PCBARTISTS_DBM, db_meter.I2C_REG_ID3, 4)
    print("Unique ID: 0x{:02x} ".format(int.from_bytes(data, "big")))

    db_meter.notify(body=f"Testing Meter {db_meter.current_decibel}db")
    
    utime.sleep(3)

    db_meter.notify(body=f"Testing Meter {db_meter.current_decibel}db")

    utime.sleep(7)

    db_meter.notify(body=f"Testing Meter {db_meter.current_decibel}db")

    while True:
        sound_level = db_meter.current_decibel
        print("Sound Level (dB SPL) = {:02d}".format(sound_level))
        utime.sleep (2)
    sys.exit()