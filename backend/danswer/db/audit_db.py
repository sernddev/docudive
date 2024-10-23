import asyncio
import contextlib
import json
from datetime import datetime

from danswer.configs.app_configs import AUDIT_URL, AUDIT_ACTIONS
from shared_configs.shared_context import user_id_context
from sqlalchemy import event
from sqlalchemy import inspect
import httpx



from danswer.utils.logger import setup_logger
logger = setup_logger()


# Synchronous wrapper function
def sync_log_changes(mapper, connection, target, operation, audit_stage):
    # Get the primary key column(s) for the target table
    primary_key_columns = [key.name for key in inspect(target).mapper.primary_key]

    primary_key_values = str({key: getattr(target, key) for key in primary_key_columns})

    record_id = json.dumps(primary_key_values) if primary_key_values else None
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(log_changes(mapper, connection, target, operation, audit_stage,record_id))
        else:
            loop.run_until_complete(log_changes(mapper, connection, target, operation, audit_stage,record_id))
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(log_changes(mapper, connection, target, operation, audit_stage,record_id))
        except Exception as ex:
            logger.error(f"Error while auditing: {audit_stage}, ERROR:{ex}")


# Function to log changes to the audit table
async def log_changes(mapper, connection, target, operation, audit_stage,record_id):
    audit_entry = {}
    try:
        table_name = target.__tablename__

        changes = json.dumps({k: str(v) for k, v in target.__dict__.items() if not k.startswith('_')})
        user_id = user_id_context.get() or "unknown"
        audit_entry = {
            "user_id": str(user_id),
            "tablename": table_name,
            "operation": operation,
            "audit_stage": audit_stage,
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat(),
            "changes": changes
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{AUDIT_URL}/log", json=audit_entry)
                response.raise_for_status()  # Raises an error for non-2xx responses
        except Exception as e:
            # Optionally log or handle failures in sending to the audit server
            print(f"Failed to send audit log: {e}")
            logger.error(f"Failed to send audit log: {e}")


    except Exception as ex:
        logger.error(f"Error while auditing: {audit_entry}, ERROR:{ex}")

''' BELOW CHANGES FOR AUDIT TO LOCAL DB
# Function to log changes to the audit table
def log_changes(mapper, connection, target, operation,audit_stage):
    audit_entry = {}
    try:
        table_name = target.__tablename__

        # Get the primary key column(s) for the target table
        primary_key_columns = [key.name for key in inspect(target).mapper.primary_key]

        # Fetch primary key values from the target
        primary_key_values = {key: getattr(target, key) for key in primary_key_columns}

        # Serialize primary key values into a string representation (JSON format)
        record_id = json.dumps(primary_key_values) if primary_key_values else None

        # Get changes in a JSON format, excluding internal SQLAlchemy attributes (those starting with '_')
        changes = json.dumps({k: str(v) for k, v in target.__dict__.items() if not k.startswith('_')})
        user_id = user_id_context.get() or "unknown"
        # Create an AuditLog entry
        audit_entry = {
            "user_id": user_id,
            "tablename": table_name,
            "operation": operation,
            "audit_stage": audit_stage,
            "record_id": record_id,
            "timestamp": datetime.utcnow(),
            "changes": changes
        }

        # Insert directly into the audit_logs table using the connection
        insert_statement = insert(AuditLog).values(**audit_entry)
        connection.execute(insert_statement)
    except Exception as ex:
        logger.error(f"Error while auditing: {audit_entry}, ERROR:{ex}")


# Generic function to add event listeners for all models, excluding AuditLog
def add_audit_listeners(Base):
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ != 'audit_logs':
            # Add event listeners for before insert, update, delete
            event.listen(cls, 'before_insert',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'INSERT', 'before'))
            event.listen(cls, 'before_update',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'UPDATE', 'before'))
            event.listen(cls, 'before_delete',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'DELETE', 'before'))

            # Add event listeners for after insert, update, delete
            event.listen(cls, 'after_insert',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'INSERT', 'after'))
            event.listen(cls, 'after_update',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'UPDATE', 'after'))
            event.listen(cls, 'after_delete',
                         lambda mapper, connection, target: log_changes(mapper, connection, target, 'DELETE', 'after'))


'''

# Generic function to add event listeners for all models, excluding AuditLog
def add_audit_listeners(Base):
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ != 'audit_logs':
            # Add event listeners for before insert, update, delete
            if "BEFORE_INSERT" in AUDIT_ACTIONS:
                event.listen(cls, 'before_insert',
                         lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'INSERT',
                                                                             'before'))
            if "BEFORE_UPDATE" in AUDIT_ACTIONS:
                event.listen(cls, 'before_update',
                         lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'UPDATE',
                                                                             'before'))
            if "BEFORE_DELETE" in AUDIT_ACTIONS:
                event.listen(cls, 'before_delete',
                         lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'DELETE',
                                                                             'before'))

            if "INSERT" in AUDIT_ACTIONS:
                # Add event listeners for after insert, update, delete
                event.listen(cls, 'after_insert',
                             lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'INSERT',
                                                                                 'after'))

            if "UPDATE" in AUDIT_ACTIONS:
                event.listen(cls, 'after_update',
                         lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'UPDATE',
                                                                             'after'))
            if "DELETE" in AUDIT_ACTIONS:
                event.listen(cls, 'after_delete',
                         lambda mapper, connection, target: sync_log_changes(mapper, connection, target, 'DELETE',
                                                                             'after'))

