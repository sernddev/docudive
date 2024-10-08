from abc import ABC
from abc import abstractmethod
from typing import IO

from sqlalchemy.orm import Session

from danswer.configs.constants import FileOrigin
from danswer.db.models import PGFileStore
from danswer.db.pg_file_store import create_populate_lobj
from danswer.db.pg_file_store import delete_lobj_by_id
from danswer.db.pg_file_store import delete_pgfilestore_by_file_name
from danswer.db.pg_file_store import get_pgfilestore_by_file_name
from danswer.db.pg_file_store import read_lobj
from danswer.db.pg_file_store import upsert_pgfilestore
from pathlib import Path
from danswer.configs.app_configs import FILE_SERVER_PATH
from danswer.configs.app_configs import DEFAULT_STORE
import io



class FileStore(ABC):
    """
    An abstraction for storing files and large binary objects.
    """

    @abstractmethod
    def save_file(
        self,
        file_name: str,
        content: IO,
        display_name: str | None,
        file_origin: FileOrigin,
        file_type: str,
        file_metadata: dict | None = None,
    ) -> None:
        """
        Save a file to the blob store

        Parameters:
        - connector_name: Name of the CC-Pair (as specified by the user in the UI)
        - file_name: Name of the file to save
        - content: Contents of the file
        - display_name: Display name of the file
        - file_origin: Origin of the file
        - file_type: Type of the file
        """
        raise NotImplementedError

    @abstractmethod
    def read_file(
        self, file_name: str, mode: str | None, use_tempfile: bool = False
    ) -> IO:
        """
        Read the content of a given file by the name

        Parameters:
        - file_name: Name of file to read
        - mode: Mode to open the file (e.g. 'b' for binary)
        - use_tempfile: Whether to use a temporary file to store the contents
                        in order to avoid loading the entire file into memory

        Returns:
            Contents of the file and metadata dict
        """

    @abstractmethod
    def delete_file(self, file_name: str) -> None:
        """
        Delete a file by its name.

        Parameters:
        - file_name: Name of file to delete
        """


class PostgresBackedFileStore(FileStore):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_file(
        self,
        file_name: str,
        content: IO,
        display_name: str | None,
        file_origin: FileOrigin,
        file_type: str,
        file_metadata: dict | None = None,
    ) -> None:
        try:
            # The large objects in postgres are saved as special objects can be listed with
            # SELECT * FROM pg_largeobject_metadata;
            obj_id = create_populate_lobj(content=content, db_session=self.db_session)
            upsert_pgfilestore(
                file_name=file_name,
                display_name=display_name or file_name,
                file_origin=file_origin,
                file_type=file_type,
                lobj_oid=obj_id,
                db_session=self.db_session,
                file_metadata=file_metadata,
            )
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise

    def read_file(
        self, file_name: str, mode: str | None = None, use_tempfile: bool = False
    ) -> IO:
        file_record = get_pgfilestore_by_file_name(
            file_name=file_name, db_session=self.db_session
        )
        return read_lobj(
            lobj_oid=file_record.lobj_oid,
            db_session=self.db_session,
            mode=mode,
            use_tempfile=use_tempfile,
        )

    def read_file_record(self, file_name: str) -> PGFileStore:
        file_record = get_pgfilestore_by_file_name(
            file_name=file_name, db_session=self.db_session
        )

        return file_record

    def delete_file(self, file_name: str) -> None:
        try:
            file_record = get_pgfilestore_by_file_name(
                file_name=file_name, db_session=self.db_session
            )
            delete_lobj_by_id(file_record.lobj_oid, db_session=self.db_session)
            delete_pgfilestore_by_file_name(
                file_name=file_name, db_session=self.db_session
            )
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise

class DiskBackedFileStore(FileStore):
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.file_storage_directory = Path("FILES")
        self.file_storage_directory.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        file_name: str,
        content: IO,
        display_name: str | None,
        file_origin: FileOrigin,
        file_type: str,
        file_metadata: dict | None = None,
    ) -> None:
        try:
            # Optimize by reducing redundant operations and handling larger files efficiently
            file_path = self.file_storage_directory / file_name

            # Encrypt the content directly and write it to disk
            with open(file_path, "wb") as f:
                for chunk in iter(lambda: content.read(4096), b''):  # Read in chunks to handle large files
                    f.write(chunk)

            # Save file metadata and reference in the database
            upsert_pgfilestore(
                file_name=file_name,
                display_name=display_name or file_name,
                file_origin=file_origin,
                file_type=file_type,
                lobj_oid=0,  # No large object, store file on disk
                db_session=self.db_session,
                file_metadata=file_metadata,
            )
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise

    def read_file(
        self, file_name: str, mode: str | None = "rb", use_tempfile: bool = False
    ) -> IO:

        file_path = self.file_storage_directory / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_name} not found on disk.")

        content = io.BytesIO()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b''):  # Read in 4KB chunks
                content.write(chunk)

            # Move the pointer to the beginning of the BytesIO object
        content.seek(0)

        return content

    def read_file_record(self, file_name: str) -> PGFileStore:
        file_record = get_pgfilestore_by_file_name(
            file_name=file_name, db_session=self.db_session
        )
        return file_record

    def delete_file(self, file_name: str) -> None:
        try:
            file_path = self.file_storage_directory / file_name
            if file_path.exists():
                file_path.unlink()  # Remove the file from disk

            # Delete the file record from the database
            delete_pgfilestore_by_file_name(
                file_name=file_name, db_session=self.db_session
            )
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise

def get_default_file_store(db_session: Session) -> FileStore:
    if DEFAULT_STORE=="DB":
        return PostgresBackedFileStore(db_session=db_session)
    else:
        return DiskBackedFileStore(db_session=db_session)
