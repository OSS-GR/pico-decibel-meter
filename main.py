from machine import Timer
import time
import random
from dbmeter import DBMeter
from lcd import LCD_1inch69
from touch import Touch_CST816D

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

        # Initialize arc gauge renderer
        # Dimensions: 160x100 framebuffer, center at (80, 50)
        # outer_radius: 45px, inner_radius: 35px (creates 10px thick arc)
        self.arc_gauge = ArcGaugeRenderer(
            lcd,
            width=160,
            height=100,
            center_x=80,
            center_y=50,
            outer_radius=45,
            inner_radius=35
        )
        # Position gauge on display (centered horizontally)
        self.arc_gauge.set_display_position(
            (lcd.width - 160) // 2,  # Center horizontally
            90  # Y position below title
        )
        
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
    
    def draw(self):
        """Draw the volume meter UI"""
        # Clear screen with white background
        self.lcd.fill(self.lcd.white)
        
        # Title
        self.lcd.write_text('Volume Level',25, 20, 2, self.lcd.black)
        
        # Calculate bar dimensions
        bar_width = 200
        bar_height = 30
        bar_x = 20
        bar_y = 120
        
        # Calculate fill amount based on current dB
        db_range = self.max_db - self.min_db
        fill_percent = (self.current_db - self.min_db) / db_range
        fill_width = int(bar_width * fill_percent)
        
        # Get color for current level
        bar_color = self.get_color_for_db(self.current_db)
        
        
        # self.lcd.rect(bar_x, bar_y, bar_width, bar_height, self.lcd.black)
        
        # Draw filled portion
        if fill_width > 0:
            # Draw background bar (outline)
            self.lcd.ellipse(round(self.lcd.width/2),bar_y, round(bar_width/2), round(bar_width/3), self.lcd.green, True, 3)
            self.lcd.ellipse(round(self.lcd.width/2),bar_y+40, round(bar_width/2)-20, round(bar_width/3), self.lcd.white, True, 3)
            # self.lcd.fill_rect(10, 55, fill_width, 75, self.lcd.black)
            # self.lcd.fill_rect(bar_x, bar_y, fill_width, bar_height, bar_color)

        
        # Draw dB value as large text
        db_text = str(int(self.current_db))
        self.lcd.write_text(db_text, 80, 180, 5, bar_color)
        
        # Draw "dB" label
        self.lcd.write_text('dB', 170, 195, 3, self.lcd.black)
        
        # Draw min/max range indicators
        self.lcd.write_text(str(self.min_db), bar_x, bar_y + bar_height + 5, 2, self.lcd.black)
        self.lcd.write_text(str(self.max_db), bar_width - 20 - bar_x, bar_y + bar_height + 5, 2, self.lcd.black)
        
        # Update display
        self.lcd.show()


#Mock Data Generator  模拟数据生成器
# class MockVolumeGenerator:
#     def __init__(self, min_db=30, max_db=100):
#         """
#         Generate realistic mock decibel data
        
#         Args:
#             min_db: Minimum dB value to generate
#             max_db: Maximum dB value to generate
#         """
#         self.min_db = min_db
#         self.max_db = max_db
#         self.current_db = 55
#         self.trend = 1  # 1 for increasing, -1 for decreasing
        
#     def get_next_value(self):
#         """Generate next mock dB value with realistic variation"""
#         # Small random walk for smooth transitions
#         change = random.randint(-3, 3)
#         self.current_db += change
        
#         # Ensure within bounds
#         if self.current_db >= self.max_db:
#             self.current_db = self.max_db
#             self.trend = -1
#         elif self.current_db <= self.min_db:
#             self.current_db = self.min_db
#             self.trend = 1
        
#         return self.current_db
  
if __name__=='__main__':
    
    LCD = LCD_1inch69()
    LCD.set_bl_pwm(65535)

    # Initialize volume meter UI
    meter = VolumeMeter(LCD, min_db=0, max_db=100)
    # generator = MockVolumeGenerator(min_db=20, max_db=100)
    db_meter = DBMeter()
    
    # Timer callback to update mock data
    def update_meter(timer):
        db_value = db_meter.get_current_db()
        meter.update_decibel(db_value)
    
    # Create timer that triggers every 500ms (0.5 seconds)
    timer = Timer()
    timer.init(period=500, mode=Timer.PERIODIC, callback=update_meter)
    
    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        timer.deinit()
        # LCD.fill(LCD.white)
        # LCD.show()
        timer.init(period=500, mode=Timer.PERIODIC, callback=update_meter)