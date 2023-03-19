import socket
import _thread

class FwebIot:
    ''' Une interface web pour FmPyIot
    '''
    def __init__(self, iot, index = "fmpyiot/index.html", port = 80):
        self.iot = iot
        self.index = index
        self.load()
        self.addr = ('0.0.0.0',port)
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(self.addr)
        self.s.listen(1)
        self.s.settimeout(1.0) # 1 seconde
        self.loop_forever = False

    def load(self):
        '''load html file
        '''
        with open(self.index,'r') as f_index:
            self.html = f_index.read()

    def listen(self):
        '''Listen port 80 and return html
        '''
        try:
            cl, addr = self.s.accept()
        except OSError:
            pass
        else:
            print(f"cl = {cl}")
            print(f"addr = {addr}")
            cl_file = cl.makefile('rwb',0)
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
            response = self.html 
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()

    def listen_forever(self):
        self.loop_forever = True
        while self.loop_forever:
            self.listen()

    def stop(self):
        self.loop_forever = False

    def run(self):
        pass
