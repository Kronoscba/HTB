import ldap3
import json

server = ldap3.Server('10.129.41.25', port=636, use_ssl=True, get_info=ldap3.ALL)
conn = ldap3.Connection(server, user='checkpoint.htb\\alex.turner', password='Checkpoint2024!', authentication=ldap3.NTLM, auto_bind=True)

base_dn = 'DC=checkpoint,DC=htb'

groups_to_check = ['Remote Management Users', 'BackupAccess', 'IT-Staff', 'DevTeam', 'Engineering-Staff', 'Domain Admins', 'Administrators', 'Backup Operators', 'DnsAdmins']

for group in groups_to_check:
    conn.search(
        search_base=base_dn,
        search_filter=f'(&(objectClass=group)(cn={group}))',
        attributes=['cn', 'member']
    )
    for entry in conn.entries:
        cn = str(entry.cn)
        members = [str(m).split(',')[0].split('=')[1] for m in entry.member] if entry.member else []
        print(f'\n[*] Group: {cn}')
        for m in members:
            print(f'    - {m}')

print('\n\n[*] Checking delegation settings for all users...')
conn.search(
    search_base=base_dn,
    search_filter='(&(objectClass=user)(!(objectClass=computer)))',
    attributes=['cn', 'msDS-AllowedToDelegateTo', 'msDS-AllowedToActOnBehalfOfOtherIdentity', 'servicePrincipalName']
)
for entry in conn.entries:
    cn = str(entry.cn)
    deleg = str(entry.msDS-AllowedToDelegateTo) if entry.msDS-AllowedToDelegateTo else None
    rbcd = str(entry.msDS-AllowedToActOnBehalfOfOtherIdentity) if entry.msDS-AllowedToActOnBehalfOfOtherIdentity else None
    spn = str(entry.servicePrincipalName) if entry.servicePrincipalName else None
    if deleg or rbcd or spn:
        print(f'\n[!] User: {cn}')
        if deleg: print(f'    AllowedToDelegateTo: {deleg}')
        if rbcd: print(f'    RBCD: {rbcd}')
        if spn: print(f'    SPN: {spn}')

print('\n\n[*] Checking alex.turner details...')
conn.search(
    search_base=base_dn,
    search_filter='(&(objectClass=user)(sAMAccountName=alex.turner))',
    attributes=['cn', 'memberOf', 'description', 'info', 'profilePath', 'scriptPath', 'homeDirectory', 'userAccountControl', 'servicePrincipalName']
)
for entry in conn.entries:
    print(f'  CN: {entry.cn}')
    if entry.memberOf:
        for m in entry.memberOf:
            print(f'  MemberOf: {m.split(",")[0].split("=")[1]}')
    if entry.description: print(f'  Description: {entry.description}')
    if entry.info: print(f'  Info: {entry.info}')
    if entry.profilePath: print(f'  ProfilePath: {entry.profilePath}')
    if entry.scriptPath: print(f'  ScriptPath: {entry.scriptPath}')
    if entry.homeDirectory: print(f'  HomeDirectory: {entry.homeDirectory}')
    if entry.servicePrincipalName: print(f'  SPN: {entry.servicePrincipalName}')

conn.unbind()
