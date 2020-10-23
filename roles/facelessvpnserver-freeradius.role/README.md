One of three roles, used for initial configuration of **faceless.me** VPN IKEv2 server.

- facelessvpnserver-system.role;
- facelessvpnserver-strongswan.role;
- facelessvpnserver-freeradius.role;

This Role install and configure FreeRadius Service on the VPN host.


> It's tested on Linux CENTOS 7 version. 
>  

It's used connection with REST API server for authorization and accounting.
Communication is fullfillend through HTTPS protocol. For security reason
there is special API token for communication with REST API server used.
You should find out this token from Backend Administrator.

Folder certs/vault in Freeradius config folder contains:
- RSA key;
- Certificate of CA, issuing certificates for clients;
- Certificate of host.

Certificates coping from Strongswan Config Folder during installation.
This certificates from VAULT PKI.