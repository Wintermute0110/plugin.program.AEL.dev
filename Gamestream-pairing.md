# Pairing with Nvidia Gamestream PC #

We now have the ability to launch PC games through Nvidia gamestreaming. To scan for the available games on your
PC we need to pair with the PC running Geforce Experience and for this we need valid certificates. Unfortunatly at 
the moment we do not have default support in Kodi to do the needed actions with encryption and certificates to make 
a secure connection. So to create the valid certificates and finish up the pairing process you need to do one of 
the following actions.

## 1. Run custom pairing python scripts 
Download the source code for AEL from github and place it on your computer. Make sure you have Python installed and 
the needed libraries, like the OpenSSL. Then go to the /tools folder of the source code.
The script must be called with two parameters, host and path where to store the new certificates.

Example: 
```
>python pair_with_nvidia.py 192.168.1.99 c:\games\gamestream\
```

When started, this tool will show a unique pincode which you need to enter in a dialog on your computer which is running 
Nvidia Geforce Experience. When done correctly it will pair up with that computer and generate certificates needed to 
keep on communicating with the geforce experience computer. These certificates can be used in a Gamestream Launcher when
running AEL in Kodi.

## 2. Use certificates from Moonlight
If you have installed Moonlight as your client for Nvidia Gamestream and you already used that to pair with your Gamestream
server, then you can reuse those certificates. Out of the box the certificates are not yet ready to be used with the AEL scripts.
You will need to have OpenSSL on your computer to transform the private key certificate to the supported format.

Execute the following command with OpenSSL:
```
openssl pkcs8 -topk8 -inform DER -outform PEM -nocrypt -in <MOONLIGHT_KEY_FILE_PATH>.key -out <YOUR_FILE_NAME>.key
```

Copy the new *.key and *.crt to a separate folder. Now you can use these certificate files when creating your launcher in AEL 
in Kodi.