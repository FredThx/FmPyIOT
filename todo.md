# # BUGS

json.dump ne fonctione pas (depuis asyncio!)

ex : SYSINFO)

# deamons a mettre ne place

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

# Asynchrone

Maintenant que FmPyIot est asynchrone

=> lui mettre des coroutines en entrée (action ou read)

- les callback system (SYSINFO...)

exemple croquettes.
