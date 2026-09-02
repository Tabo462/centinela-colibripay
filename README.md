# centinela-colibripay
 
Proyecto que tiene como fin poner en práctica y descubrir el proceso de construir, atacar, defender y documentar el entorno de una fintech mexicana ficticia.
 
Laboratorio de detección de respuestas sobre un ecosistema empresarial simulado llamado **Colibrí Pay**.
 
El proyecto construye un dominio Active Directory con extensión a la nube, tiene un SIEM, ejecuta una cadena de ataque mapeada a MITRE ATT&CK, valida detección y la contención automatizada, y documenta todo como evidencia.
 
---
 
## Contexto de la empresa ficticia
 
- **Giro** — Fintech mexicana de pagos y billetera digital
- **Tamaño** — 120 empleados, un solo sitio + trabajo remoto. Empresa mediana, muy chica para tener un SOC dedicado y muy grande para tener obligaciones reales.
- **Regulación aplicable** — LFPDPPP, con referencia a Ley Fintech (CNBV) y alcance parcial PCI-DSS por manejar datos de tarjetas
---
 
## Objetivo
 
Cerrar la brecha entre habilidad ofensiva y experiencia en un entorno corporativo real, con SIEM, Active Directory, respuesta a incidentes, nube y cumplimiento. Construyéndolo, atacándolo y defendiéndolo con mis propias manos. Con evidencia que demuestra que funciona.
 
---
 
## Arquitectura
 
Ver el directorio [`/arquitectura`](./arquitectura) para ver el diagrama.
 
**Resumen:** AD on-prem con estación de trabajo, SIEM, con identidad extendida a Microsoft Entra ID. Todo en VMs sobre un host de 16 GB, el atacante es una instancia de Kali en WSL.
 
---
 
## Stack
 
- **Directorio** — Windows Server 2022 + Active Directory · Dominio, DNS, GPO
- **Endpoint** — Windows 11 Enterprise LTSC · Estación de trabajo y víctima
- **Telemetría** — Sysmon · Profundidad de telemetría en Windows
- **SIEM** — Wazuh · Correlación, detección, respuesta
- **Nube** — Microsoft Entra ID · Identidad, acceso condicional
- **Ataque** — Kali WSL · Adversario
- **Respuesta** — IDS propio creado anteriormente con Python y Flask · Active-response de bloqueo automático
- **Framework** — MITRE ATT&CK · NIST CSF · ISO 27001 · Mapeo técnico y de cumplimiento
---
 
## Estructura del repositorio
 
```text
centinela-colibripay/
├── arquitectura/      Diseño del entorno, diagrama y as-built
├── detecciones/       Catálogo de detecciones, reglas de Wazuh, config de Sysmon
├── ataque/            Cadena MITRE ATT&CK y matriz ataque↔detección
├── ids-integracion/   Integración del IDS propio como active-response del SIEM
├── incidente/         Reporte de respuesta a incidentes
├── cumplimiento/      Mapeo de controles a NIST CSF 2.0 e ISO 27001
└── evidencia/         Capturas de pantalla
```
 
---
 
## Frameworks
 
- **MITRE ATT&CK** — cada técnica ejecutada se etiqueta con su ID y se pone con su detección.
- **NIST CSF 2.0** — funciones Identify | Protect | Detect | Respond como marco primario del trabajo defensivo.
- **ISO 27001:2022** — catálogo de controles de referencia.
- **LFPDPPP** — obligación legal que justifica los controles en el contexto de la fintech.
---
 
## Autor
 
**Carlos Adrián Taboada Vivian** — Estudiante de Ciencias Computacionales, con enfoque en ciberseguridad
