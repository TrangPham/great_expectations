import json
import logging
from abc import ABCMeta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from urllib.parse import urljoin

import requests
from typing_extensions import TypedDict

from great_expectations.core.http import create_session
from great_expectations.data_context.cloud_constants import (
    CLOUD_DEFAULT_BASE_URL,
    SUPPORT_EMAIL,
    GXCloudRESTResource,
)
from great_expectations.data_context.store.store_backend import StoreBackend
from great_expectations.data_context.types.refs import GXCloudResourceRef
from great_expectations.data_context.types.resource_identifiers import GXCloudIdentifier
from great_expectations.exceptions import StoreBackendError, StoreBackendTransientError
from great_expectations.util import bidict, filter_properties_dict, hyphen

logger = logging.getLogger(__name__)


class ErrorDetail(TypedDict):
    code: Optional[str]
    detail: Optional[str]
    source: Optional[str]


class ErrorPayload(TypedDict):
    errors: List[ErrorDetail]


class PayloadDataField(TypedDict):
    attributes: dict
    id: str
    type: str


class ResponsePayload(TypedDict):
    data: PayloadDataField


AnyPayload = Union[ResponsePayload, ErrorPayload]


def construct_url(
    base_url: str,
    organization_id: str,
    resource_name: str,
    id: Optional[str] = None,
) -> str:
    url = urljoin(
        base_url,
        f"organizations/{organization_id}/{hyphen(resource_name)}",
    )
    if id:
        url = f"{url}/{id}"
    return url


def construct_json_payload(
    resource_type: str,
    organization_id: str,
    attributes_key: str,
    attributes_value: Any,
    **kwargs: dict,
) -> dict:
    data = {
        "data": {
            "type": resource_type,
            "attributes": {
                "organization_id": organization_id,
                attributes_key: attributes_value,
                **kwargs,
            },
        }
    }
    return data


def get_user_friendly_error_message(
    http_exc: requests.exceptions.HTTPError, log_level: int = logging.WARNING
) -> str:
    # TODO: define a GeCloud service/client for this & other related behavior
    support_message = []
    response: requests.Response = http_exc.response

    logger.log(log_level, f"{http_exc.__class__.__name__}:{http_exc} - {response}")

    request_id = response.headers.get("request-id", "")
    if request_id:
        support_message.append(f"Request-Id: {request_id}")

    try:
        error_json: ErrorPayload = http_exc.response.json()
        errors = error_json.get("errors")
        if errors:
            support_message.append(json.dumps(errors))

    except json.JSONDecodeError:
        support_message.append(
            f"Please contact the Great Expectations team at {SUPPORT_EMAIL}"
        )
    return " ".join(support_message)


class GXCloudStoreBackend(StoreBackend, metaclass=ABCMeta):
    PAYLOAD_ATTRIBUTES_KEYS: Dict[GXCloudRESTResource, str] = {
        GXCloudRESTResource.CHECKPOINT: "checkpoint_config",
        GXCloudRESTResource.DATASOURCE: "datasource_config",
        GXCloudRESTResource.DATA_CONTEXT: "data_context_config",
        GXCloudRESTResource.DATA_CONTEXT_VARIABLES: "data_context_variables",
        GXCloudRESTResource.EXPECTATION_SUITE: "suite",
        GXCloudRESTResource.EXPECTATION_VALIDATION_RESULT: "result",
        GXCloudRESTResource.PROFILER: "profiler",
        GXCloudRESTResource.RENDERED_DATA_DOC: "rendered_data_doc",
        GXCloudRESTResource.VALIDATION_RESULT: "result",
    }

    ALLOWED_SET_KWARGS_BY_RESOURCE_TYPE: Dict[GXCloudRESTResource, Set[str]] = {
        GXCloudRESTResource.EXPECTATION_SUITE: {"clause_id"},
        GXCloudRESTResource.RENDERED_DATA_DOC: {"source_type", "source_id"},
        GXCloudRESTResource.VALIDATION_RESULT: {
            "checkpoint_id",
            "expectation_suite_id",
        },
    }

    RESOURCE_PLURALITY_LOOKUP_DICT: bidict = bidict(  # type: ignore[misc] # Keywords must be str
        **{  # type: ignore[arg-type]
            GXCloudRESTResource.BATCH: "batches",
            GXCloudRESTResource.CHECKPOINT: "checkpoints",
            GXCloudRESTResource.DATA_ASSET: "data_assets",
            GXCloudRESTResource.DATA_CONTEXT_VARIABLES: "data_context_variables",
            GXCloudRESTResource.DATASOURCE: "datasources",
            GXCloudRESTResource.EXPECTATION: "expectations",
            GXCloudRESTResource.EXPECTATION_SUITE: "expectation_suites",
            GXCloudRESTResource.EXPECTATION_VALIDATION_RESULT: "expectation_validation_results",
            GXCloudRESTResource.PROFILER: "profilers",
            GXCloudRESTResource.RENDERED_DATA_DOC: "rendered_data_docs",
            GXCloudRESTResource.VALIDATION_RESULT: "validation_results",
        }
    )

    def __init__(
        self,
        ge_cloud_credentials: Dict,
        ge_cloud_base_url: str = CLOUD_DEFAULT_BASE_URL,
        ge_cloud_resource_type: Optional[Union[str, GXCloudRESTResource]] = None,
        ge_cloud_resource_name: Optional[str] = None,
        suppress_store_backend_id: bool = True,
        manually_initialize_store_backend_id: str = "",
        store_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            fixed_length_key=True,
            suppress_store_backend_id=suppress_store_backend_id,
            manually_initialize_store_backend_id=manually_initialize_store_backend_id,
            store_name=store_name,
        )
        assert (
            ge_cloud_resource_type or ge_cloud_resource_name
        ), "Must provide either ge_cloud_resource_type or ge_cloud_resource_name"

        self._ge_cloud_base_url = ge_cloud_base_url

        self._ge_cloud_resource_name = (
            ge_cloud_resource_name
            or self.RESOURCE_PLURALITY_LOOKUP_DICT[ge_cloud_resource_type]
        )

        # While resource_types should be coming in as enums, configs represent the arg
        # as strings and require manual casting.
        if ge_cloud_resource_type and isinstance(ge_cloud_resource_type, str):
            ge_cloud_resource_type = ge_cloud_resource_type.upper()
            ge_cloud_resource_type = GXCloudRESTResource[ge_cloud_resource_type]

        self._ge_cloud_resource_type = (
            ge_cloud_resource_type
            or self.RESOURCE_PLURALITY_LOOKUP_DICT[ge_cloud_resource_name]
        )

        self._ge_cloud_credentials = ge_cloud_credentials

        # Initialize with store_backend_id if not part of an HTMLSiteStore
        if not self._suppress_store_backend_id:
            _ = self.store_backend_id

        self._session = create_session(
            access_token=self._ge_cloud_credentials["access_token"]
        )

        # Gather the call arguments of the present function (include the "module_name" and add the "class_name"), filter
        # out the Falsy values, and set the instance "_config" variable equal to the resulting dictionary.
        self._config = {
            "ge_cloud_base_url": ge_cloud_base_url,
            "ge_cloud_resource_name": ge_cloud_resource_name,
            "ge_cloud_resource_type": ge_cloud_resource_type,
            "fixed_length_key": True,
            "suppress_store_backend_id": suppress_store_backend_id,
            "manually_initialize_store_backend_id": manually_initialize_store_backend_id,
            "store_name": store_name,
            "module_name": self.__class__.__module__,
            "class_name": self.__class__.__name__,
        }
        filter_properties_dict(properties=self._config, inplace=True)

    def _get(self, key: Tuple[str, ...]) -> ResponsePayload:  # type: ignore[override]
        ge_cloud_url = self.get_url_for_key(key=key)
        params: Optional[dict] = None
        try:
            # if name is included in the key, add as a param
            if len(key) > 2 and key[2]:
                params = {"name": key[2]}
                ge_cloud_url = ge_cloud_url.rstrip("/")

            response = self._session.get(
                ge_cloud_url,
                params=params,
            )
            response.raise_for_status()
            response_json: dict = response.json()
            if (
                isinstance(response_json["data"], list)
                and len(response_json["data"]) == 0
            ):
                raise StoreBackendError(
                    "Unable to get object in GX Cloud Store Backend: Object does not exist."
                )
            return cast(ResponsePayload, response.json())
        except json.JSONDecodeError as jsonError:
            logger.debug(
                "Failed to parse GX Cloud Response into JSON",
                str(response.text),
                str(jsonError),
            )
            raise StoreBackendError(
                f"Unable to get object in GX Cloud Store Backend: {jsonError}"
            )
        except requests.HTTPError as http_err:
            raise StoreBackendError(
                f"Unable to get object in GX Cloud Store Backend: {get_user_friendly_error_message(http_err)}"
            )
        except requests.Timeout as timeout_exc:
            logger.exception(timeout_exc)
            raise StoreBackendTransientError(
                "Unable to get object in GX Cloud Store Backend: This is likely a transient error. Please try again."
            )

    def _move(self) -> None:  # type: ignore[override]
        pass

    # TODO: GG 20220810 return the `ResponsePayload`
    def _update(self, id: str, value: Any) -> bool:
        resource_type = self.ge_cloud_resource_type
        organization_id = self.ge_cloud_credentials["organization_id"]
        attributes_key = self.PAYLOAD_ATTRIBUTES_KEYS[resource_type]

        data = construct_json_payload(
            resource_type=resource_type.value,
            attributes_key=attributes_key,
            attributes_value=value,
            organization_id=organization_id,
        )

        url = construct_url(
            base_url=self.ge_cloud_base_url,
            organization_id=organization_id,
            resource_name=self.ge_cloud_resource_name,
        )

        if id:
            data["data"]["id"] = id
            url = urljoin(f"{url}/", id)

        try:
            response = self._session.put(url, json=data)
            response_status_code = response.status_code

            # 2022-07-28 - Chetan - GX Cloud does not currently support PUT requests
            # for the ExpectationSuite endpoint. As such, this is a temporary fork to
            # ensure that legacy PATCH behavior is supported.
            if (
                response_status_code == 405
                and resource_type is GXCloudRESTResource.EXPECTATION_SUITE
            ):
                response = self._session.patch(url, json=data)
                response_status_code = response.status_code

            response.raise_for_status()
            return True

        except requests.HTTPError as http_exc:
            raise StoreBackendError(
                f"Unable to update object in GX Cloud Store Backend: {get_user_friendly_error_message(http_exc)}"
            )
        except requests.Timeout as timeout_exc:
            logger.exception(timeout_exc)
            raise StoreBackendTransientError(
                "Unable to update object in GX Cloud Store Backend: This is likely a transient error. Please try again."
            )
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError(
                f"Unable to update object in GX Cloud Store Backend: {e}"
            )

    @property
    def allowed_set_kwargs(self) -> Set[str]:
        return self.ALLOWED_SET_KWARGS_BY_RESOURCE_TYPE.get(
            self.ge_cloud_resource_type, set()
        )

    def validate_set_kwargs(self, kwargs: dict) -> Union[bool, None]:
        kwarg_names = set(kwargs.keys())
        if len(kwarg_names) == 0:
            return True
        if kwarg_names <= self.allowed_set_kwargs:
            return True
        if not (kwarg_names <= self.allowed_set_kwargs):
            extra_kwargs = kwarg_names - self.allowed_set_kwargs
            raise ValueError(f'Invalid kwargs: {(", ").join(extra_kwargs)}')
        return None

    def _set(  # type: ignore[override]
        self,
        key: Tuple[GXCloudRESTResource, ...],
        value: Any,
        **kwargs: dict,
    ) -> Union[bool, GXCloudResourceRef]:
        # Each resource type has corresponding attribute key to include in POST body
        resource = key[0]
        id: str = key[1]

        # if key has an id, perform _update instead

        # Chetan - 20220713 - DataContextVariables are a special edge case for the Cloud product
        # and always necessitate a PUT.
        if id or resource is GXCloudRESTResource.DATA_CONTEXT_VARIABLES:
            # _update returns a bool
            return self._update(id=id, value=value)

        resource_type = self.ge_cloud_resource_type
        resource_name = self.ge_cloud_resource_name
        organization_id = self.ge_cloud_credentials["organization_id"]

        attributes_key = self.PAYLOAD_ATTRIBUTES_KEYS[resource_type]

        kwargs = kwargs if self.validate_set_kwargs(kwargs) else {}
        data = construct_json_payload(
            resource_type=resource_type,
            attributes_key=attributes_key,
            attributes_value=value,
            organization_id=organization_id,
            **kwargs,
        )

        url = construct_url(
            base_url=self.ge_cloud_base_url,
            organization_id=organization_id,
            resource_name=resource_name,
        )

        try:
            response = self._session.post(url, json=data)
            response.raise_for_status()
            response_json = response.json()

            object_id = response_json["data"]["id"]
            object_url = self.get_url_for_key((self.ge_cloud_resource_type, object_id))
            # This method is where posts get made for all cloud store endpoints. We pass
            # the response_json back up to the caller because the specific resource may
            # want to parse resource specific data out of the response.
            return GXCloudResourceRef(
                resource_type=resource_type,
                id=object_id,
                url=object_url,
                response_json=response_json,
            )
        except requests.HTTPError as http_exc:
            raise StoreBackendError(
                f"Unable to set object in GX Cloud Store Backend: {get_user_friendly_error_message(http_exc)}"
            )
        except requests.Timeout as timeout_exc:
            logger.exception(timeout_exc)
            raise StoreBackendTransientError(
                "Unable to set object in GX Cloud Store Backend: This is likely a transient error. Please try again."
            )
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError(
                f"Unable to set object in GX Cloud Store Backend: {e}"
            )

    @property
    def ge_cloud_base_url(self) -> str:
        return self._ge_cloud_base_url

    @property
    def ge_cloud_resource_name(self) -> str:
        return self._ge_cloud_resource_name

    @property
    def ge_cloud_resource_type(self) -> GXCloudRESTResource:
        return self._ge_cloud_resource_type  # type: ignore[return-value]

    @property
    def ge_cloud_credentials(self) -> dict:
        return self._ge_cloud_credentials

    def list_keys(self, prefix: Tuple = ()) -> List[Tuple[GXCloudRESTResource, str, str]]:  # type: ignore[override]
        url = construct_url(
            base_url=self.ge_cloud_base_url,
            organization_id=self.ge_cloud_credentials["organization_id"],
            resource_name=self.ge_cloud_resource_name,
        )

        resource_type = self.ge_cloud_resource_type
        attributes_key = self.PAYLOAD_ATTRIBUTES_KEYS[resource_type]

        try:
            response = self._session.get(url)
            response.raise_for_status()
            response_json = response.json()

            # Chetan - 20220824 - Explicit fork due to ExpectationSuite using a different name field.
            # Once 'expectation_suite_name' is renamed, this can be removed.
            name_attr: str
            if resource_type is GXCloudRESTResource.EXPECTATION_SUITE:
                name_attr = "expectation_suite_name"
            else:
                name_attr = "name"

            keys = []
            for resource in response_json["data"]:
                id: str = resource["id"]

                resource_dict: dict = resource.get("attributes", {}).get(
                    attributes_key, {}
                )
                resource_name: str = resource_dict.get(name_attr, "")

                key = (resource_type, id, resource_name)
                keys.append(key)

            return keys
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError(
                f"Unable to list keys in GX Cloud Store Backend: {e}"
            )

    def get_url_for_key(  # type: ignore[override]
        self, key: Tuple[str, ...], protocol: Optional[Any] = None
    ) -> str:
        id = key[1]
        url = construct_url(
            base_url=self.ge_cloud_base_url,
            organization_id=self.ge_cloud_credentials["organization_id"],
            resource_name=self.ge_cloud_resource_name,
            id=id,
        )
        return url

    def remove_key(self, key):
        if not isinstance(key, tuple):
            key = key.to_tuple()

        id = key[1]

        data = {
            "data": {
                "type": self.ge_cloud_resource_type,
                "id": id,
                "attributes": {
                    "deleted": True,
                },
            }
        }

        url = construct_url(
            base_url=self.ge_cloud_base_url,
            organization_id=self.ge_cloud_credentials["organization_id"],
            resource_name=self.ge_cloud_resource_name,
            id=id,
        )

        try:
            response = self._session.delete(url, json=data)
            response.raise_for_status()
            return True
        except requests.HTTPError as http_exc:
            logger.exception(http_exc)
            raise StoreBackendError(
                f"Unable to delete object in GX Cloud Store Backend: {get_user_friendly_error_message(http_exc)}"
            )
        except requests.Timeout as timeout_exc:
            logger.exception(timeout_exc)
            raise StoreBackendTransientError(
                "Unable to delete object in GX Cloud Store Backend: This is likely a transient error. Please try again."
            )
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError(
                f"Unable to delete object in GX Cloud Store Backend: {e}"
            )

    def _has_key(self, key: Tuple[str, ...]) -> bool:
        try:
            _ = self._get(key)
        except StoreBackendTransientError:
            raise
        except StoreBackendError as e:
            logger.info(f"Could not find object associated with key {key}: {e}")
            return False
        return True

    @property
    def config(self) -> dict:
        return self._config

    def build_key(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> GXCloudIdentifier:
        """Get the store backend specific implementation of the key. ignore resource_type since it is defined when initializing the cloud store backend."""
        return GXCloudIdentifier(
            resource_type=self.ge_cloud_resource_type,
            id=id,
            resource_name=name,
        )
