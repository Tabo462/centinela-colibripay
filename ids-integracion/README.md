# Integración del IDS propio como Active-Response (SOAR-lite)

Integración de una herramienta propia de detección/respuesta (Python/Flask) como el
**brazo de respuesta automatizada de Wazuh**: cuando el SIEM detecta un brute-force,
ordena a la herramienta bloquear la IP origen en el firewall de Windows.

El IDS original detectaba el 4625 por su cuenta y alertaba por Telegram. Aquí se
refactorizó para un modelo **SOAR-lite**: Wazuh es el cerebro (detección), el IDS es
el músculo (contención). El código vive en el proyecto `IDS-IPS` (`webhook.py`).

## Flujo de punta a punta

```
Brute-force contra DC01 (4625 en ráfaga)
  -> agente Wazuh manda los eventos a la nube
  -> Manager (AWS) la regla 60204 (Multiple Logon Failures) dispara
  -> Manager ordena active-response en el agente de DC01  (location: local)
  -> el agente ejecuta ids-block.cmd -> wazuh_ar_bridge.py
  -> el bridge hace POST a 127.0.0.1:5000/block (el webhook)
  -> el webhook decide y, si procede, bloquea la IP en el firewall
```

## Decisiones de diseño (lo defendible en entrevista)

- **Dispara en la regla compuesta (60204), no en el 4625 individual (60122).** Solo se
  activa con *varios* fallos en poco tiempo, no con un typo legítimo. Es la salvaguarda
  antes de todas las demás.
- **`location: local`.** El active-response corre en el agente que originó la alerta
  (DC01), no en el manager de AWS — porque el firewall a tocar está en DC01. Por eso el
  webhook escucha en `127.0.0.1`: quien lo invoca vive en la misma máquina.
- **Separación de privilegios.** El bridge que Wazuh invoca NO tiene permisos de
  firewall; solo hace un POST. Quien ejecuta `netsh` (con admin) es el webhook, un
  proceso aparte. Si el bridge se comprometiera, no puede tocar el firewall directo.
- **`urllib`, no `requests`.** El bridge usa solo librería estándar — una dependencia
  menos que pueda faltar en el entorno del agente.
- **`timeout_allowed: no`.** La expiración la maneja el webhook (Timer de 30 min), no
  Wazuh. Una sola fuente de verdad para el desbloqueo; el bridge solo actúa en `add`.

## Las 3 salvaguardas del webhook (anti auto-DoS)

| # | Salvaguarda | Qué previene |
|---|-------------|--------------|
| 1 | **Allowlist** (DC, gateway, localhost) | Auto-DoS contra infraestructura crítica. Suprime la ACCIÓN, no la detección: una IP protegida igual se alerta. |
| 2 | **Bloqueo temporal** (expira en 30 min) | Falsos positivos legítimos (credencial caché vieja, NAT compartido) se auto-corrigen. |
| 3 | **Validación de input** (`ipaddress`) | Command-injection: se valida que sea una IP real antes de pasarla a `netsh`. |

> Modelo de amenazas: el riesgo del auto-bloqueo no es el spoofing ciego por internet
> (TCP exige completar el handshake), sino el **falso positivo legítimo** y, en
> post-explotación, el spoofing de infra en la LAN. Por eso allowlist + bloqueo temporal.

## Archivos

| Archivo | Ubicación | Rol |
|---------|-----------|-----|
| `webhook.py` | proyecto IDS-IPS / `C:\ids\` en DC01 | El servicio: decide y bloquea (3 salvaguardas) |
| `wazuh_ar_bridge.py` | `ossec-agent\active-response\bin\` | Puente: lee la alerta de stdin, extrae la IP, POST al webhook |
| `ids-block.cmd` | `ossec-agent\active-response\bin\` | Wrapper que Wazuh ejecuta; llama al bridge pasando stdin |

## Config del manager (`/var/ossec/etc/ossec.conf`)

```xml
<command>
  <name>ids-block</name>
  <executable>ids-block.cmd</executable>
  <timeout_allowed>no</timeout_allowed>
</command>

<active-response>
  <command>ids-block</command>
  <location>local</location>
  <rules_id>60204</rules_id>
</active-response>
```

## Verificación

**Unit test del webhook (hecho).** Simulando la llamada de Wazuh con `curl`:

| Caso | Input | Resultado | Salvaguarda probada |
|------|-------|-----------|---------------------|
| IP hostil | `8.8.8.8` | `blocked` + 2 reglas reales en firewall (in/out) | — |
| IP crítica | `10.0.2.10` (DC) | `allowlisted` (alertada, no bloqueada) | #1 allowlist |
| IP repetida | `8.8.8.8` otra vez | `already_blocked` | idempotencia |

La regla de firewall `IDS_Block_8.8.8.8` se confirmó con
`netsh advfirewall firewall show rule name="IDS_Block_8.8.8.8"`.

<!-- ![Unit test webhook](imagenes/webhook-unittest.png) -->

**Prueba de fuego en vivo (pendiente — Semana 3).** El spray real contra DC01 requiere
conectividad atacante(Kali)↔DC01, que es también el prerrequisito de la cadena de
ataque de la Semana 3. Se hará como primer experimento de esa fase: spray -> Wazuh
detecta (60204) -> active-response -> bloqueo automático -> verlo en el SIEM.

## Estado

- [x] `webhook.py` refactorizado con las 3 salvaguardas
- [x] Unit-tested (bloqueo real, allowlist, idempotencia) con evidencia
- [x] Bridge + wrapper `.cmd` desplegados en el agente de DC01
- [x] Config del manager (command + active-response en rule 60204)
- [ ] Prueba de fuego en vivo (spray real) → Semana 3, tras montar la red atacante↔DC01
