---
title: Customize your deployment
---
Customizing your deployment by upgrading specific components of your deployment is a straight forward task. Data Contexts make this modular, so that you can add or swap out one component at a time. Most of these changes are quick, incremental steps—so you can upgrade from a basic demo deployment to a full production deployment at your own pace and be confident that your Data Context will continue to work at every step along the way.

This reference guide is designed to present you with clear options for upgrading your deployment. For specific implementation steps, please check out the linked How-to guides.

## Components

Here’s an overview of the components of a typical Great Expectations deployment:

* Great Expectations configs and metadata
  * [Options for storing Great Expectations configuration](#options-for-storing-great-expectations-configuration)
  * [Options for storing Expectations](#options-for-storing-expectations)
  * [Options for storing Validation Results](#options-for-storing-validation-results)
  * [Options for customizing generated notebooks](#options-for-customizing-generated-notebooks)

* Integrations to related systems
  * [Connecting to Data](#connecting-to-data)
  * [Options for hosting Data Docs](#options-for-hosting-data-docs)
  * [Additional Checkpoints and Actions](#additional-checkpoints-and-actions)
  * [How to update Data Docs as a Validation Action](../guides/validation/validation_actions/how_to_update_data_docs_as_a_validation_action.md)

## Options for storing Great Expectations configuration
The simplest way to manage your Great Expectations configuration is usually by committing great_expectations/great_expectations.yml to Git. However, it’s not usually a good idea to commit credentials to source control. In some situations, you might need to deploy without access to source control (or maybe even a file system).

Here’s how to handle each of those cases:

* [How to configure credentials](../guides/setup/configuring_data_contexts/how_to_configure_credentials.md)
* [How to instantiate an Ephemeral Data Context](/docs/guides/setup/configuring_data_contexts/instantiating_data_contexts/how_to_explicitly_instantiate_an_ephemeral_data_context)

## Options for storing Expectations
Many teams find it convenient to store Expectations in Git. Essentially, this approach treats Expectations like test fixtures: they live adjacent to code and are stored within version control. Git acts as a collaboration tool and source of record.

Alternatively, you can treat Expectations like configs, and store them in a blob store. Finally, you can store them in a database.

* [How to configure an Expectation store in Amazon S3](../guides/setup/configuring_metadata_stores/how_to_configure_an_expectation_store_in_amazon_s3.md)
* [How to configure an Expectation store in GCS](../guides/setup/configuring_metadata_stores/how_to_configure_an_expectation_store_in_gcs.md)
* [How to configure an Expectation store in Azure Blob Storage](../guides/setup/configuring_metadata_stores/how_to_configure_an_expectation_store_in_azure_blob_storage.md)
* [How to configure an Expectation store to PostgreSQL](../guides/setup/configuring_metadata_stores/how_to_configure_an_expectation_store_to_postgresql.md)
* [How to configure an Expectation store on a filesystem](../guides/setup/configuring_metadata_stores/how_to_configure_an_expectation_store_to_postgresql.md)

## Options for storing Validation Results
By default, Validation Results are stored locally, in an uncommitted directory. This is great for individual work, but not good for collaboration. The most common pattern is to use a cloud-based blob store such as S3, GCS, or Azure blob store. You can also store Validation Results in a database.

* [How to configure a Validation Result store on a filesystem](../guides/setup/configuring_metadata_stores/how_to_configure_a_validation_result_store_on_a_filesystem.md)
* [How to configure a Validation Result store in Amazon S3](../guides/setup/configuring_metadata_stores/how_to_configure_a_validation_result_store_in_amazon_s3.md)
* [How to configure a Validation Result store in GCS](../guides/setup/configuring_metadata_stores/how_to_configure_a_validation_result_store_in_gcs.md)
* [How to configure a Validation Result store in Azure Blob Storage](../guides/setup/configuring_metadata_stores/how_to_configure_a_validation_result_store_in_azure_blob_storage.md)
* [How to configure a Validation Result store to PostgreSQL](../guides/setup/configuring_metadata_stores/how_to_configure_a_validation_result_store_to_postgresql.md)

## Reference Architectures

* [How to instantiate a Data Context on an EMR Spark cluster](../deployment_patterns/how_to_instantiate_a_data_context_on_an_emr_spark_cluster.md)
* [How to use Great Expectations in Databricks](../deployment_patterns/how_to_use_great_expectations_in_databricks.md)

## Connecting to Data
Great Expectations allows you to connect to data in a wide variety of sources, and the list is constantly getting longer. If you have an idea for a source not listed here, please speak up in the public discussion forum.

* [How to connect to a Athena database](../guides/connecting_to_your_data/database/athena.md)
* [How to connect to a BigQuery database](../guides/connecting_to_your_data/database/bigquery.md)
* [How to connect to a MSSQL database](../guides/connecting_to_your_data/database/mssql.md)
* [How to connect to a MySQL database](../guides/connecting_to_your_data/database/mysql.md)
* [How to connect to a Postgres database](../guides/connecting_to_your_data/database/postgres.md)
* [How to connect to a Redshift database](../guides/connecting_to_your_data/database/redshift.md)
* [How to connect to a Snowflake database](../guides/connecting_to_your_data/database/snowflake.md)
* [How to connect to a SQLite database](../guides/connecting_to_your_data/database/sqlite.md)
* [How to connect to data on a filesystem using Spark](../guides/connecting_to_your_data/filesystem/spark.md)
* [How to connect to data on S3 using Spark](../guides/connecting_to_your_data/cloud/s3/spark.md)
* [How to connect to data on GCS using Spark](../guides/connecting_to_your_data/cloud/gcs/spark.md)

## Options for hosting Data Docs
By default, Data Docs are stored locally, in an uncommitted directory. This is great for individual work, but not good for collaboration. A better pattern is usually to deploy to a cloud-based blob store (S3, GCS, or Azure Blob Storage), configured to share a static website.

* [How to host and share Data Docs on a filesystem](../guides/setup/configuring_data_docs/how_to_host_and_share_data_docs_on_a_filesystem.md)
* [How to host and share Data Docs on Azure Blob Storage](../guides/setup/configuring_data_docs/how_to_host_and_share_data_docs_on_azure_blob_storage.md)
* [How to host and share Data Docs on GCS](../guides/setup/configuring_data_docs/how_to_host_and_share_data_docs_on_gcs.md)
* [How to host and share Data Docs on Amazon S3](../guides/setup/configuring_data_docs/how_to_host_and_share_data_docs_on_amazon_s3.md)

## Additional Checkpoints and Actions
Most teams will want to configure various Checkpoints and Validation Actions as part of their deployment. There are two primary patterns for deploying Checkpoints. Sometimes Checkpoints are executed during data processing (e.g. as a task within Airflow). From this vantage point, they can control program flow. Sometimes Checkpoints are executed against materialized data. Great Expectations supports both patterns. There are also some rare instances where you may want to validate data without using a Checkpoint.

* [How to trigger Slack notifications as a Validation Action](../guides/validation/validation_actions/how_to_trigger_slack_notifications_as_a_validation_action.md)
* [How to trigger Opsgenie notifications as a Validation Action](../guides/validation/validation_actions/how_to_trigger_opsgenie_notifications_as_a_validation_action.md)
* [How to trigger Email as a Validation Action](../guides/validation/validation_actions/how_to_trigger_email_as_a_validation_action.md)
* [How to deploy a scheduled Checkpoint with cron](../guides/validation/advanced/how_to_deploy_a_scheduled_checkpoint_with_cron.md)
* [How to get Data Docs URLs for custom Validation Actions](../guides/validation/advanced/how_to_get_data_docs_urls_for_custom_validation_actions.md)
* [How to validate data without a Checkpoint](../guides/validation/advanced/how_to_validate_data_without_a_checkpoint.md)
* [How to run a Checkpoint in Airflow](../deployment_patterns/how_to_use_great_expectations_with_airflow.md)

## Not interested in managing your own configuration or infrastructure?
Learn more about Great Expectations Cloud — our fully managed SaaS offering. Sign up for [our weekly cloud workshop](https://greatexpectations.io/cloud)! You’ll get to see our newest features and apply for our private Alpha program!
