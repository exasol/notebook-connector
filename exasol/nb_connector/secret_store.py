from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Iterable
from inspect import cleandoc
from pathlib import Path
from typing import (
    Any,
)

import tenacity
from sqlcipher3 import dbapi2 as sqlcipher  # type: ignore
from tenacity import (
    retry_if_exception_message,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

LOG = logging.getLogger(__name__)
TABLE_NAME = "secrets"


class InvalidPassword(Exception):
    """Signal potentially incorrect master password."""


class Secrets:
    def __init__(self, db_file: Path, master_password: str) -> None:
        self.db_file = db_file
        self._master_password = master_password
        self._lock = threading.Lock()
        self._cache: dict[int, sqlcipher.Connection] = {}
        self._initialize()

    def _initialize(self) -> None:
        if self.db_file.exists():
            self._verify_access()
            return
        LOG.info('Creating file %s and table "%s"', self.db_file, TABLE_NAME)
        self._execute(f"CREATE TABLE {TABLE_NAME} (key TEXT PRIMARY KEY, value TEXT)")

    def connection(self) -> sqlcipher.Connection:
        """
        SQLite allows a connection to be used only by a single thread.  In
        multi-threaded scenarios we therefore need to maintain a connection
        pool, containing a separate connection for each thread.

        Potential exceptions:
        sqlcipher3.dbapi2.IntegrityError: UNIQUE constraint failed: secrets.key
        sqlcipher3.dbapi2.OperationalError: database is locked
        """
        thread_id = threading.get_ident()
        with self._lock:
            if con := self._cache.get(thread_id):
                return con
            con = sqlcipher.connect(self.db_file)  # pylint: disable=E1101
            self._cache[thread_id] = con
        with self._cursor(con) as cur:
            self._use_master_password(cur)
        return con

    def close(self) -> None:
        thread_id = threading.get_ident()
        with self._lock:
            con = self._cache.pop(thread_id, None)
        if con:
            con.close()

    def close_all(self) -> None:
        """
        Close all connections in cache and empty cache.
        """
        with self._lock:
            for con in self._cache.values():
                con.close()
            self._cache = {}

    def __del__(self) -> None:
        self.close()

    def _use_master_password(self, cur: sqlcipher.Cursor) -> None:
        """
        If database is unencrypted then this method encrypts it.
        If database is already encrypted then this method enables to access the data.
        """
        if self._master_password is not None:
            sanitized = self._master_password.replace("'", "\\'")
            cur.execute(f"PRAGMA key = '{sanitized}'")

    def _verify_access(self) -> None:
        try:
            self._execute("SELECT * FROM sqlite_master")
        # fmt: off
        except (sqlcipher.DatabaseError) as ex:  # pylint: disable=E1101
            # fmt: on
            LOG.error("Exception %s", ex)
            if str(ex) == "file is not a database":
                raise InvalidPassword(
                    cleandoc(
                        f"""
                    Cannot access
                    database file {self.db_file}.
                    This also happens if master password is incorrect.
                    """
                    )
                ) from ex
            raise

    # If the database is locked, wait exponentially min. 0.1 seconds, max. 5
    # seconds (50 * 0.1) and retry executing the current SQL statement.
    @tenacity.retry(
        retry=(
            retry_if_exception_type(sqlcipher.OperationalError)
            | retry_if_exception_message("database is locked")
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=50),
    )
    def _execute(
        self, stmt: str, args: list[Any] | None = None, cur: sqlcipher.Cursor = None
    ) -> None:
        """
        cur.execute() returns the same object on which execute() was
        called. To avoid lifetime issues of the cursor object, we dont't
        return it. This forces the caller to inject the cursor with the correct
        lifetime into this method.
        """
        with contextlib.ExitStack() as stack:
            cur = cur or stack.enter_context(self._cursor())
            cur.execute(stmt, args or [])

    @contextlib.contextmanager
    def _cursor(
        self,
        con: sqlcipher.Connection | None = None,
    ) -> sqlcipher.Cursor:
        con = con or self.connection()
        cur = con.cursor()
        try:
            yield cur
            con.commit()
        except:
            con.rollback()
            raise
        finally:
            cur.close()

    def save(self, key: str | CKey, value: str) -> Secrets:
        """key represents a system, service, or application"""
        key = key.name if isinstance(key, CKey) else key
        stmt = (
            f"INSERT INTO {TABLE_NAME} (key,value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value=?"
        )
        self._execute(stmt, [key, value, value])
        return self

    def get(self, key: str | CKey, default_value: str | None = None) -> str | None:
        key = key.name if isinstance(key, CKey) else key
        with self._cursor() as cur:
            self._execute(f"SELECT value FROM {TABLE_NAME} WHERE key=?", [key], cur=cur)
            row = cur.fetchone()
        return row[0] if row else default_value

    def __getattr__(self, key) -> str:
        val = self.get(key)
        if val is None:
            raise AttributeError(f'Unknown key "{key}"')
        return val

    def __getitem__(self, item) -> str:
        val = self.get(item)
        if val is None:
            raise AttributeError(f'Unknown key "{item}"')
        return val

    def keys(self) -> Iterable[str]:
        """Iterator over keys akin to dict.keys()"""
        with self._cursor() as cur:
            self._execute(f"SELECT key FROM {TABLE_NAME}", cur=cur)
            yield from (row[0] for row in cur)

    def values(self) -> Iterable[str]:
        """Iterator over values akin to dict.values()"""
        with self._cursor() as cur:
            self._execute(f"SELECT value FROM {TABLE_NAME}", cur=cur)
            yield from (row[0] for row in cur)

    def items(self) -> Iterable[tuple[str, str]]:
        """Iterator over keys and values akin to dict.items()"""
        with self._cursor() as cur:
            self._execute(f"SELECT key, value FROM {TABLE_NAME}", cur=cur)
            yield from ((row[0], row[1]) for row in cur)

    def remove(self, key: str | CKey) -> None:
        """
        Deletes the entry with the specified key if it exists.  Doesn't
        raise any exception if the key doesn't exist.
        """
        key = key.name if isinstance(key, CKey) else key
        self._execute(f"DELETE FROM {TABLE_NAME} WHERE key=?", [key])
