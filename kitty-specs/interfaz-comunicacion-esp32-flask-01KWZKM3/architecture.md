# Arquitectura CSI-ESP — Estilos y Patrones

## Contexto del sistema

```
┌──────────────────────────────────────────────────────────────┐
│                    CSI-ESP System                            │
│  ┌──────────┐  UART    ┌──────────────────┐  HTTP   ┌─────┐  │
│  │  ESP32   │ ───────> │  Servidor Flask  │ ──────> │ Web │  │
│  │(firmware)│ 921600   │  (Procesamiento) │  REST   │ UI  │  │
│  └──────────┘  baud    └──────────────────┘         └─────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Restricciones del proyecto**:
- Académico, sin producción — priorizar simplicidad sobre escalabilidad
- 1 ESP32 + 1 servidor local — sin necesidad de sistemas distribuidos
- Python + Flask + numpy — stack estándar científico

---

## Estilos de arquitectura

| Estilo              | ¿Aplica?        | Justificación                                                                 |
|---------------------|-----------------|-------------------------------------------------------------------------------|
| **Layered**         | ✅ Seleccionado | Separación natural: Lectura Serial → Parseo → Procesamiento → API |
| **Component-Based** | ✅ Seleccionado | Cada etapa del pipeline como componente independiente |
| **Client/Server**   | ✅ Seleccionado | ESP32 (cliente datos) ↔ Flask (servidor) ; Flask (backend) ↔ Web (frontend) |
| **ROA / RESTful**   | ✅ Seleccionado | API Flask para consultar datos procesados |
| **Pipeline**        | ✅ Seleccionado | Cadena de procesamiento: AGC → Hampel → Butterworth → SG → Fondo → Detección |
| **Monolithic App**  | ✅ Seleccionado | Flask monolítico para el servidor; modular por paquetes Python |
| SOA                 | ❌              | Un solo servidor; no hay servicios distribuidos |
| Microservices       | ❌              | Overhead injustificado para proyecto académico local |
| Message Bus         | ❌              | Sin necesidad de broker de mensajes entre servicios |
| Plug-ins            | ⏳ Futuro       | Podría permitir algoritmos de detección intercambiables |

---

## Patrones de diseño

### Para la capa de comunicación serial (interfaz actual)

| Patrón                         | ¿Aplica? | Uso                                                     |
|--------------------------------|----------|---------------------------------------------------------|
| **DTO (Data Transfer Object)** | ✅       | `CsiLine` transporta datos entre capas sin acoplamiento |
| **Repository**                 | ✅       | Abstracción del origen de datos (serial, archivo, mock) |
| **Polling**                    | ✅       | Lector serial consulta el puerto en bucle |
| **Store and Forward**          | ✅       | Buffer de líneas CSI antes de procesar |
| **Adapter**                    | ✅       | Adaptador del protocolo serial del ESP32 al modelo interno |

### Para la capa de procesamiento (futuro)

| Patrón                                 | ¿Aplica?| Uso                                                                |
|----------------------------------------|---------|--------------------------------------------------------------------|
| **Chain of Responsibility / Pipeline** | ✅      | Cada filtro es un eslabón: AGC → Hampel → Butterworth → SG → Fondo |
| **Strategy**                           | ✅      | Algoritmo de detección intercambiable (movimiento, presencia, etc.) |
| **Decorator**                          | ✅      | Agregar pre-procesamiento (normalización, ventaneo) sin modificar el núcleo |
| **Observer**                           | ✅      | Notificar a la API cuando hay nuevos datos procesados |
| **Factory Method**                     | ✅      | Crear el pipeline según configuración |

### Para la capa de presentación (futuro)

| Patrón | ¿Aplica? | Uso |
|--------|----------|-----|
| **MVC** | ✅ | Flask (Controller) + Jinja/React (View) + Modelos (Model) |
| **DAO (Data Access Object)** | ✅ | Acceso a datos almacenados (experimentos, sesiones) |

### No aplican (overkill para este proyecto)

| Patrón | Razón |
|--------|-------|
| Service Registry | Sin microservicios |
| Service Discovery | Sin microservicios |
| API Gateway | Sin microservicios |
| Circuit Breaker | Sin llamadas remotas a servicios externos |
| Load Balance | Una sola instancia del servidor |
| Access Token / SSO | Proyecto académico local, sin autenticación |
| Webhook | Sin integraciones externas que requieran callbacks |

---

## Mapa de capas vs patrones

```
┌────────────────────────────────────────────────────────── ────┐
│  Capa                │ Estilo         │ Patrones              │
├──────────────────────┼────────────────┼───────────────────────┤
│  Web UI (frontend)   │ MVC, REST      │ Controller → View     │
│  API (Flask routes)  │ RESTful        │ Controller, DTO       │
│  Procesamiento       │ Pipeline       │ Chain of Resp., Strat │
│  Comunicación Serial │ Component      │ DTO, Repository, Poll │
│  Firmware ESP32      │ Cliente/Serv   │ (C++ fijo, no patrón) │
└──────────────────────────────────────────────────────── ──────┘
```

## Flujo de datos con patrones

```
ESP32 ──UART──> [SerialReader] ──DTO──> [CsiParser]
                (Polling + Adapter)       (Factory)
                                              │
                                              ▼
                                     [Pipeline Processor]
                                      │  AGCCompensation
                                      │  HampelFilter
                                      │  ButterworthFilter
                                      │  SGFilter
                                      │  BackgroundSubtraction
                                      │  MotionDetection (Strategy)
                                              │
                                              ▼
                                     [CsiRepository] ──> [Flask API]
                                       (DAO)              (Controller)
                                                             │
                                              ┌──────────────┘
                                              ▼
                                        [Web UI / JSON Response]
                                          (View)
```
