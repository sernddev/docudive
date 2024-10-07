
from ldap3 import Server, Connection, ALL, NTLM
import getpass

def authenticate_ldap_ntlm(server_address, domain, username, password):
    try:
        # NTLM format requires DOMAIN\username
        user_dn = f"{domain}\\{username}"

        # Create the LDAP server object
        server = Server(server_address, get_info=ALL)
        print(f"Server connection details - Host: {server.host}, LDAP: {server.name}, Port: {server.port}")
        print("Connecting.....")

        # Create the connection object with NTLM authentication
        conn = Connection(server, user=user_dn, password=password, authentication=NTLM)

        # Attempt to bind (authenticate)
        if conn.bind():
            print(f"Authentication successful ")
            
            # Fetch the full name or first name from LDAP
            conn.search(search_base=f"DC=int,DC=taqniat,DC=ae", 
                        search_filter=f"(sAMAccountName={username})", 
                        attributes=['cn', 'givenName'])
            
            if conn.entries:
                full_name = conn.entries[0]['cn']
                first_name = conn.entries[0]['givenName']
                print(f"Welcome: {full_name}")
                print(f"First Name: {first_name}")
            return True
        else:
            print(f"Authentication failed: {conn.result}")
            return False

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


# Example usage:
ldap_server = 'ldap://dc01.int.taqniat.ae'
domain = 'int.taqniat.ae'  # Domain name

username = input("Enter username: ")
password = getpass.getpass("Enter password: ")

is_authenticated = authenticate_ldap_ntlm(ldap_server, domain, username, password)

if is_authenticated:
    print("Access granted.")
else:
    print("Access denied.")

