#!/bin/bash

# Database connection details
DB_NAME="postgres"
DB_USER="postgres"
DB_HOST="192.168.1.27"
DB_PORT="5432"
SQL_DIR="plugins"  # Directory containing db kit .sql files

# Check if the directory exists
if [[ ! -d "$SQL_DIR" ]]; then
  echo "DB Kit Directory not found: $SQL_DIR"
  exit 1
fi

# Set Image Server IP
export IMAGE_SERVER=$DB_HOST
export PGPASSWORD=""

# Process all .sql scripts in the DB Kit
for sql_file in "$SQL_DIR"/*.sql; do
  # Check if any .sql files exist
  if [[ ! -e "$sql_file" ]]; then
    echo "No .sql files found in $SQL_DIR"
    exit 1
  fi

  echo "Executing $sql_file..."

  # Execute the SQL file using psql
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\set img_server :'IMAGE_SERVER'" -v img_host="$DB_HOST" -f "$sql_file"

  # Check if the command was successful
  if [[ $? -eq 0 ]]; then
    echo "Executed $sql_file successfully."
  else
    echo "Failed to execute $sql_file."
    exit 1
  fi
done

echo "DB Kit executed successfully."
