import threading
import time

def tarea():
    time.sleep(2)
    print("hilo terrminado")
    
hilo = threading.Thread(target=tarea)
hilo.start()

hilo.join()
print("el ciclo ha terminado")