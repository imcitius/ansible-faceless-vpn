One of three roles, used for initial configuration of **faceless.me** VPN IKEv2 server.

- facelessvpnserver-system.role;
- facelessvpnserver-strongswan.role;
- facelessvpnserver-freeradius.role;

This Role configure system parameters on the VPN host.


> It's tested on Linux CENTOS 7 version. 
>  

Main goals of this role:

1. Configuring systemctl parameters for IPv4 routing and disabling IPv6.
