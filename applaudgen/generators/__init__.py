from abc import ABC, abstractmethod
from dataclasses import dataclass
from re import template
from jinja2.environment import Template
from jinja2.utils import internalcode
import orjson, os
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .builders.schema import SchemaClassBuilder
from .builders.endpoint import EndpointClassBuilder
from .utils import *

class SDKGenerator(ABC):

    template_subdir: str
    schema_class_builder_class: SchemaClassBuilder
    endpoint_class_builder_class: EndpointClassBuilder

    def __init__(self, spec_file: str, output_dir: str):
        with open(spec_file, 'r') as f:
            self.spec = orjson.loads(f.read())

        cur_path = os.path.dirname(__file__)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(f'{cur_path}/../templates/{self.template_subdir}'),
            autoescape=select_autoescape(),
            keep_trailing_newline=True,
            lstrip_blocks=True,
            trim_blocks=True
        )

        self.jinja_env.filters["capfirst"] = capfirst
        self.jinja_env.filters["snake_case"] = snake_case
        self.jinja_env.filters["simple_singular"] = simple_singular
        self.jinja_env.add_extension("jinja2.ext.do")

    def build_schemas_code(self, definitions: dict, order_keys: list = [], in_models: bool = False) -> tuple[list, dict]:
        schemas_code = []
        remain_enums = {}
        sorted_keys = order_keys + [key for key in definitions.keys() if key not in order_keys]

        for key in sorted_keys:
            schema = definitions[key]
            class_builder = self.schema_class_builder_class(self.jinja_env, key, schema, in_models)
            code = class_builder.build()
            remain_enums.update(class_builder.remain_enums)
            schemas_code.append(code)

        return schemas_code, remain_enums

    def build_endpoints_code(self, paths: dict) -> tuple[dict, dict]:
        not_allowed_operations = ['put', 'options', 'head', 'trace']
        allowed_operations = ['get', 'post', 'delete', 'patch']

        endpoints = []
        endpoints_grouped_by_tag = {}
        for path, spec in paths.items():
            assert all(key not in not_allowed_operations for key in spec.keys()), f'Contains unknown operation method ({spec.keys()}) in path {path}'

            # Skip paths that do not have any allowed operations
            if all(key not in allowed_operations for key in spec.keys()):
                continue
            
            # Only 'get', 'post', 'delete', 'patch' and 'parameters' are handled
            assert all(key in allowed_operations + ['parameters'] for key in spec.keys()), f'Contains unknown key ({spec.keys()}) in path {path}'

            endpoint = self.endpoint_class_builder_class(self.jinja_env, path, spec)
            endpoints.append(endpoint)

            tag: str = None
            for operation in allowed_operations:
                if operation not in spec.keys():
                    continue

                operation_spec = spec[operation]
                assert 'tags' in operation_spec, f'Missing tag in operation {operation} in path {path}'
                assert len(operation_spec['tags']) == 1, f'Multiple tags in operation {operation} in path {path}'
                tag = operation_spec['tags'][0]
                break

            endpoints_grouped_by_tag[tag] = endpoints_grouped_by_tag.get(tag, []) + [endpoint]

        # Generate Endpoint Fields
        all_fields_enums = {}
        for endpoint in endpoints:
            for name, value in endpoint.fields_enums.items():
                if name in all_fields_enums:
                    assert all_fields_enums[name] == value, f'Field {name} is defined twice with different values'
                else:
                    all_fields_enums[name] = value

        return endpoints, endpoints_grouped_by_tag, all_fields_enums

    def generate(self):
        enums = {}
        requests = {}
        responses = {}
        models = {}

        endpoints, endpoints_code_grouped_by_tag, fields_enums = self.build_endpoints_code(self.spec['paths'])

        self.generate_connection_code(endpoints)
        self.generate_endpoints_code(endpoints_code_grouped_by_tag)

        self.generate_fields_code(fields_enums)

        for key, value in self.spec['components']['schemas'].items():
            if 'enum' in value:
                # Enums
                assert value['type'] == 'string', f'Enum {key} is not a string'
                enums[key] = value['enum']
            elif value["type"] == "object":
                # Dataclasses
                if key.endswith('Request'):
                    # Request dataclasses
                    requests[key] = value
                elif key.endswith('Response'):
                    # Response dataclasses
                    responses[key] = value
                else:
                    models[key] = value
            else:
                assert False, f'Unknown type ({value["type"]}) in schemas!'

        request_schemas, request_remain_enums = self.build_schemas_code(requests)
        self.generate_requests_code(request_schemas)

        response_schemas, response_remain_enums = self.build_schemas_code(responses)
        self.generate_responses_code(response_schemas)

        order_keys = ['ResourceLinks', 'PagingInformation', 'HttpHeader', 'ImageAsset', 'AppMediaStateError', 'AppMediaAssetState', 'UploadOperation', 'Device', 'FileLocation', 'ScmProviderType',
        'CiTagPatterns', 'CiBranchPatterns', 'CiStartConditionFileMatcher', 'CiFilesAndFoldersRule', 'CiTestDestination', 'CiAction', 'CiGitUser', 'CiIssueCounts', 'CapabilityOption', 'CapabilitySetting', 'CiBranchStartCondition', 'CiTagStartCondition', 'CiPullRequestStartCondition', 'CiScheduledStartCondition']
        model_schemas, model_remain_enums = self.build_schemas_code(models, order_keys, in_models=True)
        self.generate_models_code(model_schemas)

        enums.update(request_remain_enums)
        enums.update(response_remain_enums)
        enums.update(model_remain_enums)

        self.generate_enums_code(enums)

    @abstractmethod
    def generate_enums_code(self, enums: list):
        pass

    @abstractmethod
    def generate_fields_code(self, fields_enums: dict):
        pass

    @abstractmethod
    def generate_models_code(self, models: list):
        pass

    @abstractmethod
    def generate_responses_code(self, responses: list):
        pass

    @abstractmethod
    def generate_requests_code(self, requests: list):
        pass

    @abstractmethod
    def generate_connection_code(self, endpoints: list):
        pass

    @abstractmethod
    def generate_endpoints_code(self, grouped_endpoints: dict):
        pass

    def render_template(self, template_path: str, file_path: str=None, *args: Any, **kwargs: Any):
        if file_path is None:
            file_path = template_path
        
        target_file_path = file_path if os.path.isabs(file_path) else os.path.join(self.output_dir, file_path)
        self.jinja_env.get_template(f'{template_path}.jinja').stream(*args, **kwargs).dump(f'{target_file_path}')
