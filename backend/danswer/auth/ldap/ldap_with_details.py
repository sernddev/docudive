from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import getpass


class LDAPResponseModel:
    def __init__(self, is_authenticated=False, error_msg=None, full_name=None, first_name=None, email=None,
                 login_id=None):
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

    def authenticate(self, username, password) -> LDAPResponseModel:
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
                    entry = conn.entries[0]
                    response.full_name = entry.cn.value if hasattr(entry, 'cn') else None
                    response.first_name = entry.givenName.value if hasattr(entry, 'givenName') else None
                    response.email = entry.mail.value if hasattr(entry, 'mail') else None
            else:
                response.is_authenticated = False
                response.error_msg = conn.result.get('description', 'Authentication failed')

        except Exception as e:
            response.is_authenticated = False
            response.error_msg = str(e)

        return response

    def get_users_in_group(self, username, password, group_dn):
        try:
            # NTLM format requires DOMAIN\username
            user_dn = f"{self.domain.split('.')[0]}\\{username}"  # 'int' part of 'int.mydomain.com'

            # Create the LDAP server object
            server = Server(self.server_address, get_info=ALL)

            # Create the connection object with NTLM authentication
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM)

            # Attempt to bind (authenticate)
            if conn.bind():
                # Search for members of the given group
                conn.search(search_base=group_dn,
                            search_filter="(objectClass=group)",
                            search_scope=SUBTREE,
                            attributes=['member'])

                # Extract members from the search result
                if conn.entries:
                    members_dn = conn.entries[0]['member']
                    user_details = []
                    print(f"Users in the group {group_dn}:")

                    # Loop through each member's distinguished name (DN) to fetch their details
                    for member_dn in members_dn:
                        # Search for user details using the member DN
                        conn.search(search_base=member_dn,
                                    search_filter="(objectClass=user)",
                                    search_scope=SUBTREE,
                                    attributes=['sAMAccountName', 'givenName', 'cn', 'mail'])

                        # If user details are found, extract the required attributes
                        if conn.entries:
                            user_info = {
                                'sAMAccountName': str(conn.entries[0]['sAMAccountName']),
                                'first_name': str(conn.entries[0]['givenName']),
                                'full_name': str(conn.entries[0]['cn']),
                                'email': str(conn.entries[0]['mail']) if 'mail' in conn.entries[0] else 'N/A'
                            }
                            user_details.append(user_info)
                            print(user_info)

                    return user_details
                else:
                    print(f"No users found in the group {group_dn}")
                    return []

        except Exception as e:
            print(f"An error occurred while fetching group members: {e}")
            return []
    def get_users_in_group_1(self, username, password, group_dn):
        try:
            # NTLM format requires DOMAIN\username
            user_dn = f"{self.domain.split('.')[0]}\\{username}"  # 'int' part of 'int.mydomain.com'

            # Create the LDAP server object
            server = Server(self.server_address, get_info=ALL)

            # Create the connection object with NTLM authentication
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM)

            # Attempt to bind (authenticate)
            if conn.bind():

                # Fetch the full name, first name, and email from LDAP
                conn.search(search_base=self.ldap_search_base,
                            search_filter=f"(sAMAccountName={username})",
                            attributes=['cn', 'givenName', 'mail'])

                # Search for members of the given group
                conn.search(search_base=group_dn,
                            search_filter="(objectClass=group)",
                            search_scope=SUBTREE,
                            attributes=['member'])

                # Extract members from the search result
                if conn.entries:
                    members = conn.entries[0]['member']
                    print(f"Users in the group {group_dn}:")
                    for member in members:
                        print(member)
                    return members
                else:
                    print(f"No users found in the group {group_dn}")
                    return []

        except Exception as e:
            print(f"An error occurred while fetching group members: {e}")
            return []


def main():
    # Read configuration from the .env file
    ldap_server = "ldap://dc01.int.taqniat.ae"
    domain = "int.taqniat.ae"
    group_dn = "CN=SpectraUsers,OU=SpectraAI,DC=int,DC=taqniat,DC=ae"

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

    authenticator.get_users_in_group(username=username, password=password, group_dn=group_dn)


if __name__ == "__main__":
    main()
