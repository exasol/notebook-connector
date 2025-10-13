:octicon:`gear` API Reference
#############################

exasol.nb_connector
*******************

.. autofunction:: exasol.nb_connector.bfs_utils.put_file
.. autofunction:: exasol.nb_connector.cloud_storage.setup_scripts
.. autofunction:: exasol.nb_connector.github.retrieve_jar

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

.. autofunction:: exasol.nb_connector.connections.open_pyexasol_connection
.. autofunction:: exasol.nb_connector.connections.open_bucketfs_bucket
.. autofunction:: exasol.nb_connector.connections.open_bucketfs_location
.. autofunction:: exasol.nb_connector.connections.get_saas_database_id
.. autofunction:: exasol.nb_connector.connections.get_backend
.. autofunction:: exasol.nb_connector.connections.get_udf_bucket_path
.. autofunction:: exasol.nb_connector.connections.open_sqlalchemy_connection
.. autofunction:: exasol.nb_connector.connections.open_ibis_connection

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

.. autoclass:: exasol.nb_connector.slc.script_language_container.ScriptLanguageContainer
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.slc.CondaPackageDefinition
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.slc.PipPackageDefinition
   :members:
   :undoc-members:
.. autoclass:: exasol.nb_connector.slc.ScriptLanguageContainer
   :members:
   :undoc-members:

Functions and Classes in Other Packages
***************************************

.. autofunction:: exasol.nb_connector.language_container_activation.get_activation_sql
.. autofunction:: exasol.nb_connector.language_container_activation.open_pyexasol_connection_with_lang_definitions
.. autoclass:: exasol.nb_connector.model_installation.TransformerModel
   :members:
   :undoc-members:
.. autofunction:: exasol.nb_connector.model_installation.install_model
.. autofunction:: exasol.nb_connector.sagemaker_extension_wrapper.initialize_sme_extension
.. autofunction:: exasol.nb_connector.secret_store.Secrets
.. autoclass:: exasol.nb_connector.text_ai_extension_wrapper.Extraction
   :members:
   :undoc-members:
.. autofunction:: exasol.nb_connector.text_ai_extension_wrapper.initialize_text_ai_extension
.. autofunction:: exasol.nb_connector.transformers_extension_wrapper.initialize_te_extension
.. autofunction:: exasol.nb_connector.utils.upward_file_search
