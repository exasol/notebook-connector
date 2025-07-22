def test_itde_connect(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_connect_test_impl.py")
    assert exec_result.exit_code == 0, exec_result.output
