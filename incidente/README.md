# Reporte de respuesta a incidentes

Reporte del incidente simulado contra Colibrí Pay, reconstruido **a partir de los
datos del SIEM**, siguiendo las fases de **NIST SP 800-61**. Que el incidente se pueda
reconstruir solo con la telemetría de Wazuh es, en sí, la prueba de que el logging
capturó el ataque.

- **Fecha del ejercicio:** 28–29 oct 2026
- **Activo afectado:** DC01 (`corp.colibripay.mx`) — controlador de dominio
- **Analista:** Carlos Taboada
- **Clasificación:** ejercicio purple team controlado (no incidente real)

## 1. Preparación

Controles en su lugar antes del ataque:
- Auditoría avanzada por GPO (4624/4625, 4768/4769, 4720, 4688 con línea de comando).
- SIEM Wazuh en la nube (AWS) con agente en DC01 + Sysmon.
- Regla custom de detección de Kerberoasting (100200).
- Herramienta propia de respuesta (IDS/webhook) con allowlist y bloqueo temporal.

## 2. Detección y análisis

**Línea de tiempo (reconstruida del SIEM):**

| Hora | Evento | Fuente/Regla |
|------|--------|--------------|
| T0 | Ráfaga de 8 fallos de logon contra `mtorres` desde `192.168.0.105` | 4625 / 60122 |
| T0+Xs | Alerta compuesta "Multiple Windows Logon Failures" (nivel 10) | Regla 60204 |
| T0+Xm | Cuenta `mtorres` bloqueada (account lockout) | AD |
| T1 | Petición de TGS para `svc_sql` con cifrado RC4 | 4769 |
| T1 | Alerta "Posible Kerberoasting" (nivel 12), serviceName `svc_sql` | Regla custom 100200 |
| T1+ | (Offline, invisible) crackeo del hash → `Password1` | — |

**Análisis.** El patrón —fuerza bruta seguida de Kerberoasting contra una cuenta de
servicio— es la cadena típica de un adversario que busca escalar desde un punto de
apoyo. La IP de origen (`192.168.0.105`) y la cuenta `mtorres` fueron el vector; la
cuenta de servicio `svc_sql` (con SPN y contraseña débil) fue el objetivo de valor.

**Triaje.** La alerta 100200 (RC4 a cuenta de servicio) se confirmó como verdadero
positivo correlacionando: usuario sin privilegios pidiendo el TGS de una cuenta de
servicio, con cifrado RC4 (débil), fuera de patrón normal.

## 3. Contención, erradicación y recuperación

**Contención:**
- Account lockout bloqueó la cuenta usada en el spray (automático).
- Respuesta automatizada (IDS) diseñada para bloquear la IP origen en el firewall
  (verificada en unit test; dispatch del active-response documentado como pendiente).

**Erradicación / recuperación (remediación recomendada):**
- Rotar la contraseña de `svc_sql` y **migrarla a una gMSA** (causa raíz).
- Revisar y reducir cuentas con SPN; aplicar contraseñas largas/gestionadas.
- Forzar cifrado **AES** para Kerberos; deshabilitar RC4 donde sea posible.

## 4. Lecciones aprendidas

- **La detección de Kerberoasting requiere una regla custom** — el ruleset de fábrica
  no alerta de 4769. La regla 100200 (RC4 + cuenta de servicio) cierra ese gap.
- **La causa raíz es humana**: `svc_sql` tenía contraseña débil. La defensa real no es
  solo detectar, es eliminar la causa con gMSA.
- **RC4 es un indicador, no prueba** — una detección de producción correlacionaría más
  señales para bajar falsos positivos.
- **La contención automática necesita salvaguardas** (allowlist, bloqueo temporal) para
  no causar auto-DoS — implementadas en el IDS.
