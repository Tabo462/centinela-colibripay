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

9. Configuramos el Domain Controller **Agregamos un** *new forest* con el *Root domain name* de **corp.colibri.mx**
10. Terminamos de condigurar el Domain Controller con DNS y reiniciamos.
![alt text](<imagenes/Screenshot 2026-08-31 102856.png>)
![alt text](<imagenes/Screenshot 2026-08-31 103310.png>)
![alt text](<imagenes/Screenshot 2026-08-31 112145.png>)
![alt text](<imagenes/Screenshot 2026-08-31 120241.png>)
11. Verificamos la integridad en el cmd
![alt text](<imagenes/Screenshot 2026-08-31 120753.png>)
![alt text](<imagenes/Screenshot 2026-08-31 124058.png>)
![alt text](<imagenes/Screenshot 2026-08-31 124110.png>)


