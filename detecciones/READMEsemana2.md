# Detecciones  SIEM en la nube (Semana 2)

Centralización de la telemetría de Active Directory en un SIEM (Wazuh) desplegado en
la nube, con el agente on-prem reportando a través de internet de forma segura.

## Arquitectura: por qué el SIEM vive en la nube

El host local (16 GB RAM) no aguanta DC01 + WKS01 + Wazuh a la vez (Wazuh solo pide
~4 GB y su indexer es pesado). En vez de ahogar la RAM, el SIEM se saca a la nube.
Esto resuelve el límite de memoria y suma un componente cloud real al proyecto.

```
┌────────────────────── INTERNET ────────────────────────┐
|  AWS EC2 (t3.large, Ubuntu 24.04)                      |
│   ┌────────────────────────────────────┐               │
│   │  WAZUH  (manager + indexer + dash) │               │
│   │  Elastic IP fija: 100.60.9.84      │◄─────────┐    │
│   │   Security Group: solo mi IP       │          │    │
│   └────────────────────────────────────┘          │    │
│         ▲ 1) logs cifrados (:1514/:1515) │ 2) dashboard|
└─────────┼─────────────────────────────────────────┼────┘
          │ conexión SALIENTE                       │ (:443)
   ┌──────┼─────────────────────────────────────────┼─────┐
   │  CASA                                          │     │
   │   ┌──┴──────────────────┐        ┌─────────────┴──┐  │
   │   │ DC01 + agente Wazuh │        │Navegador (host)|  │
   │   │ 10.0.2.10           │        └────────────────┘  │
   │   └─────────────────────┘                            │
   └──────────────────────────────────────────────────────┘
```

## Nota sobre el proveedor (Oracle --> AWS)

El plan original era Oracle Cloud (ARM Always Free, 24 GB). Se descartó tras repetidos
errores **"Out of host capacity"** al provisionar la instancia ARM en Monterrey. Se cambeo a **AWS EC2** usando créditos
educativos existentes: capacidad inmediata, sin costo de bolsillo, y AWS pesa
más en vacantes de LATAM. 

## Componentes

| Componente        | Valor                                            |
|-------------------|--------------------------------------------------|
| VM del SIEM       | AWS EC2 `t3.large` (2 vCPU / 8 GB / 30 GB gp3)   |
| SO                | Ubuntu Server 24.04 LTS                          |
| SIEM              | Wazuh 4.9.2 (all-in-one)                         |
| IP pública        | Elastic IP fija `100.60.9.84`                    |
| Agente            | Wazuh Agent 4.9.2 en DC01 (`10.0.2.10`)          |

## Las tres capas de seguridad del canal agente↔nube

| Capa | Qué protege | Cómo |
|------|-------------|------|
| Cifrado AES (1514) | Que nadie lea los logs en tránsito | Nativo del agente Wazuh |
| Enrolamiento con clave (1515) | Que solo mi agente pueda reportar | Token de registro que emite el manager |
| Firewall (Security Group) | Que solo mi tráfico llegue a la VM | Puertos 22/443/1514/1515 restringidos a *My IP* |


## Pasos

1. Lanzar instancia EC2: Ubuntu 24.04, `t3.large`, 30 GiB, par de llaves `.pem`.
   Security Group inicial: solo SSH (22) desde *My IP*.

2. Conectarse por SSH desde WSL (permisos de la llave primero):

   ```bash
   chmod 600 ~/wazuh-AWS-colibripay.pem
   ssh -i ~/wazuh-AWS-colibripay.pem ubuntu@<ip>
   ```

3. Actualizar e instalar Wazuh (all-in-one):

   ```bash
   sudo apt update && sudo apt upgrade -y
   curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh && sudo bash ./wazuh-install.sh -a
   ```

   > El instalador imprime al final el usuario `admin` y una contraseña generada.
   > Las guardamos en un lugar seguro

4. Verificar que el manager está vivo:

   ```bash
   sudo systemctl status wazuh-manager --no-pager   # deberia aparece: active (running)
   ```

5. Asignar una **Elastic IP** y asociarla a la instancia. Fija la IP pública para que
   no cambie al apagar/prender .

6. Abrir puertos en el Security Group, todos restringidos a *My IP*:
   `443` (dashboard), `1514` (eventos del agente), `1515` (enrolamiento del agente).

7. Entrar al dashboard: `https://<ip>` (certificado autofirmado -> continuar).
   Health-check con los 5 checks en verde.
   ![alt text](imagenes/7checkssaludwazuh.png)

8. Instalar el agente en DC01 (PowerShell como administrador). El comando lo genera el
   propio dashboard con la IP del manager embebida:

   ```powershell
   Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.9.2-1.msi -OutFile $env:tmp\wazuh-agent; msiexec.exe /i $env:tmp\wazuh-agent /q WAZUH_MANAGER='<ip>' WAZUH_AGENT_NAME='DC01'
   NET START WazuhSvc
   ```

9. Verificar que DC01 aparece **Active** en el dashboard (Server management -->
   Endpoints Summary).
   ![alt text](imagenes/9DCActivewazuh.png)

   > Si el agente no aparece, tal vez es que faltan abrir los puertos
   > **1514 y 1515** en el Security Group (paso 6). Sin el 1515 el agente nunca
   > completa el enrolamiento.

## Verificación  la detección de punta a punta

Prueba de que el pipeline **funciona**, no solo que se instaló: provocar un login
fallido en DC01 y confirmar que la alerta llega al SIEM en la nube.

```powershell
runas /user:corp\mtorres cmd     # contraseña incorrecta a propósito
```

En el dashboard (Threat Hunting --> DC01 --> Events), aparece la alerta:

| Campo | Valor |
|-------|-------|
| rule.description | Logon Failure - Unknown user or bad password |
| rule.id | 60122 (corresponde al Event ID **4625** de Windows) |
| rule.level | 5 (elevado sobre los logins normales, nivel 3) |
| agent.name | DC01 |

![alt text](imagenes/Verificacionpipeline.png)
La cadena completa que esto valida: GPO de auditoría (Semana 1) --> Windows registra el
4625 --> el agente lo captura --> viaja cifrado --> llega a Wazuh
en AWS --> se correlaciona con la regla 60122 --> aparece en el dashboard en tiempo real.

## Estado al cierre de la Semana 2

- [x] Wazuh desplegado en AWS EC2 (health-check 5/5)
- [x] Elastic IP fija asociada
- [x] Agente en DC01 reportando (**Active**) — arquitectura híbrida on-prem-->cloud
- [x] Detección verificada (4625 --> regla 60122, nivel 5)
- [ ] Sysmon en DC01 (telemetría profunda / 4688 con línea de comando) --> pendiente
- [ ] Integración del IDS propio como active-response --> pendiente

## Higiene de costos (AWS)

- **Apagar (Stop)** la instancia al terminar cada sesión. Con la Elastic IP, al prender
  vuelve en la misma `100.60.9.84` y el agente reconecta solo.
- El disco EBS (~30 GB) sigue cobrando unos centavos aunque esté apagada — normal.
- Alerta de presupuesto configurada por si algo se sale de lo gratis.
