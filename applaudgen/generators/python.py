import os
from typing import Union
from .utils import *
from . import SDKGenerator, SchemaClassBuilder, EndpointClassBuilder

def _canonical_type_code(type: str, format: str = None) -> str:
    if type == 'string':
        if format == 'date-time':
            return 'datetime.datetime'
        elif format == 'date':
            return 'datetime.date'
        elif format == 'time':
            return 'datetime.time'
        elif format == 'email':
            return 'EmailStr'
        elif format == 'uri':
            return 'AnyUrl'
        elif format == 'uri-reference':
            return 'str'
        elif format == None:
            return 'str'
        else:
            assert False, f'Unhandled string format: {format}'
    if type == 'integer':
        assert format == None, f'Unhandled integer format: {format}'
        return 'int'
    if type == 'number':
        assert format == None, f'Unhandled number format: {format}'
        return 'float'
    if type == 'boolean':
        assert format == None, f'Unhandled boolean format: {format}'
        return 'bool'

    return type

class PythonSchemaClassBuilder(SchemaClassBuilder):

    template_name = 'schemas/class.py'
    enum_template_name = 'schemas/enum.py'

    def entitlements_type_code(self) -> str:
        return 'dict[str, dict[str, str]]'

    def canonical_type_code(self, type: str, format: str = None) -> str:
        return _canonical_type_code(type, format)

    def build_attribute_code(self, name: str, type: str, is_required: bool, default_value: str) -> str:
        name = snake_case(name)

        if default_value is None:
            return f'{name}: {type}' if is_required else f'{name}: Optional[{type}]'

        return f'{name}: Literal[{default_value}] = {default_value}'

    def model_internal_class_name(self, name) -> str:
        if name == 'businessCategory':
            return 'AppClipAdvancedExperienceBusinessCategory'
        elif name == 'releaseType':
            return 'AppStoreVersionReleaseType'
        elif name == 'contentRightsDeclaration':
            return 'AppContentRightsDeclaration'
        elif name == 'status':
            return 'DeviceStatus'
        elif name == 'profileType':
            return 'ProfileType'
        
        return None

    def union_type_code(self, union_types: list) -> str:
        return f"Union[{', '.join(union_types)}]"

    def list_type_code(self, item_type: Union[str, list]) -> str:
        if isinstance(item_type, list):
            canonical_type = self.union_type_code(item_type)
        else:
            canonical_type = self.canonical_type_code(item_type)

        return f'list[{canonical_type}]'

    def external_enum_name(self, enum) -> str:
        if enum == ["NONE", "INFREQUENT_OR_MILD", "FREQUENT_OR_INTENSE"]:
            # defined in enums.py.jinja
            return 'AgeRatingDeclarationLevel'

        return None

class PythonEndpointClassBuilder(EndpointClassBuilder):

    fields_function_template_name = 'endpoints/fields_function.py'
    sort_function_template_name = 'endpoints/sort_function.py'
    filter_function_template_name = 'endpoints/filter_function.py'
    limit_function_template_name = 'endpoints/limit_function.py'
    exists_function_template_name = 'endpoints/exists_function.py'
    include_function_template_name = 'endpoints/include_function.py'

    def filter_type_code(self, filter_type: str) -> str:
        canonical_type = _canonical_type_code(filter_type)
        return f'Union[{canonical_type}, list[{canonical_type}]]'

    def filter_enum_type(self, name: str) -> str:
        return self.__filter_enum_map.get(name, None)


class PythonSDKGenerator(SDKGenerator):

    template_subdir = 'python'
    spec_template_name = '__init__.py'
    enums_template_name = 'schemas/enums.py'
    requests_template_name = 'schemas/requests.py'
    responses_template_name = 'schemas/responses.py'
    models_template_name = 'schemas/models.py'
    connection_template_name = 'connection.py'
    endpoint_template_name = 'endpoints/class.py'
    endpoint_package_template_name = 'endpoints/package.py'
    endpoint_base_template_name = 'endpoints/base.py'
    fields_template_name = 'fields.py'

    schema_class_builder_class = PythonSchemaClassBuilder
    endpoint_class_builder_class = PythonEndpointClassBuilder

    def generate(self):
        dump_dir = os.path.join(self.output_dir, "schemas")
        os.makedirs(dump_dir, exist_ok=True)
        self.render_template(self.spec_template_name, self.spec_template_name, spec=self.spec)
        return super().generate()

    def tag_file_name(self, tag: str) -> str:
        return f'{snake_case(tag)}.py'
    
    def generate_connection_code(self, endpoints: list):
        self.render_template(self.connection_template_name, endpoints=endpoints)

    def generate_endpoints_code(self, grouped_endpoints: dict):
        dump_dir = os.path.join(self.output_dir, "endpoints")
        os.makedirs(dump_dir, exist_ok=True)
        statements = []

        for tag, endpoints in grouped_endpoints.items():
            grouped_tag_file_name = self.tag_file_name(tag)
            
            self.render_template(self.endpoint_template_name, os.path.join("endpoints", grouped_tag_file_name), endpoints=endpoints)

            grouped_tag_module_name = grouped_tag_file_name.replace('.py', '')
            statements.append(f'from .{grouped_tag_module_name} import *')
           
        self.render_template(self.endpoint_package_template_name, os.path.join("endpoints", '__init__.py'), statements=statements)
        self.render_template(self.endpoint_base_template_name)

    def generate_fields_code(self, fields_enums: dict):
        self.render_template(self.fields_template_name, fields_enums=fields_enums)

    # Schemas

    def generate_models_code(self, schemas: list):
        self.render_template(self.models_template_name, schemas=schemas)

    def generate_enums_code(self, enums: list):
        self.render_template(self.enums_template_name, enums=enums)

    def generate_responses_code(self, schemas: list):
        self.render_template(self.responses_template_name, schemas=schemas)

    def generate_requests_code(self, schemas: list):
        self.render_template(self.requests_template_name, schemas=schemas)
