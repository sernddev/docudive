from typing import Any

from fastapi import HTTPException
from fastapi_users.password import PasswordHelper
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import getpass

from pydantic import BaseModel
from sqlalchemy.orm import Session

from danswer.auth.schemas import UserRole
from danswer.db.models import User
from danswer.server.settings.models import UserInfoStore
from danswer.server.settings.store import store_user_info
from fastapi_users import exceptions

from danswer.utils.logger import setup_logger

logger = setup_logger()

class LDAPResponseModel(BaseModel):
    is_authenticated:bool= False
    error_msg:str| None = ""
    full_name:str| None = None
    first_name:str| None = None
    email:str| None = None
    login_id:str| None = None

def check_if_any_missing_fields(ldap_user:User):
    missing_fields = []

    if ldap_user.email is None:
        missing_fields.append("email")
    if ldap_user.full_name is None:
        missing_fields.append("full_name")
    if ldap_user.login_id is None:
        missing_fields.append("loginid")
    if ldap_user.first_name is None:
        missing_fields.append("first_name")

    if missing_fields:
        ldap_user.error_msg = f"Missing userinfo ({', '.join(missing_fields)}) from LDAP server"
        return True

    return False


def check_if_user_already_exists(ldap_user:User, db_session: Session):
    user = db_session.query(User).filter(User.email == ldap_user.email,User.is_active==True).first()  # type: ignore
    if user is None:
        return False

    ldap_user.error_msg = f"user already exists in the system"
    return True


class LDAPAuthenticator:
    def __init__(self, server_address, domain,group_dn=None):
        self.server_address = server_address
        self.domain = domain
        self.ldap_search_base = self._domain_to_ldap_format(domain)
        self.group_dn = group_dn


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
                logger.info("user authenticated")

                # Fetch the full name, first name, and email from LDAP
                conn.search(search_base=self.ldap_search_base,
                            search_filter=f"(sAMAccountName={username})",
                            attributes=['cn', 'givenName', 'mail'])

                if conn.entries:
                    entry = conn.entries[0]
                    response.login_id = username
                    response.full_name = entry.cn.value if hasattr(entry, 'cn') else None
                    response.first_name = entry.givenName.value if hasattr(entry, 'givenName') else None
                    response.email = entry.mail.value if hasattr(entry, 'mail') else None
                conn.unbind()
            else:
                response.is_authenticated = False
                response.error_msg = conn.result.get('description', 'Authentication failed')

        except Exception as e:
            response.is_authenticated = False
            response.error_msg = str(e)

        return response

    def get_users_in_group(self, username, password):

        try:
            # NTLM format requires DOMAIN\username
            user_dn = f"{self.domain.split('.')[0]}\\{username}"  # 'int' part of 'int.mydomain.com'

            # Create the LDAP server object
            server = Server(self.server_address, get_info=ALL)

            # Create the connection object with NTLM authentication
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM)

            # Attempt to bind (authenticate)
            if conn.bind():
                #logger.info(self.group_dn)
                logger.info("user authenticated")
                # Search for members of the given group
                conn.search(search_base=self.group_dn,
                            search_filter="(objectClass=group)",
                            search_scope=SUBTREE,
                            attributes=['member'])
                logger.info("group search finished")
                # Extract members from the search result
                if conn.entries:
                    grpEntry=conn.entries[0]
                    members_dn= grpEntry.member if hasattr(grpEntry, 'member') else None
                    if members_dn is None:
                        raise HTTPException(status_code=404, detail="member not found in Group DN")

                    #members_dn = conn.entries[0]['member']
                    user_details = []
                    print(f"Users in the group {self.group_dn}:")

                    # Loop through each member's distinguished name (DN) to fetch their details
                    for member_dn in members_dn:
                        # Search for user details using the member DN
                        conn.search(search_base=member_dn,
                                    search_filter="(objectClass=user)",
                                    search_scope=SUBTREE,
                                    attributes=['sAMAccountName', 'givenName', 'cn', 'mail'])

                        # If user details are found, extract the required attributes
                        if conn.entries:
                            entry = conn.entries[0]
                            user = LDAPResponseModel()
                            user.login_id = entry.sAMAccountName.value if hasattr(entry, 'sAMAccountName') else None
                            user.full_name = entry.cn.value if hasattr(entry, 'cn') else None
                            user.first_name = entry.givenName.value if hasattr(entry, 'givenName') else None
                            user.email = entry.mail.value if hasattr(entry, 'mail') else None
                            user_details.append(user)
                            print(user)
                            logger.info(user)

                    conn.unbind()
                    return user_details
                else:
                    print(f"No users found in the group {self.group_dn}")
                    return []

        except Exception as e:
            print(f"An error occurred while fetching group members: {e}")
            return []
    
    def activate_ldap_users(self,users:list[Any], db_session: Session) -> list[any]:
        users_result =[]
        for user in users:
            if check_if_any_missing_fields(user):
                users_result.append(user)
                continue
            try:
                if check_if_user_already_exists(user,db_session):
                    users_result.append(user)
                    continue
                passwordHelper = PasswordHelper()
                new_user = User(email=user.email,
                                hashed_password=passwordHelper.hash(user.login_id),
                                is_active=True,
                                role=UserRole.BASIC
                                )
                db_session.add(new_user)
                db_session.commit()
            except exceptions.UserAlreadyExists or exceptions.Any:
                db_session.rollback()
                user.error_msg ="user already exists in the system"
                users_result.append(user)
                continue
            try:
                user_key=f"USER_INFO_{user.email}"
                userinfo = UserInfoStore(email= user.email,
                                         loginid= user.login_id,
                                         first_name=user.first_name,
                                         full_name= user.full_name)

                store_user_info(key=user_key,user_info= userinfo)
                users_result.append(user)
            except Any:
                user.error_msg="failed to save in user keystore"
                users_result.append(user)
                continue

        return users_result

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

    authenticator = LDAPAuthenticator(ldap_server, domain, group_dn)
    response = authenticator.authenticate(username, password)

    if response.is_authenticated:
        print(f"Access granted. Welcome, {response.full_name} ({response.email}).")
    else:
        print(f"Access denied. Error: {response.error_msg}")

    authenticator.get_users_in_group(username=username, password=password)


if __name__ == "__main__":
    main()
