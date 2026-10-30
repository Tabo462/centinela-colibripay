# Cumplimiento

Mapeo de los controles técnicos del laboratorio a marcos de referencia, con **LFPDPPP**
como la obligación legal que los justifica en el contexto de Colibrí Pay (fintech que
maneja datos personales y de tarjetas).

## Por qué estos marcos

- **NIST CSF 2.0** -- marco primario; sus funciones (Identify / Protect / **Detect** /
  **Respond**) mapean directo al trabajo blue de este proyecto.
- **ISO 27001:2022 (Anexo A)** -- catálogo de controles, la certificación común en LATAM.
- **LFPDPPP** -- por qué Colibrí Pay *debe* hacer esto: proteger datos personales con
  medidas de seguridad administrativas, físicas y técnicas (art. 19).

## Matriz de mapeo

| Control implementado | Técnica/Ataque (ATT&CK) | NIST CSF 2.0 | ISO 27001:2022 | LFPDPPP |
|----------------------|-------------------------|--------------|-----------------|---------|
| Auditoría avanzada por GPO (4625/4769/4688…) | Todas | DE.CM | A.8.15 (logging) | Art. 19 -- medidas técnicas |
| SIEM (Wazuh) centraliza y correlaciona | Todas | DE.AE, DE.CM | A.8.16 (monitoreo) | Art. 19 |
| Detección password spray (regla 60204) | T1110.003 | DE.CM | A.8.5 (auth segura) | Art. 19 |
| Account lockout | T1110.003 | PR.AA / RS.MI | A.8.5 | Art. 19 |
| Detección Kerberoasting (regla custom 100200) | T1558.003 | DE.CM / DE.AE | A.5.17, A.8.5 | Art. 19 |
| Respuesta automatizada (IDS) | Contención | RS.MI / RS.AN | A.8.20, A.5.26 | Art. 19 |
| Sysmon (telemetría profunda) | Discovery/Execution | DE.CM | A.8.15, A.8.16 | Art. 19 |
| gMSA (recomendado -- causa raíz Kerberoasting) | T1558.003 | PR.AA | A.5.17 (gestión de credenciales) | Art. 19 |

## Nota de alcance (honestidad)

- El proyecto **implementa controles técnicos de detección y respuesta**; no cubre el
  programa completo de cumplimiento (políticas, avisos de privacidad, derechos ARCO,
  gestión de riesgos formal) que LFPDPPP exige a una fintech real.
- El mapeo demuestra *cómo un control técnico satisface una obligación*, que es el tipo
  de traducción técnico↔cumplimiento que se pide en un rol de infra/GRC.
- No todo control de seguridad "es cumplimiento": aquí se mapea solo lo que
  genuinamente aplica, distinguiendo seguridad real de *security theater*.
