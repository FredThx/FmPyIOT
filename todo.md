# deamons a mettre ne place

## Publier une donnée
    - si la valeur change ou n'importe quel test
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


# Scanner de broker mqtt

# Serveur web

# Serveur telnet