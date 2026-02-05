# Raspberry Pi Pico 2 Pin Configuration Guide

## Device Summary

| Device | Protocol | Address | I2C Bus | SDA Pin | SCL Pin | Status |
|--------|----------|---------|---------|---------|---------|--------|
| DBMeter (Decibel Sensor) | I2C | 0x48 | I2C1 | GP2 | GP3 | ✓ Active |
| Touch Sensor (CST816D) | I2C | 0x15 | I2C0 | GP4 | GP5 | ✓ Active |
| LCD Display (1.69") | SPI | N/A | N/A | N/A | N/A | ✓ Active |

---

## Pico 2 I2C Bus Options

The RP2350 (Pico 2) has **2 I2C buses** available, each can be assigned to different pin pairs:

### **I2C0 - Available Pin Pairs:**
- **Option 1:** GP0 (SDA) + GP1 (SCL)
- **Option 2:** GP4 (SDA) + GP5 (SCL) ← **CURRENTLY USED FOR TOUCH**
- **Option 3:** GP8 (SDA) + GP9 (SCL)
- **Option 4:** GP12 (SDA) + GP13 (SCL)
- **Option 5:** GP16 (SDA) + GP17 (SCL)
- **Option 6:** GP20 (SDA) + GP21 (SCL)

### **I2C1 - Available Pin Pairs:**
- **Option 1:** GP2 (SDA) + GP3 (SCL) ← **CURRENTLY USED FOR DBMETER**
- **Option 2:** GP6 (SDA) + GP7 (SCL)
- **Option 3:** GP10 (SDA) + GP11 (SCL)
- **Option 4:** GP14 (SDA) + GP15 (SCL)
- **Option 5:** GP18 (SDA) + GP19 (SCL)
- **Option 6:** GP22 (SDA) + GP23 (SCL)

---

## Original Website Suggestion & Problem

**Original Config (Website):**
```
TP_SDA    GP6    ← I2C1
TP_SCL    GP7    ← I2C1
DBMeter   GP2/GP3 ← I2C1
```

**Problem:** Both devices assigned to the **same I2C1 bus with different pin pairs**
- I2C buses can only use **ONE pin pair at a time** per bus
- You CANNOT use I2C1 with GP6/GP7 AND I2C1 with GP2/GP3 simultaneously
- This caused: `OSError: [Errno 5] EIO` (I/O error on I2C communication)

---

## Corrected Configuration

**Current Setup (Fixed):**
```
DBMeter Touch Sensor
├─ I2C1 Bus
│  ├─ SDA: GP2
│  ├─ SCL: GP3
│  └─ Address: 0x48
│
└─ I2C0 Bus
   ├─ SDA: GP4
   ├─ SCL: GP5
   └─ Address: 0x15
```

**Why this works:**
- Each device has its own I2C bus
- No pin conflicts
- I2C0 and I2C1 operate independently
- Both can run simultaneously at different speeds if needed

---

## Full GPIO Pin Allocation

### **SPI Pins (LCD Display) - SPI0**
| Pin | Function | Device |
|-----|----------|--------|
| GP11 | MOSI | LCD |
| GP10 | SCK | LCD |
| GP9 | CS | LCD |
| GP14 | DC (Data/Command) | LCD |
| GP8 | RST (Reset) | LCD |
| GP15 | BL (Backlight PWM) | LCD |

### **I2C Pins**
| Pin | Bus | Function | Device |
|-----|-----|----------|--------|
| GP2 | I2C1 | SDA | DBMeter |
| GP3 | I2C1 | SCL | DBMeter |
| GP4 | I2C0 | SDA | Touch Sensor |
| GP5 | I2C0 | SCL | Touch Sensor |

### **Interrupt & Reset Pins (Touch)**
| Pin | Function | Device |
|-----|----------|--------|
| GP16 | RST (Reset) | Touch Sensor |
| GP17 | IRQ (Interrupt) | Touch Sensor |

### **Power Pins**
| Pin | Function |
|-----|----------|
| 3.3V | Power (use one or multiple) |
| GND | Ground (use multiple for better distribution) |

---

## Recommended Physical Connection Setup

### **Option 1: Breadboard Power Distribution (Simplest)**
```
Pico 3.3V → Breadboard (+) rail → LCD VCC
                              ├─→ DBMeter VCC
                              └─→ Touch VCC

Pico GND  → Breadboard (-) rail → LCD GND
                              ├─→ DBMeter GND
                              └─→ Touch GND
```

### **Option 2: Direct from Multiple GND Pins (Recommended)**
```
Pico 3.3V  → Both LCD and DBMeter VCC
Pico GND#1 → LCD GND
Pico GND#2 → DBMeter GND
Pico GND#3 → Touch GND (via breadboard if needed)
```

The Pico 2 has 3 GND pins (positions 3, 8, 13, 18, 23, 28, 33, 38) - all internally connected.

---

## Code Configuration Files

### **dbmeter.py**
```python
self.i2c = machine.I2C(1,              # I2C1 bus
                        scl=machine.Pin(3),  # SCL on GP3
                        sda=machine.Pin(2),  # SDA on GP2
                        freq=100000)         # 100kHz
```

### **touch.py**
```python
self._bus = I2C(id=0,                  # I2C0 bus (changed from 1)
                scl=Pin(5),            # SCL on GP5
                sda=Pin(4),            # SDA on GP4
                freq=400_000)          # 400kHz
```

### **main.py Pin Definitions**
```python
# DBMeter: I2C1 on GP2/GP3
I2C_SDA = 2  # For reference/documentation
I2C_SCL = 3

# Touch: I2C0 on GP4/GP5 (defined in touch.py)
```

---

## Verification Checklist

- [x] DBMeter on I2C1 (GP2/GP3)
- [x] Touch Sensor on I2C0 (GP4/GP5)
- [x] No I2C bus conflicts
- [x] All pins are available (not used by other devices)
- [x] Power distribution from multiple GND pins recommended
- [x] I2C addresses don't conflict (0x48 vs 0x15)

---

## Why This Works

1. **Separate I2C Buses:** Each device has exclusive access to its bus
2. **Different Addresses:** Even if on same bus, different addresses (0x48 vs 0x15) prevent conflicts
3. **Proper GND Connection:** Multiple GND pins ensure good signal integrity
4. **Correct Pin Mapping:** All pins match the RP2350 datasheet

---

## Potential Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| OSError: [Errno 5] EIO | I2C bus conflict | Use separate I2C buses (current fix) |
| Touch sensor not responding | Wrong I2C bus/pins | Verify i2c_num=0 and pins 4/5 |
| DBMeter not responding | I2C1 on wrong pins | Verify pins 2/3 and i2c_num=1 |
| Intermittent errors | Loose GND connection | Use multiple GND pins, check breadboard |

---

**Last Updated:** 2026-01-24
**Configuration Status:** ✓ Correct - Ready to Deploy
