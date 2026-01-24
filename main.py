import time
import random
from machine import Timer
from dbmeter import DBMeter
from lcd import LCD_1inch69
from touch import Touch_CST816D
from arc_gauge import ArcGaugeRenderer
from bar_gauge import BarGauge

#Pin definition  引脚定义
I2C_SDA = 6
I2C_SDL = 7
I2C_IRQ = 17
I2C_RST = 16

DC = 14
CS = 9
SCK = 10
MOSI = 11
MISO = 12
RST = 8

BL = 15


#Volume Meter UI  音量计UI
class VolumeMeter:
    def __init__(self, lcd: LCD_1inch69, min_db=0, max_db=100):
        """
        Initialize the volume meter UI

        Args:
            lcd: LCD_1inch69 display object
            min_db: Minimum decibel value for the scale
            max_db: Maximum decibel value for the scale
        """
        self.lcd = lcd
        self.min_db = min_db
        self.max_db = max_db
        self.current_db = 0

        # Initialize both gauge renderers
        # Arc gauge
        self.arc_gauge = ArcGaugeRenderer(
            lcd,
            width=130,
            height=100,
            center_x=80,
            center_y=50,
            outer_radius=60,
            inner_radius=30
        )
        self.arc_gauge.set_display_position(
            (lcd.width - 160) // 2,  # Center horizontally
            90  # Y position below title
        )

        # Bar gauge
        self.bar_gauge = BarGauge(
            lcd,
            bar_width=200,
            bar_height=30,
            x=20,
            y=120
        )

        # Mode tracking: True = arc, False = bar
        self.use_arc_mode = False
        
    def get_color_for_db(self, db_value):
        """
        Return color based on dB level
        Green (quiet): 30-60 dB
        Yellow (normal): 60-80 dB
        Red (loud): 80+ dB
        """
        if db_value < 60:
            return self.lcd.green
        elif db_value < 80:
            return self.lcd.yellow
        else:
            return self.lcd.red
    
    def update_decibel(self, db_value):
        """Update the current decibel value"""
        self.current_db = db_value
        self.draw()

    def toggle_mode(self):
        """Toggle between bar and arc gauge modes"""
        self.use_arc_mode = not self.use_arc_mode
        mode_name = "Arc" if self.use_arc_mode else "Bar"
        print(f"Switched to {mode_name} mode")
    
    def draw(self):
        """Draw the volume meter UI"""
        # Clear screen with white background
        self.lcd.fill(self.lcd.white)

        # Title
        self.lcd.write_text('Volume Level', 25, 20, 2, self.lcd.black)

        # Calculate fill percentage based on current dB
        db_range = self.max_db - self.min_db
        fill_percent = (self.current_db - self.min_db) / db_range
        # Clamp to 0-1 range
        fill_percent = max(0.0, min(1.0, fill_percent))

        # Get color for current level
        bar_color = self.get_color_for_db(self.current_db)

        # Render appropriate gauge based on mode
        if self.use_arc_mode:
            self.arc_gauge.blit_to_lcd(fill_percent, bar_color)
        else:
            self.bar_gauge.draw(fill_percent, bar_color)

        # Draw dB value as large text (centered below gauge)
        db_text = str(int(self.current_db))
        self.lcd.write_text(db_text, 80, 180, 5, bar_color)

        # Draw "dB" label
        self.lcd.write_text('dB', 170, 195, 3, self.lcd.black)

        # Draw min/max range indicators
        if self.use_arc_mode:
            self.lcd.write_text(str(self.min_db), 20, 130, 2, self.lcd.black)
            self.lcd.write_text(str(self.max_db), 230, 130, 2, self.lcd.black)
        else:
            self.lcd.write_text(str(self.min_db), 20, 155, 2, self.lcd.black)
            self.lcd.write_text(str(self.max_db), 220, 155, 2, self.lcd.black)

        # Update display
        self.lcd.show()

  
if __name__=='__main__':
    
    print("Starting Volume Meter...")
    LCD = None
    meter = None
    db_meter = None

    try:
        LCD = LCD_1inch69()
        LCD.set_bl_pwm(65535)
        print("LCD initialized")
    except Exception as e:
        print(f"LCD init failed: {e}")

    if LCD:
        try:
            # Initialize volume meter UI
            meter = VolumeMeter(LCD, min_db=0, max_db=100)
            print("Volume Meter initialized")
        except Exception as e:
            print(f"VolumeMeter init failed: {e}")

    try:
        db_meter = DBMeter()
        print("DBMeter initialized")
    except Exception as e:
        print(f"DBMeter init failed: {e}")

    # Initialize touch controller (gesture mode)
    touch = None
    try:
        print("Initializing touch...")
        touch = Touch_CST816D()
        print("Touch created")
        touch.Set_Mode(0)  # 0 = gesture mode
        print("Touch controller initialized")
    except Exception as e:
        print(f"Touch init failed: {e}")
        print("Continuing without touch support")

    if not (meter and db_meter and LCD):
        print("ERROR: Failed to initialize required components")
        import sys
        sys.exit()

    # Timer callback to update meter
    def update_meter(timer):
        start = time.ticks_ms()
        sound_level = db_meter.read_sound_level()
        meter.update_decibel(sound_level)
        elapsed = time.ticks_ms() - start
        if elapsed > 100:
            print(f"Update took {elapsed}ms")

    # Create timer that triggers every 500ms (0.5 seconds)
    timer = Timer(-1)
    timer.init(period=500, mode=Timer.PERIODIC, callback=update_meter)
    print("Starting main loop...")

    # Keep the program running
    try:
        while True:
            # Check for long press gesture (0x0C)
            if touch and touch.Gestures == 0x0C:
                meter.toggle_mode()
                touch.Gestures = 0x00  # Reset gesture after handling
                time.sleep(0.5)  # Debounce delay
            time.sleep(0.1)
    except KeyboardInterrupt:
        timer.deinit()
        LCD.fill(LCD.white)
        LCD.write_text(text="STOP",x=0,y=60,size=5,color=LCD.red)
        LCD.show()
        print("Keyboard Interrupt")
    except Exception as e:
        timer.deinit()
        LCD.fill(LCD.white)
        LCD.write_text(text="FAIL",x=0,y=60,size=5,color=LCD.red)
        LCD.show()
        print(f"Exception: {e}")