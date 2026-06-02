:octicon:`gear` API Reference
#############################

exasol.nb_connector.secret_store
********************************

.. autoclass:: exasol.nb_connector.secret_store.InvalidPassword
.. autoclass:: exasol.nb_connector.secret_store.Secrets
   :members:
   :undoc-members:

exasol.nb_connector
*******************

.. autofunction:: exasol.nb_connector.cloud_storage.setup_scripts

.. autoclass:: exasol.nb_connector.ai_lab_config.AILabConfig
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.ai_lab_config.Accelerator
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.ai_lab_config.StorageBackend
   :members:
   :undoc-members:


exasol.nb_connector.connections
*******************************

.. autofunction:: exasol.nb_connector.connections.get_backend
.. autofunction:: exasol.nb_connector.connections.get_external_host
.. autofunction:: exasol.nb_connector.connections.get_saas_database_id
.. autofunction:: exasol.nb_connector.connections.get_udf_bucket_path
.. autofunction:: exasol.nb_connector.connections.open_bucketfs_connection
.. autofunction:: exasol.nb_connector.connections.open_bucketfs_bucket
.. autofunction:: exasol.nb_connector.connections.open_bucketfs_location
.. autofunction:: exasol.nb_connector.connections.open_ibis_connection
.. autofunction:: exasol.nb_connector.connections.open_pyexasol_connection
.. autofunction:: exasol.nb_connector.connections.open_sqlalchemy_connection

exasol.nb_connector.itde_manager
********************************

.. autoclass:: exasol.nb_connector.itde_manager.ItdeContainerStatus
   :members:
   :undoc-members:

.. autofunction:: exasol.nb_connector.itde_manager.bring_itde_up
.. autofunction:: exasol.nb_connector.itde_manager.get_itde_status
.. autofunction:: exasol.nb_connector.itde_manager.restart_itde
.. autofunction:: exasol.nb_connector.itde_manager.take_itde_down

exasol.nb_connector.script_language_container
*********************************************

.. autoclass:: exasol.nb_connector.slc.SlcError
.. autoclass:: exasol.nb_connector.slc.script_language_container.ScriptLanguageContainer
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.slc.ScriptLanguageContainer
   :members:
   :undoc-members:

exasol.nb_connector.github
**************************

.. autoclass:: exasol.nb_connector.github.Project
   :members:
   :undoc-members:
.. autofunction:: exasol.nb_connector.github.get_latest_version_and_jar_url
.. autofunction:: exasol.nb_connector.github.retrieve_jar

exasol.nb_connector.language_container_activation
*************************************************

.. autofunction:: exasol.nb_connector.language_container_activation.get_registered_languages_string
.. autofunction:: exasol.nb_connector.language_container_activation.get_registered_languages
.. autofunction:: exasol.nb_connector.language_container_activation.get_requested_languages
.. autofunction:: exasol.nb_connector.language_container_activation.get_activation_sql
.. autofunction:: exasol.nb_connector.language_container_activation.open_pyexasol_connection_with_lang_definitions

exasol.nb_connector.model_installation
**************************************

.. autoclass:: exasol.nb_connector.model_installation.TransformerModel
   :members:
   :undoc-members:
.. autofunction:: exasol.nb_connector.model_installation.ensure_model_subdir_config_value
.. autofunction:: exasol.nb_connector.model_installation.create_model_repository
.. autofunction:: exasol.nb_connector.model_installation.install_model

exasol.nb_connector.text_ai_extension_wrapper
*********************************************

.. autofunction:: exasol.nb_connector.text_ai_extension_wrapper.deploy_license
.. autoclass:: exasol.nb_connector.text_ai_extension_wrapper.Extraction
   :members:
   :undoc-members:
.. autofunction:: exasol.nb_connector.text_ai_extension_wrapper.initialize_text_ai_extension

exasol.nb_connector.transformers_extension_wrapper
**************************************************

.. autofunction:: exasol.nb_connector.transformers_extension_wrapper.deploy_scripts
.. autofunction:: exasol.nb_connector.transformers_extension_wrapper.initialize_te_extension
.. autofunction:: exasol.nb_connector.transformers_extension_wrapper.upload_model
.. autofunction:: exasol.nb_connector.transformers_extension_wrapper.upload_model_from_cache

Functions and Classes in Other Packages
***************************************

.. autofunction:: exasol.nb_connector.utils.upward_file_search
