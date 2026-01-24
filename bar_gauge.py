"""
Simple horizontal bar gauge renderer for volume meter
"""

class BarGauge:
    """
    Renders a simple horizontal filled bar gauge.
    """

    def __init__(self, lcd, bar_width=200, bar_height=30, x=20, y=120):
        """
        Initialize the bar gauge.

        Args:
            lcd: LCD display object
            bar_width: Width of the bar in pixels
            bar_height: Height of the bar in pixels
            x: X position of bar top-left
            y: Y position of bar top-left
        """
        self.lcd = lcd
        self.bar_width = bar_width
        self.bar_height = bar_height
        self.x = x
        self.y = y

    def draw(self, fill_percent, color):
        """
        Draw the filled bar.

        Args:
            fill_percent: Fill percentage (0.0 to 1.0)
            color: Color for the bar fill
        """
        # Draw background bar outline (empty rectangle)
        self.lcd.rect(self.x, self.y, self.bar_width, self.bar_height, self.lcd.black)

        # Calculate and draw filled portion
        fill_width = int(self.bar_width * fill_percent)
        if fill_width > 1:
            self.lcd.fill_rect(self.x + 1, self.y + 1, fill_width - 1, self.bar_height - 2, color)
