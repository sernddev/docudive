from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, TIMESTAMP, create_engine
from sqlalchemy.exc import OperationalError
from databases import Database
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import List
import asyncio
from sqlalchemy.sql import func
from typing import Optional
import os
# Setup logging
logging.basicConfig(filename='audit.log', level=logging.INFO, format='%(asctime)s %(message)s')

# FastAPI app initialization
app = FastAPI()

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')#"postgresql://postgres:postgres@db:5432/audit_db"

# Initialize the Database and MetaData objects
database = Database(DATABASE_URL)
metadata = MetaData()

'''
# Define the audit_logs table
audit_logs_table = Table(
    "audit_logs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(50), nullable=False),
    Column("tablename", String(50), nullable=False),
    Column("operation", String(10), nullable=False),  # INSERT, UPDATE, DELETE
    Column("audit_stage", String(50), nullable=True),
    Column("record_id", Text, nullable=False),        # Use UUID if your primary keys are UUIDs
    Column("timestamp", TIMESTAMP, server_default="CURRENT_TIMESTAMP"),
    Column("changes", Text, nullable=True)
)
'''

audit_logs_table = Table(
    "audit_logs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(50), nullable=False),
    Column("tablename", String(50), nullable=False),
    Column("operation", String(10), nullable=False),  # INSERT, UPDATE, DELETE
    Column("audit_stage", String(50), nullable=True),
    Column("record_id", Text, nullable=False),  # Use UUID if your primary keys are UUIDs
    Column("timestamp", TIMESTAMP, server_default=func.now()),  # Use func.now() for the default timestamp
    Column("changes", Text, nullable=True)
)

# Batch processing configuration
BATCH_SIZE = 5  # Number of logs to process in a batch
BATCH_INTERVAL = 5  # Interval in seconds to flush the batch

# In-memory queue for storing audit logs
audit_queue = []


class AuditEntry(BaseModel):
    user_id: str
    tablename: str
    operation: str
    audit_stage: Optional[str] = None
    record_id: str
    timestamp: Optional[datetime] = None
    changes: Optional[str] = None


def create_audit_logs_table():
    """
    Create the audit_logs table if it does not exist.
    """
    try:
        # Create a database engine
        engine = create_engine(DATABASE_URL)
        # Connect to the database
        with engine.connect() as connection:
            # Create the table if it doesn't exist
            if not engine.dialect.has_table(connection, "audit_logs"):
                metadata.create_all(engine, tables=[audit_logs_table])
                logging.info("Table 'audit_logs' created successfully.")
            else:
                logging.info("Table 'audit_logs' already exists.")
    except OperationalError as e:
        logging.error(f"Database connection failed: {e}")


@app.on_event("startup")
async def startup():
    # Create the audit_logs table if it does not exist
    create_audit_logs_table()

    # Connect to the database on startup
    await database.connect()

    # Start background task for processing the audit queue
    asyncio.create_task(process_audit_queue())


@app.on_event("shutdown")
async def shutdown():
    # Disconnect from the database on shutdown
    await database.disconnect()


@app.post("/log")
async def log_audit(entry: AuditEntry, background_tasks: BackgroundTasks):
    # Log to file immediately
    logging.info(
        f"Table: {entry.tablename}, Operation: {entry.operation}, Stage: {entry.audit_stage}, Changes: {entry.changes}")

    # Add to the audit queue for batch processing
    audit_queue.append(entry.dict())

    # Return response immediately
    return {"message": "Audit log queued successfully"}


async def process_audit_queue():
    while True:
        # Check if there are enough logs to process
        if len(audit_queue) >= BATCH_SIZE:
            # Get the first BATCH_SIZE items from the queue
            batch = [audit_queue.pop(0) for _ in range(BATCH_SIZE)]

            # Insert the batch into the database
            try:
                query = insert(audit_logs_table).values(batch)
                await database.execute(query)
                logging.info(f"Inserted batch of {len(batch)} audit logs into the database.")
            except Exception as e:
                logging.error(f"Failed to insert batch into the database: {e}")

        # Wait for the specified interval before checking again
        await asyncio.sleep(BATCH_INTERVAL)

