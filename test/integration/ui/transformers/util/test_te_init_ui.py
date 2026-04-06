import nbformat
from nbclient import NotebookClient


def test_te_init_ui_save_token(solara_test, page_session, secrets, tmp_path):
    """
    This test validates that the te_init UI can save a token to the ai_lab_config after loading it via the access_store UI.
     - First, it loads the ai_lab_config via the access_store UI by entering a password and clicking open.
     - Then, it uses the te_init UI to save a token to the ai_lab_config and verifies that the token is correctly saved.
     - This test ensures that the ai_lab_config is properly shared between the access_store UI and the te_init UI

     Why nbformat test isntead of normal python playwright test ?
     - because the access_store UI and te_init UI need to be run in the same kernel to enable the sharing of secrets
    """
    code_word = "dummy123"
    store_dir = str(tmp_path)
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(
            # loading the ai_lab_config via access_store_ui
            f"""
            from IPython.display import display
            from exasol.nb_connector.ui.access.access_store import get_access_store
            
            ui = get_access_store("{store_dir}")
            display(ui)
            
            password_field = ui.children[0].children[2].children[1]
            password_field.value = "{code_word}"
            open_button = ui.children[1]
            open_button.click()
            """
        ),
        nbformat.v4.new_code_cell("""
            assert ai_lab_config is not None
            """),
        nbformat.v4.new_code_cell(
            # Now ai_lab_config exists in this kernel session and can be used to save the token via the te_init UI
            """
            from exasol.nb_connector.ui.transformers.util import te_init
            te_init.ai_lab_config = ai_lab_config
            te_ui = te_init.get_hf_config(ai_lab_config)
            display(te_ui)
            """
        ),
        nbformat.v4.new_code_cell(
            # Verify the token is saved via the UI
            """
            token_widget = te_ui.children[0].children[1].children[1]
            token_widget.value = "hf_token_456"
            save_button = te_ui.children[-1]
            save_button.click()
            assert ai_lab_config.get("huggingface_token") == "hf_token_456"
            """
        ),
    ]
    nb = nbformat.v4.new_notebook()
    NotebookClient(nb, timeout=60, kernel_name="python3").execute()
