from machine import Pin


class PicoRender:

    icon_on = '<i class="bi bi-lightbulb-fill" style="color:green"></i>'
    icon_off = '<i class="bi bi-lightbulb-off"></i>'

    GND = '<span style="background-color:black; color:white">&nbspGND&nbsp</span>'
    VBUS = '<span style="background-color:red; color:white">&nbspVBUS&nbsp</span>'
    VSYS = '<span style="background-color:red; color:white">&nbspVSYS&nbsp</span>'
    _3V3_EN = '<span style="background-color:pink; color:white">&nbsp3V3_EN&nbsp</span>'
    _3V3_OUT = '<span style="background-color:red; color:white">&nbsp3V3(OUT)&nbsp</span>'
    ADC_VREF = '<span style="background-color:green; color:white">&nbspADC_VREF&nbsp</span>'
    RUN = '<span style="background-color:pink; color:white">&nbspRUN&nbsp</span>'

    pinout = [
        [0,1,GND,2,3,4,5,GND,6,7,8,9,GND,10,11,12,13,GND,14,15],
        [VBUS,VSYS,GND,_3V3_EN,_3V3_OUT,ADC_VREF,28,GND,27,26,RUN,22,GND,21,20,19,18,GND,17,16],
    ]

    def __init__(self, title_html:str="<H4>Pico GPIO Status</H4>"):
        self.title_html = title_html

    def render(self):
        html_content = self.title_html
        html_content += '<table>'
        for index_row in range(len(self.pinout[0])):
            html_content += f"<tr>"
            for index_col in range(len(self.pinout)):
                pin = self.pinout[index_col][index_row]
                html_content += f'<td style = "width:50%">'
                if isinstance(pin, int):
                    html_content += self.render_pin(pin)
                else:
                    html_content += pin
                html_content += '</td>'
            html_content += "</tr>"
        html_content += '</table>'
        return html_content
    
    def render_pin(self, pin_number):
        pin = Pin(pin_number)
        return f'<div><span style="background-color:YellowGreen; color:white">&nbspGP{pin_number}&nbsp</span> : {self.icon_on if pin() else self.icon_off}</div>'
    