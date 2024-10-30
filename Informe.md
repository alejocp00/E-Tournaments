# Sistemas Distribuidos

## E-Tournaments

**Ana Karla Caballero C-411**  
**Alejandro Camacho C-412**

### Abstract

Este proyecto consiste en un simulador de torneos de juegos de eliminación directa, donde los jugadores son virtuales. El juego implementado es TicTacToe, y el tipo de jugador virtual utilizado es aleatorio. Todo esto se ejecuta sobre un sistema distribuido.

Un sistema distribuido se define como un conjunto de equipos independientes que operan de manera conjunta, funcionando como si fueran un único sistema. Su principal objetivo es descentralizar tanto el almacenamiento de la información como el procesamiento de datos. En este proyecto, se implementa una arquitectura DHT Chord con algunas modificaciones, así como un algoritmo de replicación de información y otro de balanceo de carga. Todo esto se ha diseñado para asegurar la correcta y eficiente ejecución de diferentes tipos de torneos creados por múltiples clientes.

### Chord

Chord es una tabla hash distribuida que se utiliza para implementar redes peer-to-peer estructuradas. Esta especifica qué información debe almacenar cada nodo en la red, incluyendo datos sobre otros nodos y archivos compartidos. También se encarga de regular la comunicación y el intercambio de mensajes entre ellos.

#### Asignación de IDs a los nodos

Cada nodo y los IDs de los archivos compartidos se asocian a un identificador binario de m bits. El valor de m es un parámetro que se puede configurar al crear la instancia de los servidores en  server.py . La asignación de IDs se realiza utilizando la función hash SHA-1, y los identificadores de los nodos se representan en un anillo de identificadores módulo \(2^m\). Por lo tanto, el rango de los valores de los identificadores de nodos y claves va desde 0 hasta \(2^m-1\).

#### Lista de sucesores y predecesores

Para mejorar la robustez de la tabla hash distribuida, cada nodo mantiene una lista de sucesores y predecesores de tamaño \(k\), donde \(k \leq n\) y \(n\) es el total de nodos en la red. En este proyecto, se ha decidido que \(k = n\). Más adelante se discutirán las ventajas y desventajas de esta elección.

#### Elección del coordinador

A diferencia de la implementación clásica de Chord, en este proyecto, el nodo coordinador será inicialmente el que tenga el mayor ID en la red. Dado que cada nodo tiene una lista de sucesores que incluye a todos los nodos, siempre habrá consenso. Si se añade un nuevo servidor con un ID mayor que el del coordinador, se ha decidido mantener el mismo líder. Se explicarán más adelante las ventajas y desventajas de esta decisión.

#### Finger Table

Un nodo en Chord necesita almacenar información sobre unos pocos nodos de la red para localizar la clave que busca. Esta información se guarda en una tabla conocida como finger table, que tiene \(m\) entradas, donde \(m\) es la longitud de los identificadores en el anillo. Cada entrada \(2^i\) (donde \(0 \leq i \leq m-1\)) en la finger table de un nodo con identificador \(n\) contiene el ID del nodo sucesor de \((n + 2^i)\) y su dirección IP.

#### Inserción de un nodo en la red

La inserción de un nuevo nodo debe mantener siempre tres invariantes:

1. La estructura de anillo, donde el ID de cada nodo es menor que el de su sucesor, excepto en el caso en que el nodo con el ID más alto se conecta al de ID más bajo para cerrar el anillo.
2. La finger table debe estar actualizada, ya que es crucial para llevar a cabo los algoritmos de búsqueda.
3. La tabla de sucesores también debe estar actualizada, ya que se utiliza para mantener la consistencia del anillo en caso de fallos en algún servidor. Este algoritmo se explicará con más detalle más adelante.

A diferencia del algoritmo clásico de Chord, donde el nodo coordinador maneja las solicitudes de nuevos nodos, en este proyecto la inserción de nodos se realiza mediante multicast. Cuando un nodo desea unirse a la red, envía un mensaje multicast, y pueden ocurrir tres situaciones:

1. Nadie escucha el mensaje (no hay más servidores), por lo que este se convierte en el primero y ejecuta un método para recibir mensajes multicast de nuevos servidores.
2. Solo un servidor que ya pertenece a la red escucha el mensaje. Dependiendo del ID del nuevo nodo, el servidor crea la conexión manteniendo la primera invariante, y le envía la lista de sucesores para que el nuevo nodo se actualice. Ambos actualizan sus respectivas finger tables, cumpliendo así las otras dos invariantes.
3. Más de un nodo escucha el mensaje. En este caso, solo los nodos entre los cuales debe insertarse el nuevo servidor responden, enviándole la lista de sucesores y la finger table, mientras que los demás simplemente actualizan.

#### Eliminación de un nodo de la red

Al igual que en la inserción, se deben mantener las tres invariantes. Cuando un nodo sale de la red, el responsable de mantener la consistencia del algoritmo es el nodo predecesor, que puede detectar casi instantáneamente cuando un nodo se desconecta. Este nodo utiliza la tabla de sucesores para intentar conectarse al nodo sucesor del que ha caído. Si este tampoco responde, intentará con el siguiente, y así sucesivamente. Esto puede llevar a dos situaciones:

1. No hay ningún nodo en la lista de sucesores que pueda aceptar conexión, dejando al nodo solo en la red.
2. Existe al menos un nodo al que puede conectarse. Después de hacerlo, le informa sobre todos los nodos que han caído para que actualice la lista de sucesores y la finger table. Este último propagará el mensaje a los demás servidores, asegurando que todos actualicen el cambio y mantengan la estabilidad de la red.

#### Algoritmo de búsqueda

Cuando un nodo \(n\) busca información de un ID \(k\), primero verifica si \(k\) está entre su identificador y el de su predecesor. Si \(k\) se encuentra en ese rango, el nodo \(n\) es responsable de \(k\) y consultará su tabla de claves para finalizar la búsqueda. Si no está en ese rango, \(n\) buscará el nodo responsable de \(k\) en su finger table siguiendo estos pasos:

1. Encuentra el nodo responsable de \(k\) en su finger table y envía la solicitud de búsqueda directamente a ese nodo, finalizando la búsqueda.
2. Si no encuentra el nodo responsable de \(k\), busca en su finger table un nodo \(j\) cuyo ID sea más cercano a \(k\) que el suyo, ya que ese nodo podría tener más información sobre la región del anillo donde se ubica \(k\). Luego, \(n\) envía la solicitud de búsqueda de \(k\) a ese nodo \(j\).

Este proceso se repite, permitiendo que los nodos descubran otros nodos cuyos IDs están cada vez más cerca de \(k\). En este proyecto, este algoritmo de búsqueda se utiliza para enviar de manera eficiente al nodo coordinador las notificaciones de cada jugada realizada por los servidores, para que luego este las muestre al cliente.

#### Balanceo de carga

Se implementó un algoritmo para equilibrar la carga de los servidores en la red, con el fin de distribuir de manera equitativa la cantidad de partidas de juegos que ejecuta cada servidor. El líder recibe la solicitud de un cliente y, tras crear las partidas necesarias, verifica si el servidor que lo tiene como sucesor tiene un número de hilos de juego activos mayor o igual al suyo. Si es así, el líder toma un juego y le transfiere los demás a su sucesor, quien repetirá el mismo procedimiento hasta que todos los juegos estén repartidos equitativamente.

#### Réplica

##### En juegos

Cada nodo \(n\) de la red mantiene una réplica del estado de los juegos que se ejecutan en los nodos de su finger table. Así, si \(n\) falla, el primer nodo que reciba el mensaje de aviso podrá continuar la ejecución de los juegos que \(n\) estaba gestionando.

##### En torneos

El nodo líder, además de replicar las jugadas mencionadas anteriormente, también replica constantemente en su finger table el estado de los torneos en curso. De esta manera, si el líder falla, al concluir el algoritmo de eliminación de un nodo de la red, todos tendrán una réplica del estado del torneo, permitiendo que el nuevo servidor que asuma el liderazgo mantenga la correcta ejecución del torneo. Los otros servidores eliminarán esta réplica para liberar espacio.

#### Flujo de ejecución

Una vez que se lleva a cabo el algoritmo de balanceo de carga, cada servidor comienza a ejecutar los juegos que le corresponden, replicando las jugadas en los nodos de su finger table (y el estado de los torneos si es el líder). Además, envían al líder esas jugadas mediante el algoritmo de búsqueda mencionado anteriormente. A medida que el líder recibe las jugadas, las envía al cliente para su visualización.

#### Tolerancia a fallas

Cuando un servidor que no es líder falla, se deben considerar ciertos aspectos:

1. Retomar la réplica de los juegos que estaba ejecutando, lo cual se resuelve utilizando lo explicado en la sección de Réplicas en Juegos.
2. Es probable que este servidor tenga mensajes pendientes para enviar al líder, provenientes de otros servidores, que se pierden al caer. La solución es que los servidores que detecten su caída, al actualizar sus finger tables y otras estructuras, vuelvan a enviar las últimas \(k\) jugadas que ya habían enviado para tratar de reparar la pérdida o, en el peor de los casos, minimizarla.
3. Si aún así se pierde información (especialmente de los ganadores, ya que una ronda no puede avanzar sin todos), se implementó un algoritmo que, tras cierto tiempo, busca si hay jugadas del juego perdido para retomarlo. Si esto no es posible, se reejecuta desde el inicio.

Si el servidor líder falla, se realizarán las funciones 1 y 3 mencionadas anteriormente, además de:

1. Retomar la réplica de los torneos que estaba gestionando, utilizando lo explicado en la sección de Réplicas en Torneos.

Cuando un cliente falla, el sistema continúa ejecutando su torneo y lo guarda por un tiempo predefinido, permitiendo que, si el cliente vuelve a entrar, pueda continuar viendo el torneo desde donde lo dejó, volver a verlo desde el principio o iniciar uno nuevo.

#### Análisis de las características de la implementación

##### Tabla de sucesores con tamaño \(k=n\)

**Ventajas:**

1. Mejora el proceso de eliminación, ya que cuanto más grande sea el tamaño de la tabla, más difícil será romper la red.
2. Elimina la necesidad de un algoritmo de elección de líder, ya que todos estarán de acuerdo en que el líder sea el servidor con el ID más alto de la lista de sucesores.
3. Al no requerir algoritmos de elección de líder, se evitan sus desventajas.
4. Funciona bien en redes de servidores de tamaño moderado.

**Desventajas:**

1. Difícil de mantener con un número elevado de servidores.
2. Una falla puede desestabilizar la consistencia del anillo, afectando su funcionamiento.

### Uso de multicast para crear conexiones

**Ventajas:**

1. Reduce la carga del nodo coordinador al no tener que centrarse en la inserción, disminuyendo así el tráfico de la red.
2. Facilita la actualización de la lista de sucesores y la finger table de cada servidor, ya que todos reciben el mensaje simultáneamente.
3. Disminuye el tráfico en la red al evitar el intercambio de mensajes entre servidores para determinar dónde puede insertarse un nuevo nodo.

**Desventajas:**

1. Si el receptor de multicast que debería participar en la inserción falla, puede haber retrasos en el funcionamiento de la red, aunque el problema se solucione más adelante.
2. En redes con muchos servidores, es posible que el mensaje no llegue a todos, lo que puede provocar la primera falla mencionada.

##### Replicar en la finger table

**Ventajas:**

1. Al estar siempre actualizada, las réplicas estarán correctamente localizadas.
2. Si los servidores fallan en intervalos de al menos 2 segundos, se podrá preservar la réplica, incluso si solo queda un servidor en el sistema.

**Desventajas:**

1. Si dos o más servidores fallan simultáneamente en menos de 2 segundos, es probable que se pierda información. Esta falla se controla mediante verificaciones periódicas, y si se excede el tiempo, la información se considera perdida, notificándose al cliente y continuando con la ejecución del programa.
