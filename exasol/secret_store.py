import contextlib
import logging
import os
import pathlib
from pathlib import Path
from dataclasses import dataclass
from sqlcipher3 import dbapi2 as sqlcipher
from typing import List, Optional, Union
from inspect import cleandoc


_logger = logging.getLogger(__name__)
TABLE_NAME = "secrets"


class InvalidPassword(Exception):
    """Signal potentially incorrect master password."""


class Secrets:
    def __init__(self, db_file: Path, master_password: str) -> None:
        self.db_file = db_file
        self._master_password = master_password
        self._con = None

    def close(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def connection(self) -> sqlcipher.Connection:
        if self._con is None:
            db_file_found = self.db_file.exists()
            if not db_file_found:
                _logger.info(f"Creating file {self.db_file}")
            self._con = sqlcipher.connect(self.db_file)
            self._use_master_password()
            self._initialize(db_file_found)
        return self._con

    def _initialize(self, db_file_found: bool) -> None:
        if db_file_found:
            self._verify_access()
            return
        _logger.info(f'Creating table "{TABLE_NAME}".')
        with self._cursor() as cur:
            cur.execute(f"CREATE TABLE {TABLE_NAME} (key TEXT, value TEXT PRIMARY KEY)")

    def _use_master_password(self) -> None:
        """
        If database is unencrypted then this method encrypts it.
        If database is already encrypted then this method enables to access the data.
        """
        if self._master_password is not None:
            sanitized = self._master_password.replace("'", "\\'")
            with self._cursor() as cur:
                cur.execute(f"PRAGMA key = '{sanitized}'")

    def _verify_access(self):
        try:
            with self._cursor() as cur:
                cur.execute("SELECT * FROM sqlite_master")
        except sqlcipher.DatabaseError as ex:
            print(f'exception {ex}')
            if str(ex) == "file is not a database":
                raise InvalidPassword(
                    cleandoc(
                    f"""
                    Cannot access
                    database file {self.db_file}.
                    This also happens if master password is incorrect.
                    """)
                ) from ex
            else:
                raise ex

    @contextlib.contextmanager
    def _cursor(self) -> sqlcipher.Cursor:
        cur = self.connection().cursor()
        try:
            yield cur
            self.connection().commit()
        except:
            self.connection().rollback()
            raise
        finally:
            cur.close()

    def save(self, key: str, value: str) -> "Secrets":
        """key represents a system, service, or application"""
        def entry_exists(cur) -> None:
            res = cur.execute(
                f"SELECT * FROM {TABLE_NAME} WHERE key=?",
                [key])
            return res and res.fetchone()

        def update(cur) -> None:
            cur.execute(
                f"UPDATE {TABLE_NAME} SET value=? WHERE key=?",
                [value, key])

        def insert(cur) -> None:
            cur.execute(
                f"INSERT INTO {TABLE_NAME} (key,value) VALUES (?, ?)",
                [key, value])

        with self._cursor() as cur:
            if entry_exists(cur):
                update(cur)
            else:
                insert(cur)
        return self

    def get(self, key: str) -> Optional[List[str]]:
        with self._cursor() as cur:
            res = cur.execute(
                f"SELECT value FROM {TABLE_NAME} WHERE key=?",
                [key])
            row = res.fetchone() if res else None
        return row[0] if row else None
