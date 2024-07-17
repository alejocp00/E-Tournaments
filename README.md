# Distribuido

## Informe Técnico

Autores:

- Alejandro Camacho Perez C-412
- Ana Karla Caballero Gonzalez C-411

### Introducción

Este informe se detalla el diseño e implementación de un sistema distribuido destinado a la organización de torneos online para juegos de dos jugadores. El sistema está diseñado para aprovechar la capacidad de cómputo de múltiples equipos, permitiendo la realización de enfrentamientos virtuales en paralelo y ofreciendo una experiencia rica en características para los administradores de torneos y participantes.

#### Características del Sistema

* Arquitectura Distribuida
El sistema adopta una arquitectura orientada a servicios, lo que significa que los componentes del sistema están dispersos en múltiples máquinas pero trabajan juntos como un solo sistema. Esta arquitectura mejora la escalabilidad y la tolerancia a fallos.

* Tolerancia a Fallos
Se implementan mecanismos de tolerancia a fallos para garantizar que el desarrollo de los torneos no se vea interrumpido por fallas en los equipos donde se están llevando a cabo enfrentamientos. Esto incluye la replicación de datos y servicios críticos, así como estrategias de recuperación ante fallos.

* Migración de Código
El sistema permite la migración de código de los jugadores virtuales al nodo donde se efectuarán los enfrentamientos. Esto optimiza el uso de recursos computacionales y mejora la eficiencia del sistema.

* Modalidades de Torneos
La modalidad implementada en este proyecto es la de eliminición directa

* Acceso a Información y Estadísticas

* Desarrollo Simultáneo de Torneos
El sistema está diseñado para soportar la realización de varios torneos simultáneamente sin comprometer el rendimiento o la integridad de los datos.

#### Implementación Técnica

##### Microservicios

El sistema se divide en tres microservicios fundamentales:

* Gestión de Información:
Encargado de administrar toda la información relacionada con los torneos, jugadores y juegos. Esto incluye datos sobre administradores de torneos, jugadores registrados, torneos creados y en curso, así como detalles sobre los juegos disponibles y en juego.

* Gestión de Torneo:
Se ocupa de la lógica específica de cada torneo, incluyendo la creación, gestión y seguimiento de los enfrentamientos dentro del torneo.

* Gestión de Juego:
Responsable de ejecutar las instancias de los juegos entre jugadores virtuales, gestionando el estado del juego y comunicando los resultados a otros componentes del sistema.

##### Contenedores y Docker Compose

Cada uno de estos microservicios se empaqueta en contenedores Docker, lo que facilita su despliegue, escalabilidad y gestión. Utilizando Docker Compose, estos contenedores pueden ser orquestados fácilmente, permitiendo la generación automática de nuevos contenedores según sea necesario para soportar la carga adicional durante la creación de nuevos torneos y juegos.

##### Comunicación a través de Sockets

La comunicación entre los microservicios y con los clientes se realiza mediante sockets TCP/IP. Esto permite una comunicación eficiente y en tiempo real, esencial para la actualización de estados de juego, resultados de enfrentamientos y otras interacciones dinámicas dentro del sistema.

#### Conclusión

Este sistema distribuido para la organización de torneos online representa una solución robusta y escalable que aprovecha las ventajas de la arquitectura distribuida, la tolerancia a fallos y la comunicación en tiempo real. Al dividir el sistema en microservicios bien definidos y utilizar contenedores Docker para su implementación, se facilita la gestión, escalabilidad y mantenimiento del sistema. La capacidad de soportar múltiples modalidades de torneos y ofrecer acceso detallado a información y estadísticas mejora significativamente la experiencia tanto para los organizadores de torneos como para los participantes.