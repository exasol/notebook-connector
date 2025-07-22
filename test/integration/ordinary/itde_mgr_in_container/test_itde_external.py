def test_itde_external(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_external_test.py")
    assert exec_result.exit_code == 0, exec_result.output
