from unittest.mock import patch, MagicMock
import pytest

from exasol.language_container_activation import (
    ACTIVATION_KEY_PREFIX,
    get_activation_sql,
    get_requested_languages,
    get_registered_languages,
)


def test_get_registered_languages(secrets):

    with patch('exasol.language_container_activation.get_registered_languages_string',
               MagicMock(return_value='R=builtin_r JAVA=builtin_java')):

        lang_definitions = get_registered_languages(secrets)
        expected_definitions = {'R': 'builtin_r', 'JAVA': 'builtin_java'}
        assert  lang_definitions == expected_definitions


def test_get_requested_languages(secrets):

    secrets.save(ACTIVATION_KEY_PREFIX + '_1','lang1=url1')
    secrets.save(ACTIVATION_KEY_PREFIX + '_2','lang1=url1')
    secrets.save(ACTIVATION_KEY_PREFIX + '_3','lang3=url3')

    lang_definitions = get_requested_languages(secrets)
    expected_definitions = {'lang1': 'url1', 'lang3': 'url3'}
    assert lang_definitions == expected_definitions


def test_get_requested_languages_ambiguous(secrets):

    secrets.save(ACTIVATION_KEY_PREFIX + '_1','lang1=url1')
    secrets.save(ACTIVATION_KEY_PREFIX + '_2','lang1=url2')
    secrets.save(ACTIVATION_KEY_PREFIX + '_3','lang3=url3')

    with pytest.raises(RuntimeError):
        get_requested_languages(secrets)


def test_get_activation_sql(secrets):

    with patch('exasol.language_container_activation.get_registered_languages',
               MagicMock(return_value={'lang1': 'url1', 'lang2': 'url2'})):
        with patch('exasol.language_container_activation.get_requested_languages',
                   MagicMock(return_value={'lang2': 'url22', 'lang3': 'url33'})):
            act_sql = get_activation_sql(secrets)
            expected_sql = "ALTER SESSION SET SCRIPT_LANGUAGES='lang1=url1 lang2=url22 lang3=url33';"
            assert act_sql == expected_sql
