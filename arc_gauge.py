"""
Arc Gauge Framebuffer Renderer for Volume Meter
Provides efficient semi-circular gauge rendering using MicroPython framebuf
"""
import framebuf
import math


class ArcGauge:
    """
    Renders a filled semi-circular arc gauge to a framebuffer.
    Efficiently fills the arc horizontally based on a percentage value.
    """

    def __init__(self, width, height, center_x, center_y,
                 outer_radius, inner_radius=None,
                 start_angle=180, end_angle=0):
        """
        Initialize the arc gauge framebuffer.

        Args:
            width: Framebuffer width in pixels
            height: Framebuffer height in pixels
            center_x: X coordinate of arc center
            center_y: Y coordinate of arc center
            outer_radius: Outer radius of the arc ring
            inner_radius: Inner radius (if None, uses outer_radius - 8)
            start_angle: Starting angle in degrees (default 180 = left)
            end_angle: Ending angle in degrees (default 0 = right)
        """
        self.width = width
        self.height = height
        self.center_x = center_x
        self.center_y = center_y
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius if inner_radius else outer_radius - 8
        self.start_angle = start_angle
        self.end_angle = end_angle

        # Create framebuffer in RGB565 format (16-bit color)
        self.buffer = bytearray(width * height * 2)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.RGB565)

    def _angle_to_radians(self, angle):
        """Convert degrees to radians"""
        return (angle * math.pi) / 180.0

    def _point_in_arc(self, x, y, fill_angle):
        """
        Check if a point is within the arc and should be filled.

        Args:
            x, y: Pixel coordinates
            fill_angle: Maximum angle to fill (0-180 for semi-circle)

        Returns:
            True if point should be filled
        """
        # Calculate distance from center
        dx = x - self.center_x
        dy = y - self.center_y
        dist_sq = dx * dx + dy * dy

        # Check if within radius bounds
        inner_sq = self.inner_radius * self.inner_radius
        outer_sq = self.outer_radius * self.outer_radius

        if not (inner_sq <= dist_sq <= outer_sq):
            return False

        # Calculate angle from center (range: -180 to 180)
        angle = math.atan2(dy, dx) * 180.0 / math.pi

        # Check if angle is in top semicircle (180° left, through -90° top, to 0° right)
        if angle >= 180 or angle <= 0:
            # Convert to arc_angle (0 at 180°, 180 at 0°)
            arc_angle = (angle - 180) % 360
            # Check if within fill range
            if arc_angle <= fill_angle:
                return True

        return False

    def draw_filled_arc(self, fill_percent, color):
        """
        Draw a filled arc at the given percentage.

        Args:
            fill_percent: Fill percentage (0.0 to 1.0)
            color: Color in RGB565 format
        """
        # Clear framebuffer first (transparent - black for now)
        self.fb.fill(0x0000)

        # Calculate fill angle (0-180 for semi-circle)
        fill_angle = fill_percent * 180.0

        # Iterate through all pixels in the bounding box
        min_x = max(0, self.center_x - self.outer_radius)
        max_x = min(self.width, self.center_x + self.outer_radius + 1)
        min_y = max(0, self.center_y - self.outer_radius)
        max_y = min(self.height, self.center_y + self.outer_radius + 1)

        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if self._point_in_arc(x, y, fill_angle):
                    self.fb.pixel(x, y, color)

    def draw_arc_outline(self, color, thickness=2):
        """
        Draw just the arc outline (no fill).

        Args:
            color: Color in RGB565 format
            thickness: Line thickness in pixels
        """
        self.fb.fill(0x0000)

        # Draw outer and inner arc edges
        for t in range(thickness):
            r_outer = self.outer_radius - t
            r_inner = self.inner_radius + t

            # Draw semi-circle arcs (180 to 360 degrees = left to right)
            steps = max(r_outer, r_inner) * 2
            for i in range(steps):
                angle = 180 + (180 * i / steps)  # 180° to 360°
                rad = self._angle_to_radians(angle)

                # Outer arc
                x_outer = int(self.center_x + r_outer * math.cos(rad))
                y_outer = int(self.center_y + r_outer * math.sin(rad))
                if 0 <= x_outer < self.width and 0 <= y_outer < self.height:
                    self.fb.pixel(x_outer, y_outer, color)

                # Inner arc
                x_inner = int(self.center_x + r_inner * math.cos(rad))
                y_inner = int(self.center_y + r_inner * math.sin(rad))
                if 0 <= x_inner < self.width and 0 <= y_inner < self.height:
                    self.fb.pixel(x_inner, y_inner, color)

    def get_buffer(self):
        """Return the framebuffer for blitting to display"""
        return self.fb

    def get_buffer_data(self):
        """Return raw buffer data"""
        return self.buffer


class ArcGaugeRenderer:
    """
    High-level arc gauge renderer that integrates with LCD display.
    Handles color conversion and display updates.
    """

    def __init__(self, lcd, width=160, height=100,
                 center_x=80, center_y=50,
                 outer_radius=45, inner_radius=35):
        """
        Initialize the arc gauge renderer.

        Args:
            lcd: LCD display object with color definitions
            width: Gauge framebuffer width
            height: Gauge framebuffer height
            center_x: Center X of the arc
            center_y: Center Y of the arc
            outer_radius: Outer radius of arc ring
            inner_radius: Inner radius of arc ring
        """
        self.lcd = lcd
        self.arc = ArcGauge(width, height, center_x, center_y,
                           outer_radius, inner_radius)
        self.display_x = 0
        self.display_y = 0
        self.width = width
        self.height = height

    def set_display_position(self, x, y):
        """Set where to display the gauge on the LCD"""
        self.display_x = x
        self.display_y = y

    def _rgb888_to_rgb565(self, r, g, b):
        """Convert RGB888 to RGB565 format"""
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F
        b5 = (b >> 3) & 0x1F
        return (r5 << 11) | (g6 << 5) | b5

    def _lcd_color_to_rgb565(self, lcd_color):
        """
        Convert LCD color (usually 16-bit) to framebuffer RGB565.
        Assumes LCD colors are already in RGB565 format.
        """
        return lcd_color

    def render(self, fill_percent, color):
        """
        Render the gauge at the specified fill percentage.

        Args:
            fill_percent: Fill percentage (0.0 to 1.0)
            color: Color object or 16-bit RGB565 value
        """
        # Convert color if needed
        if hasattr(color, '__iter__'):  # RGB tuple
            rgb565_color = self._rgb888_to_rgb565(color[0], color[1], color[2])
        else:
            rgb565_color = self._lcd_color_to_rgb565(color)

        # Draw the filled arc
        self.arc.draw_filled_arc(fill_percent, rgb565_color)

        # Blit to display (if LCD supports direct framebuffer blitting)
        # Otherwise, pixel data can be accessed and drawn manually
        return self.arc.get_buffer_data()

    def blit_to_lcd(self, fill_percent, color):
        """
        Render and display the gauge on the LCD.

        Args:
            fill_percent: Fill percentage (0.0 to 1.0)
            color: Color for the arc fill
        """
        # Render to framebuffer
        buffer_data = self.render(fill_percent, color)

        # Manually copy pixels to LCD (for compatibility with various LCD drivers)
        # This is more portable than assuming a specific blit function
        self._draw_buffer_to_lcd(buffer_data)

    def _draw_buffer_to_lcd(self, buffer_data):
        """
        Draw the framebuffer contents to the LCD display.
        Iterates through framebuffer and draws each pixel.
        """
        for y in range(self.height):
            for x in range(self.width):
                # Get pixel from RGB565 framebuffer (2 bytes per pixel)
                idx = (y * self.width + x) * 2
                if idx + 1 < len(buffer_data):
                    # Extract RGB565 value (little-endian)
                    rgb565 = buffer_data[idx] | (buffer_data[idx + 1] << 8)

                    # Skip black pixels (transparent/background)
                    if rgb565 != 0x0000:
                        # Draw pixel on LCD at display position
                        px = self.display_x + x
                        py = self.display_y + y
                        self.lcd.pixel(px, py, rgb565)
