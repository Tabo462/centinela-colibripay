# Arquitectura


## Semana 1

### Componentes desplegados

| Atributo            | Valor                                                     |
|---------------------|-----------------------------------------------------------|
| OS                  | Windows Server 2022 Standard (Desktop Experience), eval   |
| Roles               | AD DS + DNS                                               |
| Hipervisor          | VirtualBox (host Windows Home, 16 GB RAM)                 |
| RAM / vCPU / Disco  | 4 GB / 2 / 60 GB                                          |
| FQDN                | `DC01.corp.colibripay.mx`                                 |
| Roles FSMO          | Todos                                                     |

### Direccionamiento

Red NAT de VirtualBox: `10.0.2.0/24`

| Host          | IP           |
|---------------|--------------|
| Gateway (NAT) | `10.0.2.1`   | 
| DC01          | `10.0.2.10`  | 
| WKS01         | `10.0.2.20`  |        
| Wazuh         | `10.0.2.30`  | 


### Dominio

| Atributo                        | Valor                 |
|---------------------------------|-----------------------|
| Dominio                         | `corp.colibripay.mx`  |
| NetBIOS                         | `CORP`                |
| Nivel funcional bosque/dominio  | Windows Server 2016   |

### Pasos

1. Creamos nuestro VM de Windows Server 2022
![alt text](<./imagenes/Screenshot 2026-08-31 100306-1.png>)
2. Entramos a las propiedades de IPv4 de nuestro servidor
![alt text](<./imagenes/Screenshot 2026-09-02 145204.png>)
3. Verificamos que nuestras opciones se guardaron correctamente:
![alt text](<./imagenes/Screenshot 2026-08-31 101541.png>)
4. En la ventana de Server Manager, nos vamos al menuú de "**Manage**" y hacemos *click* en "**Add Roles and Features**"
![alt text](<./imagenes/Screenshot 2026-09-02 150100.png>)
5. En la pestaña de "**Installation Type**", seleccionamos la [**Role Based or feture Installation**]
![alt text](<imagenes/Screenshot 2026-08-31 101755.png>)
6. En la pestaña de  "**Sever selection**" seleccionamos el servidor por *default*
7. En la pestaña de "**Server Roles**" *palomeamos* **Active Directory DOmain Services y **aceptamos** el popup y **aceptamos** los *features*
8. Damos **siguiente** hasta confirmar e instalar

9. Configuramos el Domain Controller **Agregamos un** *new forest* con el *Root domain name* de **corp.colibripay.mx**
10. Terminamos de condigurar el Domain Controller con DNS y reiniciamos.
![alt text](<imagenes/Screenshot 2026-08-31 102856.png>)
![alt text](<imagenes/Screenshot 2026-08-31 103310.png>)
![alt text](<imagenes/Screenshot 2026-08-31 112145.png>)
![alt text](<imagenes/Screenshot 2026-08-31 120241.png>)
11. Verificamos la integridad en el cmd
![alt text](<imagenes/Screenshot 2026-08-31 120753.png>)
![alt text](<imagenes/Screenshot 2026-08-31 124058.png>)
![alt text](<imagenes/Screenshot 2026-08-31 124110.png>)



# Estructura de identidad (OUs, usuarios y cuenta de servicio)

Todo el aprovisionamiento se hizo con **PowerShell** (reproducible y versionable), no por GUI.

**Diseño de OUs:**

```text
corp.colibripay.mx
└── OU=ColibriPay              ← OU raíz propia (todo lo administrado vive aquí)
    ├── OU=Usuarios
    │   ├── OU=IT
    │   ├── OU=Finanzas
    │   └── OU=Soporte
    ├── OU=Grupos
    ├── OU=ServiceAccounts     ← cuentas de servicio, aisladas
    └── OU=Equipos             ← destino de WKS01 (planeado)
```

Se usa una OU raíz propia (`ColibriPay`) en vez de trabajar sobre el dominio, para
poder aplicar GPOs por alcance sin afectar los Domain Controllers ni la
infraestructura del sistema. La OU `ServiceAccounts` se aísla porque las cuentas de
servicio son blanco de alto valor.

12. Creamos la estructura de OUs con PowerShell.
![alt text](<./imagenes/12CrearOUs.png>)

13. Creamos 7 usuarios distribuidos en sus OU de departamento (convención de login:
    inicial + apellido, ej. `mtorres`).
![alt text](<./imagenes/13AñadirUsuarios.png>)

14. Creamos la cuenta de servicio `svc_sql` en la OU `ServiceAccounts` y le
    registramos un **SPN** (`MSSQLSvc/dc01.corp.colibripay.mx:1433`).

    > La contraseña de `svc_sql` es débil **a propósito**: cumple la política de
    > complejidad pero es crackeable. Esto simula una mala configuración común y la
    > vuelve *kerberoasteable* (MITRE **T1558.003**), que es el blanco del ataque de
    > la Semana 3. En un entorno real esta cuenta sería una **gMSA** (contraseña
    > gestionada por AD, aleatoria y rotada sola).
![alt text](imagenes/14RegistrarservicioaSPN.png)
15. Verificamos la capa de identidad. La última consulta es, además, el mismo comando
    que un atacante usa para descubrir blancos de Kerberoasting:

    ```powershell
    Get-ADOrganizationalUnit -Filter * | Select-Object Name, DistinguishedName
    Get-ADUser -Filter * -SearchBase "OU=Usuarios,OU=ColibriPay,DC=corp,DC=colibripay,DC=mx"
    Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties ServicePrincipalName |
        Select-Object SamAccountName, ServicePrincipalName
    ```
![alt text](imagenes/15Kerberroasteable.png)

    Devolvió `svc_sql` con su SPN (blanco plantado) y `krbtgt` (cuenta de sistema del
    KDC, incluida por tener SPN).
    


# **Auditoria Avanzada por GPO**

Por default, Windows registra pocos eventos de seguridad. Se configura una Group Policy Object de auditoria, que se enlaza a la OU ColibriPpay, para que Windows empiece a registrar los eventos que los ataques de la Semana 3 van a generar. Sin estos sensores, el SIEM de la Semana 2 no tendra nada que leer.

## Sensores configurados y qué detecta cada uno:

| Sensor (subcategoría)              | Event ID    | Detecta                          |
|------------------------------------|-------------|----------------------------------|
| Audit Logon                        | 4624 / 4625 | Password spraying, logins        |
| Audit Kerberos Service Ticket Ops  | 4769        | Kerberoasting                    |
| Audit Kerberos Authentication      | 4768        | Peticiones de TGT                |
| Audit User Account Management      | 4720        | Persistencia (cuentas backdoor)  |
| Audit Security Group Management    | 4728 / 4732 | Escalada por grupos              |
| Audit Process Creation             | 4688        | Qué se ejecuta (con línea de cmd)|

16. En **Group Policy Management** (Tools → Group Policy Management), click derecho
    sobre la OU `ColibriPay` → *Create a GPO in this domain, and Link it here* →
    nombre `Auditoria - ColibriPay`.
    ![alt text](<imagenes/16CrearGPO.png>)

17. Click derecho sobre el GPO → *Edit*. En el editor, navegar a:
    Computer Configuration → Policies → Windows Settings → Security Settings →
    Advanced Audit Policy Configuration → Audit Policies. 

18. Activar las subcategorias 
    - **Logon/Logoff → Audit Logon**: Success + Failure. (4624/4625; el 4625 es el
      sensor del password spray y alimenta el IDS.)
    - **Account Logon → Audit Kerberos Service Ticket Operations**: Success + Failure.
      (4769; sensor del Kerberoasting.)
    - **Account Logon → Audit Kerberos Authentication Service**: Success + Failure. (4768)
    - **Account Management → Audit User Account Management**: Success + Failure. (4720)
    - **Account Management → Audit Security Group Management**: Success.
    - **Detailed Tracking → Audit Process Creation**: Success. (4688)
    ![alt text](<17Colocarsubcategory.png>)
19. Incluir linea de comando en el evento 4688 (Audit Process Creation):

Computer Configuration → Policies → Administrative Templates → System →
    Audit Process Creation → Include command line in process creation event  →
    **Enabled**
    > Antes el evento 4688 registraba solo `powershell.exe`
    > Ahora registra `Powershell.exe -enc <base64>`
    > Hicimos que podamos ver los argumentos de una ejecución, pero ahora los argumentos pueden tener informacion sensible y cualqueira con permiso de lectura en los logs puede ver esos argummentos.

20. Forzar el uso de las subcategorias avanzadas:

Computer Configuration → Policies → Windows Settings → Security Settings →
    Local Policies → Security Options → Audit: Force audit policy subcategory
    settings (Windows Vista or later) → **Enabled**.

21. Cerramos el Editor, y abrimos **Powershell** como **administrador** para verificar la configuracion:
    ```powershell
    gpupdate /force
    auditpol /get /category:*
    ```

22. Probamos que el sensor funciona, provocando un login fallido a proposito y confirmamos que se registra el evento 4625 (Logon Failure):

    ```powershell
        runas /user:corp\mtorres cmd     # metemos una contraseña erronea

        Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 5 |
            Format-List TimeCreated, Message
    ```
    ![alt text](<imagenes/22LogonFailure.png>)
    
    > El evento 4625 apareció con `Account Name: mtorres`, `Failure Reason: bad
    > password`, `Status 0xC000006D / Sub Status 0xC0000064` (credencial inválida) y
    > `Logon Type: 2` (interactivo). En la Semana 3, un password spray generará estos
    > 4625 en ráfaga desde una misma IP — el patrón que el SIEM y el IDS detectarán.





