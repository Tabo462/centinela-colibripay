# Diagrama del entorno

```
                         ┌────────────────────────────────────┐
                         │  AWS  ·  nube                      │
                         │  EC2 t3.large · Ubuntu 24.04 LTS   │
                         │  WAZUH  (manager + indexer + dash) │
                         │  Elastic IP fija · SG: solo mi IP  │
                         └─────────────────┬──────────────────┘
                                           │  logs del agente cifrados (:1514 / :1515)
                                           │  dashboard (:443)
                                           │  ── conexión SALIENTE desde casa ──
   ┌───────────────────────────────────────┼─────────────────────────────────────┐
   │  LAB EN CASA — VirtualBox             │                                     │
   │                                       │                                     │
   │   ┌─────────────────────────────┐     │                                     │
   │   │  DC01   Windows Server 2022 │─────┘  agente Wazuh + Sysmon              │
   │   │  AD DS + DNS + GPO          │                                           │
   │   │  corp.colibripay.mx         │   active-response (location: local)       │
   │   │  10.0.2.10  /  192.168.0.130│──────────────► IDS propio (Flask)         │
   │   │                             │                 127.0.0.1:5000 → netsh    │
   │   └──────────────┬──────────────┘                 (bloqueo en firewall)     │
   │                  │ mismo segmento L2 (adaptador Bridged durante el ataque)  │
   │   ┌──────────────┴──────────────┐                                           │
   │   │  Kali  (WSL en el host)     │   NetExec · Impacket · hashcat            │
   │   │  adversario · 192.168.0.105 │                                           │
   │   └─────────────────────────────┘                                           │
   └─────────────────────────────────────────────────────────────────────────────┘
```

Notas:

- **El SIEM (Wazuh) vive en la nube (AWS EC2)**, no en el host local. El agente en DC01
  reporta hacia la nube por una conexión saliente cifrada; el Security Group restringe
  el acceso a mi IP (ver `/detecciones`).

- **El atacante (Kali) corre como distribución de WSL** en el host, no como VM aparte.

- **Direccionamiento.** El lab se construyó sobre la red NAT de VirtualBox
  (`10.0.2.0/24`, DC01 = `10.0.2.10`) y se cambió a **Bridged** (`192.168.0.0/24`,
  DC01 = `192.168.0.130`) para la fase de ataque, porque el modo *mirrored* de WSL no
  enruta hacia los adaptadores Host-Only de VirtualBox. Por eso DC01 aparece con las
  dos IPs según la fase.

- **No hay estación de trabajo (WKS01).** El objetivo del ataque es DC01 directamente;
  Sysmon y el agente Wazuh corren en el propio controlador de dominio.
