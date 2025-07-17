# pylint: skip-file
# Importing cython packages causes import erros in pylint, we need to investigate this later
from test.utils.integration_test_utils import (
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    setup_itde,
)

from exasol.ai.text.extraction.abstract_extraction import (
    Defaults,
    Output,
)
from exasol.ai.text.extractors.extractor import PipelineExtractor
from exasol.ai.text.extractors.source_table_extractor import (
    NameSelector,
    SchemaSource,
    SourceTableExtractor,
    TableSource,
)
from exasol.ai.text.extractors.standard_extractor import StandardExtractor
from exasol.ai.text.impl.utils.sql_utils import (
    integer_column_spec,
    varchar_column_spec,
)
from exasol.analytics.schema import (
    SchemaName,
    Table,
    TableName,
    TableNameImpl,
)

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.text_ai_extension_wrapper import (
    Extraction as WrappedExtraction,
)
from exasol.nb_connector.text_ai_extension_wrapper import (
    initialize_text_ai_extension,
)


class TxaiTest:
    def __init__(self, schema_name: str):
        self.schema = SchemaName(schema_name)
        self.key_column = integer_column_spec(name="key").to_column()
        self.text_column = varchar_column_spec(name="text").to_column()
        self.table = Table(
            name=self.input_table_name(), columns=[self.key_column, self.text_column]
        )

    def input_table_name(self, id: int = 0) -> TableName:
        suffix = f"_{id}" if id else ""
        return TableNameImpl(table_name=f"INPUT_TABLE{suffix}", schema=self.schema)


def test_text_ai_extension_2(secrets: Secrets, setup_itde):
    conf = secrets
    topics = {"urgent", "not urgent"}
    scenario = TxaiTest("INPUT_SCHEMA")
    schema = scenario.schema
    table = scenario.table
    text_column = scenario.text_column.name.name
    key_column = scenario.key_column.name.name

    with open_pyexasol_connection(conf) as pyexasol_connection:
        pyexasol_connection.execute(
            f"DROP SCHEMA IF EXISTS {schema.fully_qualified} CASCADE"
        )
        pyexasol_connection.execute(f"CREATE SCHEMA {schema.fully_qualified}")
        pyexasol_connection.execute(table.create_statement)
        pyexasol_connection.execute(
            f"INSERT INTO {table.name.fully_qualified} VALUES"
            " (1, 'This is a test.'),"
            " (2, 'Exasol is awesome.')"
        )

    initialize_text_ai_extension(conf)
    # model_repository is None by default and will be replaced by
    # text_ai_extension_wrapper.py
    defaults = Defaults(parallelism_per_node=1, batch_size=10)
    src_extractor = SourceTableExtractor(
        name="DOCUMENTS",
        sources=[
            SchemaSource(
                db_schema=NameSelector(pattern=schema.name),
                tables=[
                    TableSource(
                        table=NameSelector(pattern=table.name.name),
                        columns=[NameSelector(pattern=text_column)],
                        keys=[NameSelector(pattern=key_column)],
                    )
                ],
            )
        ],
    )
    p_extractor = PipelineExtractor(
        steps=[src_extractor, StandardExtractor(topics=topics)]
    )
    extraction = WrappedExtraction(
        extractor=p_extractor,
        output=Output(db_schema=schema.name),
        defaults=defaults,
    )
    extraction.run(conf)
