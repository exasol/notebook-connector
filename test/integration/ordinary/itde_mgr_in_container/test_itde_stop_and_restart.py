def test_itde_stop_and_restart(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_stop_and_restart.py")
    assert exec_result.exit_code == 0, exec_result.output
