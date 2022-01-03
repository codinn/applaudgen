from abc import ABC, abstractmethod
from typing import Any
from jinja2 import environment
from dataclasses import dataclass, field
from ..utils import *

### Connection().user(id=xxx).filter(appCategories=[], ...).field(...).get()

class EndpointClassBuilder(ABC):

    @dataclass
    class GetOperation:
        deprecated: bool
        response_type: str
        response_single_instance: bool
        response_comment: str

    @dataclass
    class PostOperation:
        deprecated: bool
        response_type: str
        response_single_instance: bool
        response_comment: str
        request_type: str
        request_single_instance: bool
        request_comment: str

    @dataclass
    class PatchOperation:
        deprecated: bool
        response_type: str
        response_single_instance: bool
        response_comment: str
        request_type: str
        request_single_instance: bool
        request_comment: str

    @dataclass
    class DeleteOperation:
        deprecated: bool
        request_type: str
        request_single_instance: bool
        request_comment: str

    fields_function_template_name: str
    sort_function_template_name: str
    filter_function_template_name: str
    exists_function_template_name: str
    limit_function_template_name: str
    include_function_template_name: str
    
    _operation_prefixes = {
        'get': 'get', 
        'post': 'create',
        'delete': 'delete',
        'patch': 'update'
    }

    _filter_enum_map = {
        'AppCategoryListEndpoint.platforms'                 : 'Platform',
        'AppEncryptionDeclarationListEndpoint.platform'     : 'Platform',
        'AppListEndpoint.appStoreVersions.appStoreState'    : 'AppStoreVersionState',
        'AppListEndpoint.appStoreVersions.platform'         : 'Platform',
        'BetaAppReviewSubmissionListEndpoint.betaReviewState': 'BetaReviewState',
        'BetaTesterListEndpoint.inviteType'                 : 'BetaInviteType',
        'BuildListEndpoint.betaAppReviewSubmission.betaReviewState': 'BetaReviewState',
        'BuildListEndpoint.buildAudienceType'               : 'BuildAudienceType',
        'BuildListEndpoint.preReleaseVersion.platform'      : 'Platform',
        'BuildListEndpoint.processingState'                 : 'BuildProcessingState',
        'BundleIdListEndpoint.platform'                     : 'BundleIdPlatform',
        'CertificateListEndpoint.certificateType'           : 'CertificateType',
        'CiProductListEndpoint.productType'                 : 'CiProductType',
        'DeviceListEndpoint.platform'                       : 'BundleIdPlatform',
        'DeviceListEndpoint.status'                         : 'DeviceStatus',
        'PreReleaseVersionListEndpoint.builds.processingState': 'BuildProcessingState',
        'PreReleaseVersionListEndpoint.platform'            : 'Platform',
        'ProfileListEndpoint.profileState'                  : 'ProfileState',
        'ProfileListEndpoint.profileType'                   : 'ProfileType',
        'UserInvitationListEndpoint.roles'                  : 'UserRole',
        'UserListEndpoint.roles'                            : 'UserRole',
        'AppClipAdvancedExperienceListOfAppClipEndpoint.action' : 'AppClipAction',
        'AppClipAdvancedExperienceListOfAppClipEndpoint.placeStatus': 'AppClipAdvancedExperiencePlaceStatus',
        'AppClipAdvancedExperienceListOfAppClipEndpoint.status' : 'AppClipAdvancedExperienceStatus',
        'AppPreviewSetListOfAppStoreVersionLocalizationEndpoint.previewType': 'PreviewType',
        'AppScreenshotSetListOfAppStoreVersionLocalizationEndpoint.screenshotDisplayType': 'ScreenshotDisplayType',
        'AppStoreVersionListOfAppEndpoint.appStoreState':       'AppStoreVersionState',
        'AppStoreVersionListOfAppEndpoint.platform':             'Platform',
        'GameCenterEnabledVersionListOfAppEndpoint.platform':    'Platform',
        'InAppPurchaseListOfAppEndpoint.inAppPurchaseType':      'InAppPurchaseType',
        'PerfPowerMetricListOfAppEndpoint.metricType':           'PerfPowerMetricType',
        'DiagnosticSignatureListOfBuildEndpoint.diagnosticType': 'DiagnosticType',
        'PerfPowerMetricListOfBuildEndpoint.metricType':         'PerfPowerMetricType',
        'BuildListOfCiBuildRunEndpoint.betaAppReviewSubmission.betaReviewState': 'BetaReviewState',
        'BuildListOfCiBuildRunEndpoint.buildAudienceType':       'BuildAudienceType',
        'BuildListOfCiBuildRunEndpoint.preReleaseVersion.platform': 'Platform',
        'BuildListOfCiBuildRunEndpoint.processingState':         'BuildProcessingState',
        'CompatibleVersionListOfGameCenterEnabledVersionEndpoint.platform': 'Platform',
        'PerfPowerMetricListOfAppEndpoint.platform':             'PerfPowerMetricPlatform',
        'PerfPowerMetricListOfBuildEndpoint.platform':           'PerfPowerMetricPlatform',
    }
    
    @abstractmethod
    def filter_type_code(self, filter_type: str) -> str:
        pass

    def build_include_function_code(self, include_names: list[str]) -> str:
        return self.jinja_env.get_template(f'{self.include_function_template_name}.jinja').render(include_names=include_names, endpoint_class=self.class_name)

    def build_limit_function_code(self, limit_tuples: list[tuple[str, int, str]]) -> str:
        # Make sure defualt limit is at first position
        limit_tuples.sort(key=lambda x: 0 if x[0] == 'default-limit' else 1)
        return self.jinja_env.get_template(f'{self.limit_function_template_name}.jinja').render(limit_tuples=limit_tuples, endpoint_class=self.class_name)

    def build_fields_function_code(self, fields_tuples: list[tuple[str, str]]) -> str:
        # Remove duplicates
        res_fields = [field for n, field in enumerate(fields_tuples) if field not in fields_tuples[:n]]
        return self.jinja_env.get_template(f'{self.fields_function_template_name}.jinja').render(fields_tuples=res_fields, endpoint_class=self.class_name)

    def build_exists_function_code(self, exists_names: list) -> str:
        return self.jinja_env.get_template(f'{self.exists_function_template_name}.jinja').render(exists_names=exists_names, endpoint_class=self.class_name)

    def build_sort_function_code(self, qualifiers: list[str]) -> str:
        return self.jinja_env.get_template(f'{self.sort_function_template_name}.jinja').render(qualifiers=qualifiers, endpoint_class=self.class_name)

    def build_filter_function_code(self, filter_tuples: list[tuple[str, str, bool, str]]) -> str:
        return self.jinja_env.get_template(f'{self.filter_function_template_name}.jinja').render(filter_tuples=filter_tuples, endpoint_class=self.class_name)

    def __init__(self, jinja_env: environment, path: str, info: dict):
        self.path = path
        self.info = info
        self.jinja_env = jinja_env
        self.has_id_param = False
        self.is_relationship = False
        self.operation_get = None
        self.fields_enums = {}
        self.fields_function_code: str = None
        self.exists_function_code = None
        self.sort_function_code: str = None
        self.filter_function_code: str = None
        self.limit_function_code: str = None
        self.include_function_code: str = None
        self.include_names = []
        self.operation_get: self.GetOperation = None
        self.enums = {}

        # Eample path: /v1/users/{id}/relationships/visibleApps
        path_comp = path.split('/')
        
        root_endpoint_name = path_comp[2]
        assert root_endpoint_name.endswith('s'), f'Invalid root endpoint ({root_endpoint_name}) in path {path}'

        self.parent_class_name = None

        if '{id}' in path_comp:
            self.__parse_parameters(path, info['parameters'])

            method = simple_singular(root_endpoint_name)
            class_name = capfirst(method)

            self.params = [{'name': 'id', 'type': 'str'}]

            if path_comp[-1] == '{id}':
                # /v1/users/{id}
                pass
            else:
                # /v1/users/{id}/relationships/visibleApps or /v1/users/{id}/visibleApps
                assert len(path_comp) == 6 and 'relationships' in path_comp or len(path_comp) == 5,\
                        f'Invalid path ({path}) in path {path}'

                self.parent_class_name = class_name

                # visibleApps
                child_endpoint_name = path_comp[-1]

                if child_endpoint_name.endswith('s'):
                    # visibleApps -> visibleAppList
                    method = simple_singular(child_endpoint_name) + 'List'
                else:
                    method = child_endpoint_name

                # VisibleAppListOfUser
                class_name = f'{capfirst(method)}Of{class_name}'

                if path_comp[-2] == 'relationships':
                    self.is_relationship = True
                    # VisibleAppOfUserRelationships
                    class_name = f'{class_name}Relationships'

                method = simple_singular(class_name)
        else:
            assert 'parameters' not in info, f"Can't have parameters in path {path}"
            method = simple_singular(root_endpoint_name) + 'List'
            class_name = capfirst(method)

        self.class_name = class_name + 'Endpoint'
        self.method = method

        if 'get' in info:
            info_get = info['get']
            assert all(subkey in ['parameters', 'responses', 'tags', 'operationId', 'deprecated'] for subkey in info_get.keys()), f'Invalid keys in operation `get` in path {self.path}'
            assert '200' in info_get['responses'], f'Get operation must have 200 response in path {self.path}'

            self.__parse_operation_parameters('get', info_get)
            deprecated, response_type, response_single_instance, response_comment = self.__parse_operation_responses('get', info_get)
            self.operation_get = self.GetOperation(deprecated, response_type, response_single_instance, response_comment)

        if 'post' in info:
            info_post = info['post']
            assert all(subkey in ['requestBody', 'responses', 'tags', 'operationId', 'deprecated'] for subkey in info_post.keys()), f'Invalid keys in operation `post` in path {self.path}'
            assert '201' in info_post['responses'] or '204' in info_post['responses'], f'Post operation must have 201 or 204 response in path {self.path}'

            request_type, request_single_instance, request_comment = self.__parse_operation_request_body('post', info_post)
            deprecated, response_type, response_single_instance, response_comment = self.__parse_operation_responses('post', info_post)
            self.operation_post = self.PostOperation(deprecated, response_type, response_single_instance, response_comment, request_type, request_single_instance, request_comment)

        if 'patch' in info:
            info_patch = info['patch']
            assert all(subkey in ['requestBody', 'responses', 'tags', 'operationId', 'deprecated'] for subkey in info_patch.keys()), f'Invalid keys in operation `patch` in path {self.path}'
            assert '200' in info_patch['responses'] or '204' in info_patch['responses'], f'Patch operation must have 200 or 204 response in path {self.path}'

            request_type, request_single_instance, request_comment = self.__parse_operation_request_body('patch', info_patch)
            deprecated, response_type, response_single_instance, response_comment = self.__parse_operation_responses('patch', info_patch)
            self.operation_patch = self.PatchOperation(deprecated, response_type, response_single_instance, response_comment, request_type, request_single_instance, request_comment)

        if 'delete' in info:
            info_delete = info['delete']

            assert all(subkey in ['requestBody', 'responses', 'tags', 'operationId', 'deprecated'] for subkey in info_delete.keys()), f'Invalid keys in operation `delete` in path {self.path}'

            assert '204' in info_delete['responses'], f'Delete operation must have a 204 response in path {self.path}'
            assert info_delete['responses']['204']['description'] == 'Success (no content)', f'Delete operation should not have content, path: {self.path}'

            if 'requestBody' not in info_delete:
                self.operation_delete = self.DeleteOperation(False, None, None, None)
            else:
                request_type, request_single_instance, request_comment = self.__parse_operation_request_body('delete', info_delete)
                deprecated, response_type, response_single_instance, response_comment = self.__parse_operation_responses('delete', info_delete)
                self.operation_delete = self.DeleteOperation(deprecated, request_type, request_single_instance, request_comment)

    def __parse_parameters(self, path, params_info: dict):
        assert len(params_info) == 1, f'Invalid number of parameters in path {path}'
        param = params_info[0]

        assert param['in'] == 'path' and param['name'] == 'id' and param['style'] == 'simple' and param['required'] == True and param['schema']['type'] == 'string', f'Invalid parameter in path {path}'

        self.has_id_param = True
    
    def __parse_operation_request_body(self, operation_name: str, info: dict) -> tuple[str, bool, str]:
        request_body = info['requestBody']
        assert request_body['required'] == True, f'Request body in operation {operation_name} in path {self.path} must be required'

        description = request_body['description']
        single_instance = not description.startswith('List of ')
        ref = request_body['content']['application/json']['schema']['$ref']
        type = ref.split('/')[-1]
        return type, single_instance, description
    
    def __parse_operation_parameters(self, operation_name: str, info: dict):
        assert operation_name == 'get', f'`parameters` is only allowed in `get` operation in path {self.path}'
        params = info['parameters']
        fields_tuples = []
        sort_qualifiers = None
        filter_tuples = []
        limit_tuples = []
        exists_names = []

        for param in params:
            assert param['in'] == 'query' and param['style'] == 'form', f'Invalid parameter in path {self.path}'
            param_name = param['name']
            assert param.get('explode', False) == False, f'Parameter {param_name} in path {self.path} must not be exploded'

            if not param_name.startswith('filter['):
                assert param.get('required', False) == False, f'Parameter `{param_name}: only filter parameters in path {self.path} must be required'

            # TODO: mark 'required' - Parameter filter[app] in path /v1/betaAppReviewDetails
            # print(f'Parameter {param_name} in path {self.path} is required')

            if param_name.startswith('fields['):
                fields_tuple = self.__parse_fields(param_name, param)
                fields_tuples.append(fields_tuple)
            elif param_name == 'sort':
                assert sort_qualifiers is None, f'Can\'t have multiple sort qualifiers in path {self.path}'
                sort_qualifiers = self.__parse_sort(param)
            elif param_name.startswith('filter['):
                filter_tuple = self.__parse_filter(param_name, param)
                filter_tuples.append(filter_tuple)
            elif param_name == 'limit' or param_name.startswith('limit['):
                assert param['schema']['type'] == 'integer', f'Invalid limit parameter in path {self.path}'

                limit_tuple = self.__parse_limit(param_name, param)
                limit_tuples.append(limit_tuple)
            elif param_name.startswith('exists['):
                exists_name = self.__parse_exists(param_name, param)
                exists_names.append(exists_name)
            elif param_name == 'include':
                self.include_names = self.__parse_include(param)
            else:
                assert False, f'Can\'t parse parameter `{param_name}` in path {self.path}'

        if len(fields_tuples) > 0:
            self.fields_function_code = self.build_fields_function_code(fields_tuples)

        if len(exists_names) > 0:
            self.exists_function_code = self.build_exists_function_code(exists_names)

        if sort_qualifiers and len(sort_qualifiers) > 0:
            self.sort_function_code = self.build_sort_function_code(sort_qualifiers)

        if len(filter_tuples) > 0:
            self.filter_function_code = self.build_filter_function_code(filter_tuples)

        if len(limit_tuples) > 0:
            self.limit_function_code = self.build_limit_function_code(limit_tuples)

        if len(self.include_names) > 0:
            self.include_function_code = self.build_include_function_code(self.include_names)

    def __parse_operation_responses(self, operation_name: str, info: dict) -> tuple[bool, str, bool, str]:
        deprecated = info.get('deprecated', False)
        response_type: str = None
        single_instance = None
        description = None

        responses = info['responses']
        for code, resp in responses.items():
            if code.startswith('20'):
                description = resp.get('description', '')
                if description.startswith('List of '):
                    single_instance = False
                elif description.startswith('Single ') or description=='Related resource' or description=='Related linkage':
                    single_instance = True
                elif description == 'Success (no content)':
                    single_instance = None
                else:
                    assert False, f'Invalid response description `{description}` in path {self.path}'

                if 'content' in resp:
                    if 'application/json' in resp['content']:
                        assert "$ref" in resp['content']['application/json']['schema'], f'Invalid response in path {self.path}'
                        response_type = resp['content']['application/json']['schema']['$ref'].split('/')[-1]
                    elif 'gzip' in resp['content']:
                        schema = resp['content']['gzip']['schema']
                        assert schema['type'] == 'string' and schema['format'] == 'binary', f'Invalid response in operation {operation_name} in path {self.path}'
                        response_type = 'bytes'
                    else:
                        assert False, f'Invalid response in operation {operation_name} in path {self.path}'
            elif code in ['400', '403', '404', '409']:
                error_type = resp['content']['application/json']['schema']['$ref'].split('/')[-1]
                assert error_type == 'ErrorResponse', f'Invalid response error type `{error_type}` in path {self.path}'
            else:
                assert False, f'Invalid response code `{code}` in path {self.path}'

        return (deprecated, response_type, single_instance, description)

    def __parse_include(self, info: dict) -> list[str]:
        assert info['schema']['type'] == 'array', f'Invalid include parameter in path {self.path}'
        assert info['schema']['items']['type'] == 'string', f'Invalid include parameter in path {self.path}'
        assert info['style'] == 'form', f'Invalid include parameter in path {self.path}'
        assert info['in'] == 'query', f'Invalid include parameter in path {self.path}'
        assert 'required' not in info or info['required'] == False, f'Invalid include parameter in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid include parameter in path {self.path}'

        return info['schema']['items']['enum']

    def __parse_fields(self, name: str, info: dict) -> tuple[str, str]:
        assert info['schema']['type'] == 'array', f'Invalid field in path {self.path}'
        assert info['schema']['items']['type'] == 'string', f'Invalid field in path {self.path}'
        assert info['in'] == 'query', f'Invalid field in path {self.path}'
        assert info['style'] == 'form', f'Invalid field in path {self.path}'
        assert 'required' not in info or info['required'] == False, f'Invalid field in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid field in path {self.path}'
        assert 'description' in info, f'Field parameter `{name}` without description in path {self.path}'

        try:
            # fields[appCategories]
            fields_name = re.search(r'fields\[(.+?)\]', name).group(1)
        except:
            assert False, f'Invalid field `{name}` in path {self.path}'

        self.fields_enums[fields_name] = info['schema']['items']['enum']
        return fields_name, info['description']

    def __parse_sort(self, info: dict) -> list[str]:
        assert info['schema']['type'] == 'array', f'Invalid field in path {self.path}'
        assert info['schema']['items']['type'] == 'string', f'Invalid field in path {self.path}'
        assert info['in'] == 'query', f'Invalid field in path {self.path}'
        assert info['style'] == 'form', f'Invalid field in path {self.path}'
        assert 'required' not in info or info['required'] == False, f'Invalid field in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid field in path {self.path}'
        qualifiers = info['schema']['items']['enum']
        compact_qualifiers = [q for q in qualifiers if not q.startswith('-')]

        # Make sure that all qualifiers have both assending and descending order
        for q in qualifiers:
            assert not q.startswith('+'), f'Invalid qualifier `{q}` in path {self.path}'
            if q.startswith('-'):
                assert q.removeprefix('-') in qualifiers, f'Invalid qualifier `{q}` in path {self.path}'
            else:
                assert '-' + q in qualifiers, f'Invalid qualifier `{q}` in path {self.path}'

        return compact_qualifiers

    def __parse_limit(self, name: str, info: dict) -> tuple[str, int, str]:
        assert info['schema']['type'] == 'integer', f'Invalid limit parameter in path {self.path}'
        assert info['in'] == 'query', f'Invalid limit parameter in path {self.path}'
        assert info['style'] == 'form', f'Invalid limit parameter in path {self.path}'
        assert 'required' not in info or info['required'] == False, f'Invalid limit parameter in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid limit parameter in path {self.path}'
        assert 'description' in info, f'Limit parameter without description in path {self.path}'

        try:
            # 'limit[subcategories]' or just 'limit'
            if name == 'limit':
                limit_name = 'default-limit'
            else:
                limit_name = re.search(r'limit\[(.+?)\]', name).group(1)
        except:
            assert False, f'Invalid limit parameter `{name}` in path {self.path}'

        return limit_name, info['schema']['maximum'], info['description']
    
    def __parse_filter(self, name: str, info: dict) -> tuple[str, str, bool, str]:
        assert info['schema']['type'] == 'array', f'Invalid filter in path {self.path}'
        assert info['schema']['items']['type'] == 'string', f'Invalid filter in path {self.path}'
        assert info['in'] == 'query', f'Invalid filter in path {self.path}'
        assert info['style'] == 'form', f'Invalid filter in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid filter in path {self.path}'
        assert 'description' in info, f'Filter parameter without description in path {self.path}'

        try:
            # filter[appStoreVersions.platform]
            filter_name = re.search(r'filter\[(.+?)\]', name).group(1)
        except:
            assert False, f'Invalid filter `{name}` in path {self.path}'

        filter_item_type = info['schema']['items']['type']
        if 'enum' in info['schema']['items']:
            filter_trace = f'{self.class_name}.{filter_name}'

            if filter_trace in ['FinanceReportListEndpoint.reportType', 'SalesReportListEndpoint.frequency', 'SalesReportListEndpoint.reportType', 'SalesReportListEndpoint.reportSubType']:
                # Embeds enums of those filters
                filter_item_type = capfirst(filter_name)
                self.enums[filter_item_type] = info['schema']['items']['enum']
            else:
                filter_item_type = self._filter_enum_map[filter_trace]

        required = info['required'] if 'required' in info else False
        return (filter_name, self.filter_type_code(filter_item_type), required, info['description'])
    
    def __parse_exists(self, name: str, info: dict) -> str:
        assert info['schema']['type'] == 'array', f'Invalid exists parameter in path {self.path}'
        assert info['schema']['items']['type'] == 'string', f'Invalid exists parameter in path {self.path}'
        assert info['in'] == 'query', f'Invalid exists parameter in path {self.path}'
        assert info['style'] == 'form', f'Invalid exists parameter in path {self.path}'
        assert 'required' not in info or info['required'] == False, f'Invalid exists parameter in path {self.path}'
        assert 'explode' not in info or info['explode'] == False, f'Invalid exists parameter in path {self.path}'

        try:
            # exists[releaseWithAppStoreVersion]
            exists_name = re.search(r'exists\[(.+?)\]', name).group(1)
        except:
            assert False, f'Invalid exists parameter `{name}` in path {self.path}'

        return exists_name

    @abstractmethod
    def filter_enum_type(name: str) -> str:
        pass

    def build(self) -> str:
        pass
        