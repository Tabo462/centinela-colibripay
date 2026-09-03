# Diagrama del entorno


```
                              INTERNET
                                 │
                  ┌──────────────┴───────────────┐
                  │   Microsoft Entra ID    [ ]  │   (nube — tenant E5 dev)
                  │   Conditional Access · MFA   │
                  │   Purview (cumplimiento)     │
                  └──────────────┬───────────────┘
                                 │ logs (API O365) → Wazuh
                                 │
   ┌─────────────────────────────┴──────────────────────────────┐
   │           RED NAT VirtualBox — 10.0.2.0/24 (aislada)       │
   │                                                            │
   │   ┌──────────────────────┐      ┌───────────────────────┐  │
   │   │  DC01        [   ]   │      │  WAZUH (SIEM)   [ ]   │  │
   │   │  Win Server 2022     │◄────►│  Ubuntu Server        │  │
   │   │  AD DS + DNS         │ logs │  + módulo O365/Azure  │  │
   │   │  corp.colibripay.mx  │      │  + active-response ───┼──┼──► IDS propio
   │   │  10.0.2.10           │      │  10.0.2.30            │  │    (FastAPI) [ ]
   │   └──────────┬───────────┘      └───────────┬───────────┘  │
   │              │ join                         │ agente       │
   │   ┌──────────┴────────────┐                 │              │
   │   │  WKS01         [ ]    │─────────────────┘              │
   │   │  Win 11 LTSC          │  Sysmon + agente Wazuh         │
   │   │  10.0.2.20 (víctima)  │                                │
   │   └───────────────────────┘                                │
   └────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ ataque (red NAT)
                     ┌───────────┴────────────┐
                     │  Kali (WSL)      []    │
                     │  NetExec · Impacket    │
                     │  BloodHound            │
                     └────────────────────────┘
```

Notas:

- El atacante (Kali) corre como distribución de **WSL** en el host, no como VM
  aparte.
- Las herramientas .NET (Rubeus, SharpHound.exe) se ejecutan desde **WKS01** una vez
  comprometida, no desde Kali
