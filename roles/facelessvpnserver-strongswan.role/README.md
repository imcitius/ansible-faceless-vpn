One of three roles, used for initial configuration of **faceless.me** VPN IKEv2 server.

- facelessvpnserver-system.role;
- facelessvpnserver-strongswan.role;
- facelessvpnserver-freeradius.role;

This Role install and configure Strongswan Service on the VPN host.


> It's tested on Linux CENTOS 7 version. 
>  

This configurations is prepared for EAP-TLS IKEv2 connections. There are
two profiles in ipsec.conf - one for IOS devices and one for another OS.

Certificates for this VPN host is gotten from VAULT PKI CA during
initial installation. 

Backend for this Strongswan installation is Freeradius on the same
server. All connection attempts in case of good client certificate
authenticate/authorize on Freradius. Using 1812/1813 UDP ports
on localhost.

On files folder of this Ansible role you can find python script - 
**get_vault_certificate.py**. This script get certificate from
VAULT PKI CA for VPN IKEv2 server.
