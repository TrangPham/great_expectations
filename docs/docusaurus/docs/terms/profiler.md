---
id: profiler
title: Profiler
hoverText: Generates Metrics and candidate Expectations from data.
---
import UniversalMap from '/docs/images/universal_map/_universal_map.mdx';
import TechnicalTag from '../term_tags/_tag.mdx';
import CreateHeader from '/docs/images/universal_map/_um_create_header.mdx';

<UniversalMap setup='inactive' connect='inactive' create='active' validate='inactive'/> 

## Overview

### Definition

A Profiler generates <TechnicalTag relative="../" tag="metric" text="Metrics" /> and candidate <TechnicalTag relative="../" tag="expectation" text="Expectations" /> from data.

### Features and promises

A Profiler creates a starting point for quickly generating Expectations.

There are several Profilers included with Great Expectations; conceptually, each Profiler is a checklist of questions which will generate an Expectation Suite when asked of a Batch of data.

### Relationship to other objects

A Profiler builds an Expectation Suite from one or more Data Assets. Many Profiler workflows will also include a step that <TechnicalTag relative="../" tag="validation" text="Validates" /> the data against the newly-generated Expectation Suite to return a <TechnicalTag relative="../" tag="validation_result" text="Validation Result" />.

## Use cases

<CreateHeader/>

Profilers come into use when it is time to configure Expectations for your project.  At this point in your workflow you can configure a new Profiler, or use an existing one to generate Expectations from a <TechnicalTag relative="../" tag="batch" text="Batch" /> of data.

For details on how to configure a customized Rule-Based Profiler, see our guide on [how to create a new expectation suite using Rule-Based Profilers](../guides/expectations/advanced/how_to_create_a_new_expectation_suite_using_rule_based_profilers.md).

For instructions on how to use a `UserConfigurableProfiler` to generate Expectations from data, see our guide on [how to create and edit Expectations with a Profiler](../guides/expectations/how_to_create_and_edit_expectations_with_a_profiler.md).

## Features

### Multiple types of Profilers available

There are multiple types of Profilers built in to Great Expectations.  Below is a list with overviews of each one.  For more information, you can view their docstrings and source code in the `great_expectations\profile` [folder on our GitHub](https://github.com/great-expectations/great_expectations/tree/develop/great_expectations/profile).

#### UserConfigurableProfiler

The `UserConfigurableProfiler` is used to build an Expectation Suite from a dataset. The Expectations built are strict - they can be used to determine whether two tables are the same.  When these Profilers are instantiated they can be configured by providing one or more input configuration parameters, allowing you to rapidly create a Profiler without needing to edit configuration files.  However, if you need to change these parameters you will also need to instantiate a new `UserConfigurableProfiler` using the updated parameters.

For instructions on how to use a `UserConfigurableProfiler` to generate Expectations from data, see our guide on [how to create and edit Expectations with a Profiler](../guides/expectations/how_to_create_and_edit_expectations_with_a_profiler.md).

### Rule-Based Profiler

Rule-Based Profilers are a newer implementation of Profiler that allows you to directly configure the Profiler through a YAML configuration.  Rule-Based Profilers allow you to integrate organizational knowledge about your data into the profiling process. For example, a team might have a convention that all columns **named** "id" are primary keys, whereas all columns ending with the **suffix** "_id" are foreign keys. In that case, when the team using Great Expectations first encounters a new dataset that followed the convention, a Profiler could use that knowledge to add an `expect_column_values_to_be_unique` Expectation to the "id" column (but not, for example an "address_id" column).

For details on how to configure a customized Rule-Based Profiler, see our guide on [how to create a new expectation suite using Rule-Based Profilers](../guides/expectations/advanced/how_to_create_a_new_expectation_suite_using_rule_based_profilers.md).

## API basics

### How to access

The recommended workflow for Profilers is to use the `UserConfigurableProfiler`.  Doing so can be as simple as importing it and instantiating a copy by passing a <TechnicalTag relative="../" tag="validator" text="Validator" /> to the class, like so:

```python title="Python code"
from great_expectations.profile.user_configurable_profiler import UserConfigurableProfiler
profiler = UserConfigurableProfiler(profile_dataset=validator)
```

There are additional parameters that can be passed to a `UserConfigurableProfiler`, all of which are either optional or have a default value.  These consist of:

- **excluded_expectations:** A list of Expectations to not include in the suite.
- **ignored_columns:** A list of columns for which you would like to NOT create Expectations.
- **not_null_only:** Boolean, default False. By default, each column is evaluated for nullity. If the column values contain fewer than 50% null values, then the Profiler will add `expect_column_values_to_not_be_null`; if greater than 50% it will add `expect_column_values_to_be_null`. If `not_null_only` is set to `True`, the Profiler will add a not_null Expectation irrespective of the percent nullity (and therefore will not add an `expect_column_values_to_be_null`).
- **primary_or_compound_key:** A list containing one or more columns which are a dataset's primary or compound key. This will create an `expect_column_values_to_be_unique` or `expect_compound_columns_to_be_unique` expectation. This will occur even if one or more of the `primary_or_compound_key` columns are specified in `ignored_columns`.
- **semantic_types_dict:** A dictionary where the keys are available `semantic_types` (see profiler.base.ProfilerSemanticTypes) and the values are lists of columns for which you would like to create `semantic_type` specific Expectations e.g.: `"semantic_types": { "value_set": ["state","country"], "numeric":["age", "amount_due"]}`.
- **table_expectations_only:** Boolean, default False. If True, this will only create the two table level Expectations available to this Profiler (`expect_table_columns_to_match_ordered_list` and `expect_table_row_count_to_be_between`). If a `primary_or_compound_key` is specified, it will create a uniqueness Expectation for that column as well.
- **value_set_threshold:** Takes a string from the following ordered list - "none", "one", "two", "very_few", "few", "many", "very_many", "unique". When the Profiler runs without a semantic_types dict, each column is profiled for cardinality. This threshold determines the greatest cardinality for which to add `expect_column_values_to_be_in_set`. For example, if `value_set_threshold` is set to "unique", it will add a value_set Expectation for every included column. If set to "few", it will add a value_set Expectation for columns whose cardinality is one of "one", "two", "very_few" or "few". The default value is "many". For the purposes of comparing whether two tables are identical, it might make the most sense to set this to "unique".


### How to create

It is unlikely that you will need to create a custom Profiler by extending an existing Profiler with a subclass.  Instead, you should work with a Rule-Based Profiler which can be fully configured in a YAML configuration file.

Configuring a custom Rule-Based Profiler is covered in more detail in the [Configuration](#configuration) section below.  You can also read our guide on [how to create a new expectation suite using Rule-Based Profilers](../guides/expectations/advanced/how_to_create_a_new_expectation_suite_using_rule_based_profilers.md) to be walked through the process, or view [the full source code for that guide](https://github.com/great-expectations/great_expectations/blob/develop/tests/integration/docusaurus/expectations/advanced/multi_batch_rule_based_profiler_example.py) on our GitHub as an example.

### Configuration

#### Rule-Based Profilers

**Rule-Based Profilers** allow users to provide a highly configurable specification which is composed of **Rules** to use in order to build an **Expectation Suite** by profiling existing data.

Imagine you have a table of Sales that comes in every month. You could profile last month's data, inspecting it in order to automatically create a number of expectations that you can use to validate next month's data.  

A **Rule** in a Rule-Based Profiler could say something like "Look at every column in my Sales table, and if that column is numeric, add an `expect_column_values_to_be_between` Expectation to my Expectation Suite, where the `min_value` for the Expectation is the minimum value for the column, and the `max_value` for the Expectation is the maximum value for the column."

Each rule in a Rule-Based Profiler has three types of components:

1. **DomainBuilders**: A DomainBuilder will inspect some data that you provide to the Profiler, and compile a list of Domains for which you would like to build expectations
1. **ParameterBuilders**: A ParameterBuilder will inspect some data that you provide to the Profiler, and compile a dictionary of Parameters that you can use when constructing your ExpectationConfigurations
1. **ExpectationConfigurationBuilders**: An ExpectationConfigurationBuilder will take the Domains compiled by the DomainBuilder, and assemble ExpectationConfigurations using Parameters built by the ParameterBuilder

In the above example, imagine your table of Sales has twenty columns, of which five are numeric:
* Your **DomainBuilder** would inspect all twenty columns, and then yield a list of the five numeric columns
* You would specify two **ParameterBuilders**: one which gets the min of a column, and one which gets a max. Your Profiler would loop over the Domain (or column) list built by the **DomainBuilder** and use the two `ParameterBuilders` to get the min and max for each column.
* Then the Profiler loops over Domains built by the `DomainBuilder` and uses the **ExpectationConfigurationBuilders** to add a `expect_column_values_to_between` column for each of these Domains, where the `min_value` and `max_value` are the values that we got in the `ParameterBuilders`.

In addition to Rules, a Rule-Based Profiler enables you to specify **Variables**, which are global and can be used in any of the Rules. For instance, you may want to reference the same `BatchRequest` or the same tolerance in multiple Rules, and declaring these as Variables will enable you to do so. 

Below is an example configuration based on this discussion:

```yaml title="YAML configuration"
variables:
  my_last_month_sales_batch_request: # We will use this BatchRequest in our DomainBuilder and both of our ParameterBuilders so we can pinpoint the data to Profile
    datasource_name: my_sales_datasource
    data_connector_name: monthly_sales
    data_asset_name: sales_data
    data_connector_query:
      index: -1
  mostly_default: 0.95 # We can set a variable here that we can reference as the `mostly` value for our expectations below
rules:
  my_rule_for_numeric_columns: # This is the name of our Rule
    domain_builder:
      batch_request: $variables.my_last_month_sales_batch_request # We use the BatchRequest that we specified in Variables above using this $ syntax
      class_name: SemanticTypeColumnDomainBuilder # We use this class of DomainBuilder so we can specify the numeric type below
      semantic_types:
        - numeric
    parameter_builders:
      - parameter_name: my_column_min
        class_name: MetricParameterBuilder
        batch_request: $variables.my_last_month_sales_batch_request
        metric_name: column.min # This is the metric we want to get with this ParameterBuilder
        metric_domain_kwargs: $domain.domain_kwargs # This tells us to use the same Domain that is gotten by the DomainBuilder. We could also put a different column name in here to get a metric for that column instead.
      - parameter_name: my_column_max
        class_name: MetricParameterBuilder
        batch_request: $variables.my_last_month_sales_batch_request
        metric_name: column.max
        metric_domain_kwargs: $domain.domain_kwargs
    expectation_configuration_builders:
      - expectation_type: expect_column_values_to_be_between # This is the name of the expectation that we would like to add to our suite
        class_name: DefaultExpectationConfigurationBuilder
        column: $domain.domain_kwargs.column
        min_value: $parameter.my_column_min.value # We can reference the Parameters created by our ParameterBuilders using the same $ notation that we use to get Variables
        max_value: $parameter.my_column_max.value
        mostly: $variables.mostly_default
```
