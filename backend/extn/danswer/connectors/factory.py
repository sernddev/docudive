from danswer.configs.constants import DocumentSource
from extn.danswer.connectors.confluence.perm_sync import confluence_update_db_group
from extn.danswer.connectors.confluence.perm_sync import confluence_update_index_acl


CONNECTOR_PERMISSION_FUNC_MAP = {
    DocumentSource.CONFLUENCE: (confluence_update_db_group, confluence_update_index_acl)
}
