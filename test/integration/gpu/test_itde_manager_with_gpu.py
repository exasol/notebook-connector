from inspect import cleandoc
from test.integration.ordinary.test_itde_manager import remove_itde

from exasol.nb_connector.ai_lab_config import (
    Accelerator,
    AILabConfig,
)
from exasol.nb_connector.itde_manager import (
    bring_itde_up,
)

DB_NETWORK_NAME = "db_network_DemoDb"

DB_VOLUME_NAME = "db_container_DemoDb_volume"

DB_CONTAINER_NAME = "db_container_DemoDb"


def test_itde_with_gpu(secrets):

    try:
        secrets.save(AILabConfig.accelerator, Accelerator.nvidia.value)
        bring_itde_up(secrets)
        query_accelerator_parameters = cleandoc(
            f"""
                SELECT PARAM_VALUE, PARAM_NAME FROM EXA_METADATA 
                WHERE PARAM_NAME LIKE '%accelerator%' 
                ORDER BY PARAM_NAME;
                """
        )
        from exasol.nb_connector.connections import open_pyexasol_connection

        con = open_pyexasol_connection(secrets)
        result = con.execute(query_accelerator_parameters).fetchall()
        assert result == [
            ("1", "acceleratorDeviceDetected"),
            ("1", "acceleratorDeviceGpuNvidiaDetected"),
        ]

    finally:
        remove_itde()
