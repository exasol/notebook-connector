


def test_shell():
    import IPython.core.interactiveshell

    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    ipython_code = """
    print("testing shell print")
    """
    result = shell.run_cell(ipython_code)


def test_dummy():
    from IPython.testing.globalipapp import get_ipython
    ipython = get_ipython()
    ipython.run_cell("testing IPython.testing.globalipapp.get_ipython")

def test_shell_store():
    import IPython.core.interactiveshell
    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    shell.run_line_magic("run", "test/unit/ui/access_store_ui_app.py")
    assert "sb_store_file" in shell.user_ns.keys()


def test_magics():

    from IPython import get_ipython
    # from IPython.testing.globalipapp import get_ipython
    line_magics = list(get_ipython().magics_manager.magics.get('line'))
    cell_magics = list(get_ipython().magics_manager.magics.get('cell'))

    print(line_magics)
    print(cell_magics)

def test_nonexistent_object():
    from IPython.testing.globalipapp import get_ipython
    ip = get_ipython()
    # ip.magic('load_ext %    store')

    data="test_data.txt"
    ip.user_ns["data"] = data
    ip.run_line_magic('load_ext', 'storemagic')

    ip.run_line_magic('store', "data")


def test_3():
    from IPython.testing.globalipapp import get_ipython

    ip = get_ipython()
    data = "test_data.txt"
    ip.user_ns["data"] = data
    ip.run_line_magic('load_ext', 'storemagic')
    ip.run_line_magic('store', "data")
    ip.run_line_magic('store', "-r data")
    print(ip.user_ns.keys())
    assert ip.user_ns.get("data") == data
    print(f"Successfully stored {ip.user_ns.get('data')}")


