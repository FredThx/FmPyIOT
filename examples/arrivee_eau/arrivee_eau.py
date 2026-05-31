from fmpyiot.fmpyiot_web import FmPyIotWeb
from fmpyiot.topics import TopicAction, TopicRead
from fmpyiot.device import Device
from machine import Pin
from flowmeter import FlowMeter
import logging, time

class ArriveeEau(Device):
    '''
    Class representing a water inlet fitted with a valve and a flow meter 
    '''
    params = {
        'flowmeter_interval' : 5,
        'flowmeter_A' : 8.1,  # Calibration factor A for flow rate calculation
        'flowmeter_B' : 5,  # Calibration factor B for flow rate calculation
    }
    def __init__(self,
                 pin_valve:int,
                 pin_flowmeter:int,
                 name = "Arrivée d'Eau"):
        '''
        :param pin_valve: GPIO pin number for controlling the valve (output)
        :param pin_flowmeter: GPIO pin number for reading the flow meter (input)
        '''
        super().__init__(name)
        self.pin_valve = Pin(pin_valve, Pin.OUT)
        self.flowmeter = FlowMeter(
            pin=pin_flowmeter,
            A=self.params['flowmeter_A'], B=self.params['flowmeter_B'],
            interval=self.params['flowmeter_interval'],
            auto_save=True)
        self.load_params()
    
    def on_load_params(self):
        '''Called on load_params and when parameters are changed'''
        logging.info(f"ArriveeEau.load_params({self.params})")
        self.flowmeter.interval = self.params['flowmeter_interval']
        self.flowmeter.A = self.params['flowmeter_A']
        self.flowmeter.B = self.params['flowmeter_B']

    def set_iot(self, iot:FmPyIotWeb):
        '''
        Crée les topics MQTT pour gérer l'arrivée d'eau :
        ./FLOW : topic de lecture (sortant) du débit mesuré par le débitmètre
                    envoyé toutes les 5 secondes
        ./VOLUME : topic de lecture (sortant) du volume total d'eau écoulé depuis le démarrage
        ./SET_VOLUME : topic d'action (entrant) pour réinitialiser le volume total 
        ./VANNE : topic action (entrant) pour contrôler les LEDs indicatrices
        '''
        super().set_iot(iot)
        iot.add_topic(TopicRead("./FLOW", read= self.flowmeter.get_flow_rate, send_period=7))
        iot.add_topic(TopicRead("./VOLUME", read= self.flowmeter.get_liter_count, send_period=20))
        iot.add_topic(TopicRead("./VANNE_STATUS", read= lambda : 'OFF' if self.pin_valve.value() else 'ON', send_period=10))
        iot.add_topic(TopicAction("./VANNE", action = lambda topic, payload : self.set_valve(payload)))
        iot.add_topic(TopicAction("./SET_VOLUME", action = lambda topic, payload : self.flowmeter.reset(volume=float(payload) if payload else 0.0)))
    

    def set_valve(self, payload:str):
        '''Ouvre ou ferme la vanne en fonction du payload reçu ('ON' ou 'OFF')
        La vanne étant Normalement Ouverte, elle est fermée quand la sortie est à 1 et ouverte quand la sortie est à 0
        '''
        logging.info(f"Set valve = '{payload}'")
        if payload == 'ON':
            self.pin_valve.off() # la vanne est ouverte quand la sortie est à 0 (Normalement Ouverte)
        else:
            self.pin_valve.on() # la vanne est fermée quand la sortie est à 1 (Normalement Ouverte)

    def render_web(self)->str:
        '''Renders the web page content
        '''
        heure = '%s-%s-%s %s:%s:%s'%(time.localtime()[:6])
        html = f"""<br><H3>Arrivée d'eau dans la cave</H3>
            <p>Current Time: {heure}</p>
            <p>Débit instantané : {self.flowmeter.get_flow_rate():.1f} L/min</p>
            <p>Volume total : {self.flowmeter.get_liter_count()/1000:.3f} m3</p>
            <br>
            <p>Etat de la vanne : {'Fermée' if self.pin_valve.value() else 'Ouverte'}</p>
            <button type="button" onclick="postAction('/api/action/action_T__VANNE', 'ON')">Ouvrir la vanne</button>
            <button type="button" onclick="postAction('/api/action/action_T__VANNE', 'OFF')">Fermer la vanne</button>
            <button type="button" onclick="postAction('/api/action/action_T__SET_VOLUME', '0')">Réinitialiser le volume</button>
            <script>
                async function postAction(url, payload) {{
                    try {{
                        const params = new URLSearchParams();
                        params.append('payload', payload);
                        const response = await fetch(url, {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                            body: params.toString()
                        }});
                        if (!response.ok) {{
                            console.error('Erreur POST', response.status, response.statusText);
                        }}
                    }} catch (error) {{
                        console.error('Erreur fetch', error);
                    }}
                }}
            </script>
            """
        return html


