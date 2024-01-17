import re

import pytest

from exasol.language_container_activation import (
    ACTIVATION_KEY_PREFIX,
    get_activation_sql,
)


def test_get_activation_sql(secrets):
    secrets.save(
        ACTIVATION_KEY_PREFIX + "_lang1",
        "ALTER SESSION SET SCRIPT_LANGUAGES='"
        "R=builtin_r JAVA=builtin_java PYTHON3=builtin_python3 "
        "FIRST_LANG=localzmq+protobuf:///bfs_path1?"
        "lang=python#/buckets/bfs_path1/exaudf/exaudfclient_py3';",
    )

    secrets.save("some_other_key", "some_other_value")

    secrets.save(
        ACTIVATION_KEY_PREFIX + "_lang2",
        "ALTER SESSION SET SCRIPT_LANGUAGES='"
        "R=builtin_r JAVA=builtin_java PYTHON3=builtin_python3 "
        "SECOND_LANG=localzmq+protobuf:///bfs_path2?"
        "lang=python#/buckets/bfs_path2/exaudf/exaudfclient_py3';",
    )

    sql = get_activation_sql(secrets)
    match = re.match(
        r"\A\s*ALTER\s+SESSION\s+SET\s+SCRIPT_LANGUAGES\s*=\s*'(.+?)'\s*;?\s*\Z",
        sql,
        re.IGNORECASE,
    )
    assert match is not None
    lang_defs = set(match.group(1).split())
    expected_lang_defs = {
        "R=builtin_r",
        "JAVA=builtin_java",
        "PYTHON3=builtin_python3",
        "FIRST_LANG=localzmq+protobuf:///bfs_path1?"
        "lang=python#/buckets/bfs_path1/exaudf/exaudfclient_py3",
        "SECOND_LANG=localzmq+protobuf:///bfs_path2?"
        "lang=python#/buckets/bfs_path2/exaudf/exaudfclient_py3",
    }
    assert lang_defs == expected_lang_defs


def test_get_activation_sql_failure(secrets):
    secrets.save(
        ACTIVATION_KEY_PREFIX + "_lang1",
        "ALTER SESSION SET SCRIPT_LANGUAGES='"
        "R=builtin_r JAVA=builtin_java PYTHON3=builtin_python3 "
        "LANG_ABC=localzmq+protobuf:///bfs_path1?"
        "lang=python#/buckets/bfs_path1/exaudf/exaudfclient_py3';",
    )

    secrets.save("some_other_key", "some_other_value")

    secrets.save(
        ACTIVATION_KEY_PREFIX + "_lang2",
        "ALTER SESSION SET SCRIPT_LANGUAGES='"
        "R=builtin_r JAVA=builtin_java PYTHON3=builtin_python3 "
        "LANG_ABC=localzmq+protobuf:///bfs_path2?"
        "lang=python#/buckets/bfs_path2/exaudf/exaudfclient_py3';",
    )

    with pytest.raises(RuntimeError):
        get_activation_sql(secrets)
