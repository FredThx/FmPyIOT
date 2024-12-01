from micropython import const
import framebuf, logging

LEFT = const(1)
RIGHT = const(2)


class Display:
    '''Un ecran sur lequel on peut afficher des données 
    '''
    FONT_SIZE = (8,8)

    def __init__(self, device:framebuf.FrameBuffer):
        self.device = device
        self.topics={}

    @property
    def width_car(self):
        return self.device.width//self.FONT_SIZE[1]

    def update(self):
        try:
            self.device.update()
        except:
            self.device.show()

    def set_widget(self, topic:str, widget:Widget, payload:str = None):
        widget.root = self
        if topic not in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(widget)
        widget.show(payload)
    
    set_field = set_widget

    def text(self, text:str, row:int, column:int, color:int=1, backcolor:int=0):
        '''Write text on display
        '''
        x,y = column*self.FONT_SIZE[0], row*self.FONT_SIZE[1]
        try:
            self.device.rect(x,y,len(text*self.FONT_SIZE[0]), self.FONT_SIZE[1],backcolor,True)
        except TypeError:
            self.device.fill_rect(x,y,len(text*self.FONT_SIZE[0]), self.FONT_SIZE[1],backcolor)
        self.device.text(text, x,y, color)
    
    def draw_icon(self, icon, x:int, y:int, color:int=1, backcolor:int=0):
        '''Draw a icon ([[0,1,..], [...]])
        '''
        for i in range(len(icon[0])):
            for j in range(len(icon)):
                self.device.pixel(x+i,y+j,1 if icon[j][i]==color else 0)

    def set(self, topic:str, payload:str):
        logging.debug(f"{self}.set(topic='{topic}', payload = '{payload}')")
        if topic in self.topics:
            for w in self.topics[topic]:
                w.set(payload)
        else:
            logging.error(f"No topic {topic} in {self}")
    
    def power(self, value:bool):
        if value:
            self.device.poweron()
        else:
            self.device.poweroff()
    

class Widget:
    def __init__(self, invert):
        self.root=None
        self.color = 0 if invert else 1
        self.backcolor = 1 if invert else 0
        self.payload = None
    
    def set(self, payload:str):
        self.payload = payload
        self.show()
        self.root.update()
    
    def show(self, payload:str=None):
        if payload:
                self.payload = payload

class Field(Widget):
    '''Un champ avec label
    '''
    def __init__(self, label:str="",
                 row:int=0,column:int=0, width:int|None=None, height:int = 1,
                 align:int=LEFT,
                 invert = False,
                 unit:str=None
                 ):
        super().__init__(invert)
        self.label = label or ""
        self.row = row
        self.column = column
        self.height = height
        self.width = width
        self.align = align
        self.unit = unit or ""

    def show(self, payload:str=None):
        super().show(payload)
        self.root.text(self.label, self.row, self.column, self.color, self.backcolor)
        text = self.payload or ""
        self.width = self.width or self.root.width_car - len(self.label) #Initialize once
        text = text[:self.width] + self.unit
        if self.align == LEFT:
            text = text + " " * (self.width - len(text))
        else:
            text = " " * (self.width - len(text)) + text
        self.root.text(text, self.row, self.column + len(self.label), self.color, self.backcolor)
    
class WidgetPix(Widget):
    '''Un widget géré en x,y (alosr que Fields ets géré en row, colums)
    '''
    def __init__(self, x, y, invert):
        super().__init__(invert)
        self.x = x
        self.y = y


class Icon(WidgetPix):
    '''Une icone
    '''
    def __init__(self, x:int,y:int, invert=False, icons:dict=None, function:function=None):
        super().__init__(x, y, invert)
        self.icons = icons or {}
        self.f_icon = function

    def set_icon(self, payload:str, icon:list[list]):
        '''Affecte une icon à une valeur
        '''
        self.icons[payload] = icon
    
    def set_function_icon(self, function:function):
        self.f_icon = function

    def show(self, payload:str=None):
        super().show(payload)
        if self.payload in self.icons:
            self.root.draw_icon(self.icons[self.payload], self.x, self.y)
        elif self.f_icon:
            self.root.draw_icon(self.f_icon(self.payload), self.x, self.y)

class BarGraph(WidgetPix):
    '''Un barre graphe
    '''
    def __init__(self, x:int, y:int, lenght:int=100, width:int=10, n:int=10, max_value:float=1, orient:int=0, invert=False ):
        '''
        x,y     :   origine of the widget (top left corner)
        lenght  :   lenght 
        width   :   width
        n       :   qty of rectangles
        max_value : value for 100% full
        orient  :   angle in degres (0:➡️ , 90:⬆️ , 180:⬅️, 270:⬇️)
        '''
        super().__init__(x, y, invert)
        self.max_value = max_value
        self.n = n
        orient = orient % 360
        if orient==0:
            self.direction = lenght//n, 0
            self.rect = lenght//n -1, width
        elif orient==90:
            self.y = self.y + lenght-lenght//n
            self.direction = 0,-lenght//n
            self.rect = width, lenght//n - 1
        elif orient==180:
            self.x = self.x + lenght-lenght//n
            self.direction = -lenght//n, 0
            self.rect = lenght//n-1, width
        elif orient == 270:
            self.direction = 0, lenght//n
            self.rect = width, lenght//n -1
        else:
            raise Exception(f"orient must be in (0,90,180,270), not {orient}!")
            
    def show(self, payload:float=None):
        '''payload: float between 0.0 and 1.0
        '''
        super().show(payload)
        self.payload = float(self.payload or 0)
        x, y = self.x, self.y
        level:int = round(self.payload*self.n/self.max_value)
        for index in range(self.n):
            if index < level:
                self.root.device.fill_rect(x,y, *self.rect, self.color)
            else:
                self.root.device.fill_rect(x+1,y+1, self.rect[0]-1, self.rect[1]-2, self.backcolor)
                self.root.device.rect(x,y, *self.rect, self.color)
            x, y = x + self.direction[0], y + self.direction[1]
        

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