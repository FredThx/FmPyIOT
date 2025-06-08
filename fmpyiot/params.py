import json, logging


#TODO
'''
- typer les paramètres (int, float, ...)
    - éventuellement avec dict : {topic : type, ...}

'''

class FmPyIotParams:
    '''Une collection de FmPyIotparam
    Utilisation :
        attribut de FmPyIot
            set_loader : définit une fonction callback lié à un paramètre : exécuté quand la valeur change
            set_param : Ajoute ou met à jour la valeur d'un paramètre
            set_params : Met à jour la valeur de plusieurs paralmètres (voir tous)
            to_html : pour web
    '''
    nested_separator = "__@@__"

    def __init__(self, params_json = "params.json"):
        self.params_json = params_json
        self.params_loaders = {}
        self.params:dict[str, FmPyIotParam] = self.load_json()
        
    def __iter__(self):
        for param in self.params:
            yield param
    
    def append(self, param):
        self[param.key] = param
    
    def get_params(self)->dict:
        '''Renvoie le contenu de params_json ou du cache self.params
        '''
        return self.params
    
    def set_params(self, params:bytes|dict|None=None):
        '''Met à jour des paramètres (self.params + fichier params_json)
        params :   json dict {key:value} or dict
        '''
        logging.debug(f"set_params({params=} ({type(params)}))")
        if type(params)==dict:
            data = params
        else:
            try:
                data = json.loads(params)
                assert type(data)==dict, "params must be a dict"
            except Exception as e:
                logging.error(e)
                return None
        for key, value in data.items():
            self.set_param(key, json.dumps(value))

    def set_param(self, key:bytes, payload:any=None, default:bytes|None=None, on_change:callable=None):
        '''Ajoute ou Met à jour un parametre (self.params + fichier params_json)
        si key est du genre "key{self.nested_separator}sub_key", alors self.params[key][sub_key] est modifié et self.param_loader(self.params[key]) est executé
        '''
        params = self.get_params()
        keys = key.split(self.nested_separator)
        #Defaults values
        if default is not None and key not in params and payload is None:
            payload = default
        elif type(payload) == dict and type(default) == dict and payload is None and key in params:
            payload = default
            payload.update(params[key])
        #decode payload
        if type(payload) in (str, bytes):
            try:
                payload = json.loads(payload)
                #payload = json.loads(payload) # Pour focer a faire des int, float #TODO : typer les paramètres
                logging.debug(f"payload decoded : {payload} => {payload} ({type(payload)})")
            except ValueError:
                logging.error(f"Error on set_params : {e}")
        logging.info(f"set_param(key={key},payload={payload} (type={type(payload)}))")
        #Update params (memory + disk)
        if payload is not None:
            self.set_nested_item(params, keys, payload)
            self.write_params(params)
        #Callback
        if on_change:
            self.params_loaders[keys[0]] = on_change
        if keys[0] in self.params_loaders:
            try:
                self.params_loaders[keys[0]](params[keys[0]])
            except Exception as e:
                print(f"Error on params_loader {keys[0]} : {e}")

    @classmethod
    def set_nested_item(cls, data_dict, maplist:list[str], val):
        '''Set item in nested dictionary'''
        assert len(maplist)>0, "maplist cannot be empty."
        if len(maplist)==1:
            data_dict[maplist[0]] = val
        else:
            cls.set_nested_item(data_dict[maplist[0]], maplist[1:], val)


    def load_json(self)->dict:
        '''tente de charger le fichier json, sinon, l'initialise'''
        try:
            with open(self.params_json,"r") as json_file:
                self.params = json.load(json_file)
                return self.params
        except (OSError, ValueError) as e:
            logging.warning(f"Error reading {self.params_json} : {e}")
            logging.info(f"create new empty file {self.params_json}")
            self.write_params({})
            return {}
            
    def write_params(self, params:dict):
        '''Ecrit le fichier params et le cache self.params
        '''
        logging.info(f"write params : {params}")
        self.params = params
        try:
            with open(self.params_json,"w") as json_file:
                json.dump(params, json_file)
        except OSError as e:
            logging.error(f"Error writing file {self.params_json} : {e}")

    def set_loader(self, key:str, loader:callable):
        '''Attribut une fonction à un paramètre. La fonction est executé lmors du changement de valeur.
        attributs de la fonction : new_value
        '''
        self.params_loaders[key] = loader

    def params_deep(self, super_key:str=None, params:dict=None):#->Iterator[tuple[str, str]]
        '''Renvoie un generator yield = (key, val) des paramètres de manière recursive (les sous dict sont parcourus)
        dans le cas de sous dict, la key est du type "key.sub_jey"
        '''
        for key, val in (params or self.params).items():
            if super_key:
                key = super_key + self.nested_separator + key
            if type(val) == dict:
                yield from self.params_deep(key, val)
            else:
                yield key, val

    def to_html(self):#->Iterator[str]
        '''Renvoi un generator du code html représentant les paramètres
        '''
        for key, val in self.params_deep():
            yield f'''
                <div>
                    <span>{key.replace(self.nested_separator, '.')} : </span>
                    <span>
                        <input type = "text" class="form_control" id="_params_{key}" placeholder="value", value = "{val}">
                    </span>
                    <span>
                        <input class="btn btn-primary btn-sm" id="_set_params_{key}" type="submit" value="Mise à jour">
                    </span>
                </div>
            '''.strip()

#Pour l'instant non utilisé (on reste sur un dict) => TODO
class FmPyIotParam:
    '''Un parametre pour FmPyIot
    '''
    def __init__(self, key:bytes, default:bytes|None=None, on_change:callable=None):
        self.key = key
        self.on_change = on_change

    