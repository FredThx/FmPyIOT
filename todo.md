# deamons a mettre ne place

## Publier une donnée
    ex : le poids de la balance
    - a interval régulier
        un timer pour tous ok 
    - à la demande via mqtt
        topic_ / SENDIT     OK
    - si la valeur change ou n'importe quel test
    - json si object ok 
    - sur trigger

## REPL via mqtt
    topic : ./REPL_
    Mais a priori, il est impossible de rediriger stdout en micropython
    (alorq qu'en python3, c'est easy : 
    
    ```python
    from contextlib import redirect_stdout 
    from io import StringIO
    with redirect_stdout(f):
        exec("print(42)")
    capture = f.getvalue()
    ```
    )

## Watchdog
    envoie d'un message régulièrement ok
    Si pas de réponse => reboot

## SYSTEM

    -  publish à la connection

# Scanner de broker mqtt

# Serveur web

# Serveur telnet