from micropython import const
import framebuf

LEFT = const(1)
RIGHT = const(2)


class Display:
    '''Un ecran sur lequel on peutafficher des données 
    '''
    FONT_SIZE = (8,8)

    def __init__(self, device:framebuf.FrameBuffer):
        self.device = device
        self.topics={}

    def update(self):
        self.device.update()

    def set_field(self, topic:str, field:Field, payload:str = None):
        field.root = self
        self.topics[topic] = field
        field.show(payload)

    def text(self, text:str, row:int, column:int, color:int=1, backcolor:int=0):
        '''Write text on display
        '''
        x,y = column*self.FONT_SIZE[0], row*self.FONT_SIZE[1]
        self.device.rect(x,y,len(text*self.FONT_SIZE[0]), self.FONT_SIZE[1],backcolor,True)
        self.device.text(text, x,y, color)

    def set(self, topic:str, payload:str):
        try:
            field = self.topics[topic]
        except:
            print(f"No topic {topic}!")
        else:
            field.set(payload)

class Field:
    '''Un champ avec label
    '''
    def __init__(self, label:str,
                 row:int,column:int, width:int=1, height:int = 1,
                 align:int=LEFT,
                 invert = False
                 ):
        self.root = None
        self.label = label
        self.row = row
        self.column = column
        self.height = height
        self.width = width
        self.text = None
        self.align = align
        self.color = 0 if invert else 1
        self.backcolor = 1 if invert else 0

    def show(self, payload:str=None):
        if payload:
            self.text = payload
        self.root.text(self.label or "", self.row, self.column, self.color, self.backcolor)
        text = (self.text or "")[:self.width]
        if self.align == LEFT:
            text = text + " " * (self.width - len(text))
        else:
            text = " " * (self.width - len(text)) + text
        self.root.text(text, self.row, self.column + len(self.label), self.color, self.backcolor)
    
    def set(self, payload:str):
        self.text = payload
        self.show()
        self.root.update()


if __name__=='__main__':
    from lcd12864 import SPI_LCD12864
    from machine import Pin, SPI
    import time
    lcd = SPI_LCD12864(
        spi=SPI(0, polarity=0, phase = 1,bits=8, sck=Pin(6), mosi=Pin(7)),
        cs=Pin(5, Pin.OUT, value = 0)
    )
    disp = Display(lcd)
    disp.set_field("i", Field(disp, "I=", 0,1,width=5, align=RIGHT))
    disp.set_field("i2", Field(disp, "I*I=", 1,1,width=5, align=RIGHT))
    i=0
    while True:
       print(i)
       disp.set("i", str(i)) 
       disp.set("i2", str(i*i)) 
       time.sleep(0.5)
       i+=1