import ldap3
from ldap3 import Server, Connection, ALL, NTLM, SASL, KERBEROS

server = Server('10.129.41.25', port=389, get_info=ALL)
conn = Connection(server, user=r'checkpoint.htb\alex.turner', password='Checkpoint2024!', authentication=NTLM)
conn.open()

# Try to perform a SASL bind with NTLM signing
from ldap3.core.connection import SASL_QUALITY_PROTECTION
try:
    conn.sasl_mechanism = 'NTLM'
    conn.sasl_credentials = ('checkpoint.htb\\alex.turner', 'Checkpoint2024!', None, None, None)
    conn.bind()
    print(f'Bind result: {conn.result}')
except Exception as e:
    print(f'SASL bind failed: {e}')
    # Try simple bind with signing
    try:
        conn2 = Connection(server, user=r'checkpoint.htb\alex.turner', password='Checkpoint2024!', authentication=NTLM, auto_bind=True)
        print(f'Auto bind result: {conn2.result}')
    except Exception as e2:
        print(f'Auto bind failed: {e2}')
