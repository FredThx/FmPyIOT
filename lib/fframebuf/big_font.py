import framebuf

class BigFont():
    '''A BIG font to write text on FrameBuffer
    '''
    def __init__(self, width:int=40, invert = False):
        self.width = width
        self.invert = invert
        self.letters:dict[str, dict] = {}

    def load_pbm(self, letter:str, filename:str):
        '''Load a pbm file
        '''
        with open(filename, 'rb') as file:
            assert file.readline() == b'P4\n', "pbm file not valid : only P4 (binary) type accepted."
            file.readline() # Creator comment
            width, height = [int(x) for x in file.readline().split()]
            data =bytearray(file.read())
        if not self.invert:
            data = bytearray((0xFF & ~byte for byte in data))
        buf = framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)
        self.letters[letter] = {
                'width' : width,
                'height' : height,
                'buf' : buf
            }

    def text(self, fb:framebuf.frameBuffer, text:str, x:int, y:int, c:int=None):
        '''Write text to FrameBuffer 
        '''
        for str_letter in text:
            if str_letter in self.letters:
                letter = self.letters[str_letter]
                fb.blit(letter['buf'], x, y)
                x += letter['width']
            elif str_letter==" ":
                x += self.width




