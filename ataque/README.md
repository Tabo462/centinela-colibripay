# Ataque y detección (Purple) -- Semana 3

Cadena de ataque contra el dominio `corp.colibripay.mx`, ejecutada desde Kali y
emparejada con su detección en el SIEM. El entregable central es la **matriz
ataque↔detección**: por cada técnica, el comando real, lo que disparó en Wazuh (o el
gap), y la evidencia.

## Entorno del ataque

- **Atacante:** Kali (WSL) en `192.168.0.105`.
- **Objetivo:** DC01 (`192.168.0.130`), dominio `corp.colibripay.mx`.
- **Red:** adaptador Bridged de VirtualBox (Kali y DC01 en el mismo segmento L2).
  > Nota de diseño: se intentó primero una red Host-Only aislada + WSL mirrored, pero
  > el modo mirrored no enruta hacia los adaptadores Host-Only de VirtualBox. Se
  > pivoteó a Bridged por confiabilidad. En producción el laboratorio vulnerable iría
  > en una VLAN aislada; aquí se apaga DC01 fuera de las pruebas.

## Matriz ataque↔detección

| # | Técnica | MITRE | Comando (Kali) | Detección (Wazuh) | Evidencia |
|---|---------|-------|----------------|-------------------|-----------|
| 1 | Password spraying | T1110.003 | `nxc smb 192.168.0.130 -u mtorres -p <lista>` | Regla **60204** "Multiple Windows Logon Failures" (nivel 10), compuesta de 4625/60122 | `PasswordSpray/` |
| 2 | Kerberoasting | T1558.003 | `nxc ldap ... --kerberoasting` + `hashcat -m 13100` | Regla **custom 100200** (nivel 12): 4769 + RC4 (0x17) a cuenta de servicio | `Kerberoasting/` |

---

## Par 1 -- Password spraying → detección 60204

**Ataque.** Desde Kali, varios intentos de autenticación SMB contra `mtorres` con
contraseñas incorrectas:
```bash
nxc smb 192.168.0.130 -u mtorres -p 'Otoño2024' 'Verano2024' 'Password1' 'Colibri123' 'Hola2024' 'Qwerty123' 'Admin123' 'Lab2024'
```
![alt text](<PasswordSpray/Kali Password Spray.png>)
![alt text](<PasswordSpray/Wazuh Attack Spray.png>)
Resultado: 8 fallos de logon (evento **4625**) en segundos desde la misma IP.

**Detección.** El SIEM generó la alerta compuesta **60204** "Multiple Windows Logon
Failures" (nivel 10), que agrega varios 4625 individuales (60122) en una ventana de
tiempo. Esa agregación es la clave: no se alerta por un fallo aislado (que sería un
typo legítimo), sino por el *patrón* de fuerza bruta.

**Integración del IDS (SOAR-lite).** Este par está conectado a la respuesta
automatizada: la 60204 debía disparar el active-response → el IDS propio bloquea la IP.
La detección y la respuesta (webhook) se verificaron por separado; el dispatch del
active-response quedó documentado como *known issue* (ver `/ids-integracion`).

---

## Par 2 -- Kerberoasting → detección custom 100200

**Ataque.** Autenticado como un usuario cualquiera (`mtorres`, sin privilegios), se
pidió el TGS de la cuenta de servicio `svc_sql` (que tiene SPN) y se crackeó offline:
```bash
nxc ldap 192.168.0.130 -u mtorres -p 'Lab2024Pass!' --kerberoasting kerb_hashes.txt
hashcat -m 13100 kerb_hashes.txt /usr/share/wordlists/rockyou.txt
```
Resultado: hash `$krb5tgs$23$*svc_sql$...` (el `$23$` = RC4) → crackeado a **`Password1`**
en 1 segundo.

![alt text](<Kerberoasting/Kali Kerberoasting.png>)
![alt text](<Kerberoasting/Wazuh Kerberoasting.png>)
**Detección -- regla custom (detection engineering).** Wazuh **no alerta** de los 4769
por defecto (un DC genera cientos legítimos por hora). Para distinguir el ataque del
ruido se escribió una **regla propia** en `local_rules.xml`:
```xml
<rule id="100200" level="12">
  <if_group>windows</if_group>
  <field name="win.system.eventID">^4769$</field>
  <field name="win.eventdata.ticketEncryptionType">^0x17$</field>
  <description>Posible Kerberoasting: TGS con cifrado RC4 debil a cuenta de servicio</description>
  <mitre><id>T1558.003</id></mitre>
</rule>
```
La señal no es "hubo un 4769", es **"4769 + RC4 (0x17) a una cuenta de servicio"**. La
alerta disparó en vivo (nivel 12) con `serviceName: svc_sql`.

**Mitigación de raíz.** gMSA -- contraseña gestionada por AD (aleatoria, 240 caracteres,
rotada sola). Contra una gMSA no hay contraseña débil que crackear.

---

## Gaps de detección (parte del entregable)

Documentar lo que NO se detecta es pensamiento de analista senior:

- **RC4 también aparece en tráfico legítimo** (clientes/apps legacy). La regla 100200
  es un *indicador*, no prueba --
 puede dar falsos positivos. La versión de alta
  confianza correlacionaría RC4 + volumen anómalo (un usuario pidiendo muchos SPN en
  poco tiempo) + exclusión de cuentas de máquina (`$`).
- **El crackeo del Kerberoasting es invisible** al DC (ocurre offline en la máquina del
  atacante). Solo la petición del ticket (4769) deja rastro.
- **Active-response dispatch:** la contención automática del Par 1 quedó como known
  issue de propagación del comando al agente (ver `/ids-integracion`).