from ldap3 import Server, Connection, ALL, NTLM
import getpass
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class LDAPResponseModel:
    def __init__(self, is_authenticated=False, error_msg=None, full_name=None, first_name=None, email=None, login_id=None):
        self.is_authenticated = is_authenticated
        self.error_msg = error_msg
        self.full_name = full_name
        self.first_name = first_name
        self.email = email
        self.login_id = login_id

    def __repr__(self):
        return f"LDAPResponseModel(is_authenticated={self.is_authenticated}, error_msg={self.error_msg}, full_name={self.full_name}, first_name={self.first_name}, email={self.email}, login_id={self.login_id})"


class LDAPAuthenticator:
    def __init__(self, server_address, domain):
        self.server_address = server_address
        self.domain = domain
        self.ldap_search_base = self._domain_to_ldap_format(domain)

    def _domain_to_ldap_format(self, domain):
        """Convert a domain like 'int.mydomain.com' into 'DC=int,DC=mydomain,DC=com'."""
        parts = domain.split('.')
        return ','.join([f"DC={part}" for part in parts])

    def authenticate(self, username, password):
        response = LDAPResponseModel(login_id=username)
        try:
            # NTLM format requires DOMAIN\username
            user_dn = f"{self.domain.split('.')[0]}\\{username}"  # 'int' part of 'int.mydomain.com'

            # Create the LDAP server object
            server = Server(self.server_address, get_info=ALL)

            # Create the connection object with NTLM authentication
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM)

            # Attempt to bind (authenticate)
            if conn.bind():
                response.is_authenticated = True

                # Fetch the full name, first name, and email from LDAP
                conn.search(search_base=self.ldap_search_base,
                            search_filter=f"(sAMAccountName={username})",
                            attributes=['cn', 'givenName', 'mail'])

                if conn.entries:
                    response.full_name = conn.entries[0]['cn']
                    response.first_name = conn.entries[0]['givenName']
                    response.email = conn.entries[0]['mail']
            else:
                response.is_authenticated = False
                response.error_msg = conn.result.get('description', 'Authentication failed')

        except Exception as e:
            response.is_authenticated = False
            response.error_msg = str(e)

        return response


def main():
    # Read configuration from the .env file
    ldap_server = "ldap://dc01.int.taqniat.ae"
    domain = "int.taqniat.ae"



    if not ldap_server or not domain:
        print("Error: Missing LDAP_SERVER or DOMAIN in .env file.")
        return

    # Example usage:
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    authenticator = LDAPAuthenticator(ldap_server, domain)
    response = authenticator.authenticate(username, password)

    if response.is_authenticated:
        print(f"Access granted. Welcome, {response.full_name} ({response.email}).")
    else:
        print(f"Access denied. Error: {response.error_msg}")


if __name__ == "__main__":
    main()
