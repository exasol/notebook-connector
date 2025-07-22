def test_itde_recreation_without_take_down(docker_container):
    exec_result = docker_container.exec_run(
        "python3 /tmp/itde_recreation_without_take_down.py"
    )
    assert exec_result.exit_code == 0, exec_result.output
