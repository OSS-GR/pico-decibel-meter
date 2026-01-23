from machine import Pin,I2C
import time


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

#Touch drive  触摸驱动
class Touch_CST816D(object):
    #Initialize the touch chip  初始化触摸芯片
    def __init__(self,address=0x15,mode=0,i2c_num=1,i2c_sda=I2C_SDA,i2c_scl=I2C_SDL,irq_pin=I2C_IRQ,rst_pin=I2C_RST,LCD=None):
        self._bus = I2C(id=i2c_num,scl=Pin(i2c_scl),sda=Pin(i2c_sda),freq=400_000) #Initialize I2C 初始化I2C
        self._address = address #Set slave address  设置从机地址
        self.int=Pin(irq_pin,Pin.IN, Pin.PULL_UP)         
        self.rst=Pin(rst_pin,Pin.OUT)
        self.Reset()
        bRet=self.WhoAmI()
        if bRet :
            print("Success:Detected CST816D.")
            Rev= self.Read_Revision()
            print("CST816D Revision = {}".format(Rev))
            self.Stop_Sleep()
        else    :
            print("Error: Not Detected CST816D.")
            return None
        self.Mode = mode
        self.Gestures="None"
        self.Flag = self.Flgh =self.l = 0
        self.X_point = self.Y_point = 0
        self.int.irq(handler=self.Int_Callback,trigger=Pin.IRQ_FALLING)
      
    def _read_byte(self,cmd):
        rec=self._bus.readfrom_mem(int(self._address),int(cmd),1)
        return rec[0]
    
    def _read_block(self, reg, length=1):
        rec=self._bus.readfrom_mem(int(self._address),int(reg),length)
        return rec
    
    def _write_byte(self,cmd,val):
        self._bus.writeto_mem(int(self._address),int(cmd),bytes([int(val)]))

    def WhoAmI(self):
        if (0xB5) != self._read_byte(0xA7):
            return False
        return True
    
    def Read_Revision(self):
        return self._read_byte(0xA9)
      
    #Stop sleeping  停止睡眠
    def Stop_Sleep(self):
        self._write_byte(0xFE,0x01)
    
    #Reset  复位    
    def Reset(self):
        self.rst(0)
        time.sleep_ms(1)
        self.rst(1)
        time.sleep_ms(50)
    
    #Set mode  设置模式   
    def Set_Mode(self,mode,callback_time=10,rest_time=5): 
        # mode = 0 gestures mode 
        # mode = 1 point mode 
        # mode = 2 mixed mode 
        if (mode == 1):      
            self._write_byte(0xFA,0X41)
            
        elif (mode == 2) :
            self._write_byte(0xFA,0X71)
            
        else:
            self._write_byte(0xFA,0X11)
            self._write_byte(0xEC,0X01)
     
    #Get the coordinates of the touch  获取触摸的坐标
    def get_point(self):
        xy_point = self._read_block(0x03,4)
        
        x_point= ((xy_point[0]&0x0f)<<8)+xy_point[1]
        y_point= ((xy_point[2]&0x0f)<<8)+xy_point[3]
        
        self.X_point=x_point
        self.Y_point=y_point
    
    #Draw points and show  画点并显示  
    def Touch_HandWriting(self):
        x = y = data = 0
        color = 0
        self.Flgh = 0
        self.Flag = 0
        self.Mode = 1
        self.Set_Mode(self.Mode)
        
        LCD.fill(LCD.white)
        LCD.rect(118,138,2,2,LCD.black)
        LCD.show()
        
        try:
            while True:              
                if self.Flag == 1:  
                    LCD.pixel(self.X_point,self.Y_point,color)
                    LCD.rect(self.X_point - 1,self.Y_point - 1,2,2,color)
                    LCD.Windows_show(x,y,self.X_point,self.Y_point)

        except KeyboardInterrupt:
            pass
    
    #Gesture  手势
    def Touch_Gesture(self):
        self.Mode = 0
        self.Set_Mode(self.Mode)
        LCD.write_text('Gesture test',70,90,1,LCD.black)
        LCD.write_text('Complete as prompted',35,120,1,LCD.black)
        LCD.show()
        time.sleep(5)
        LCD.fill(LCD.white)
        while self.Gestures != 0x02:
            LCD.fill(LCD.red)
            LCD.write_text('UP',100,110,3,LCD.black)
            LCD.show()
            
        while self.Gestures != 0x01:
            LCD.fill(LCD.black)
            LCD.write_text('DOWM',70,110,3,LCD.white)
            LCD.show()
            
        while self.Gestures != 0x03:
            LCD.fill(LCD.blue)
            LCD.write_text('LEFT',70,110,3,LCD.brown)
            LCD.show()
            
        while self.Gestures != 0x04:
            LCD.fill(LCD.brown)
            LCD.write_text('RIGHT',60,110,3,LCD.green)
            LCD.show()
            
        while self.Gestures != 0x0C:
            LCD.fill(LCD.yellow)
            LCD.write_text('Long Press',40,110,2,LCD.dark_red)
            LCD.show()
            
        while self.Gestures != 0x0B:
            LCD.fill(LCD.green)
            LCD.write_text('Double Click',25,110,2,LCD.yellow)
            LCD.show() 
        
    def Int_Callback(self,pin):
        if self.Mode == 0 :
            self.Gestures = self._read_byte(0x01)

        elif self.Mode == 1:           
            self.Flag = 1
            self.get_point()

    def Timer_callback(self,t):
        self.l += 1
        if self.l > 100:
            self.l = 50
