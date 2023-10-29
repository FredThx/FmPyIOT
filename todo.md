# # BUGS

SYSINFO (et autre) : json format.

# Divers

- wifi country
- mqtt mqtt_client_name
- mqtt log

# Deamons a mettre en place

## Publier une donnée

    - si la valeur change ou n'importe quel test
    - sur trigger : fait

## REPL via mqtt

    topic : ./REPL_
    Mais a priori, il est impossible de rediriger stdout en micropython
    (alors qu'en python3, c'est easy :

    ``python     from contextlib import redirect_stdout      from io import StringIO     with redirect_stdout(f):         exec("print(42)")     capture = f.getvalue()     ``
    )

# Scanner de broker mqtt

# Serveur web

Maintenant que le reseau est ok en async, ce devrait aller mieux

# Serveur telnet
