# applaudgen

`applaudgen` parses [App Store Connect specification file](https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip) and generates client library for accessing [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi).

For the generated Python client library, navigate to [applaud](https://github.com/codinn/applaud).

## Motivation

At [Codinn](https://codinn.com), we have two apps distribute on App Store – [Core Shell](https://apps.apple.com/cn/app/core-shell/id1354319581?l=en&mt=12) and [Core Tunnel](https://apps.apple.com/cn/app/core-tunnel/id1354318707?l=en&mt=12). We wrote a bunch of scripts to automate the build, package and upload processes, we benefit from the automation scripts and it saves a lot of time.

For the app information (localized descriptions, versions, changelogs and other meta data) in App Store, we maintained it manually for a very long time. But this can easily go wrong, we made a few horrible mistakes while updating the information, e.g., pasted the description of Core Shell to Core Tunnel, using Spanish changelog for English localization, forgot update site links.

We decided to adopt App Store Connect API to automate app information updating process as well, but soon discovered that it lacks client support. Most client libraries implement a very small portion of the API, provide very limited operations.

We surprisingly found that App Store Connect API uses and conforms to OpenAPI specification, it shouldn't be too hard to generate client code from the specification. So we create project `applaudgen` for this purpose, and its masterpiece – project [applaud](https://github.com/codinn/applaud).

## Prerequisites

This project is written in Python, and uses [Poetry](https://python-poetry.org/) for packaging and dependency management. You should have [Poetry installed](https://python-poetry.org/docs/#installation) if you want to contribute to the Python code in this repository.

## Usage

The `applaudgen` command:
```
usage: applaudgen.py [-h] [-s SPEC_FILE] [-o OUTPUT_DIR]

Generate Python SDK code for the App Store Connect API.

optional arguments:
  -h, --help            show this help message and exit
  -s SPEC_FILE, --spec SPEC_FILE
                        Path to the App Store Connect API specification file.
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Path to the package output directory.
```

`SPEC_FILE` defaults to `app_store_connect_api.json` under project root, which is the latest supported version (1.6 at present) of App Store Connect specification file.

`OUTPUT_DIR` defaults to `./PythonPackage`.

## Compare to other OpenAPI client generators

Code generated by most OpenAPI client generators are not as elegant as `applaudgen`.

For example, App Store Connect API has tons of inner schemas like `[UserUpdateRequest.Data.Attributes](https://developer.apple.com/documentation/appstoreconnectapi/userupdaterequest/data/attributes)` and `[AppInfoLocalizationCreateRequest.Data.Relationships.AppInfo.Data](https://developer.apple.com/documentation/appstoreconnectapi/appinfolocalizationcreaterequest/data/relationships/appinfo/data)`. [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) creates numerous schema classes `Data1`, `Data2` … for each inner `Data` schema.

On the contrary, `applaudgen` creates inner classes to align with App Store Connect API documentation perfectly:
```
class UserUpdateRequest(ApplaudModel):
    class Data(ApplaudModel):
        class Attributes(ApplaudModel):
            roles: Optional[list[UserRole]]
            all_apps_visible: Optional[bool]
            provisioning_allowed: Optional[bool]

        class Relationships(ApplaudModel):
            class VisibleApps(ApplaudModel):
                class Data(ApplaudModel):
                    id: str
                    type: Literal["apps"] = "apps"

                data: Optional[list[Data]]

            visible_apps: Optional[VisibleApps]

        id: str
        type: Literal["users"] = "users"
        attributes: Optional[Attributes]
        relationships: Optional[Relationships]

    data: Data
```

A common pitfall of generic OpenAPI client generators is rigid, inflexible. Take an example, [ErrorResponse](https://developer.apple.com/documentation/appstoreconnectapi/errorresponse) is a schema of course, but `applaudgen` wrap it into an exception for you without write extra code:

```
connection = ApplaudConnection(APPSTORE_ISSUER_ID, APPSTORE_KEY_ID, APPSTORE_PRIVATE_KEY)

try:
    response = connection.beta_tester_invitation_list().create(…)
except EndpointException as err:
    already_accepted_error = False
    for e in err.errors:
        if e.code == 'STATE_ERROR.TESTER_INVITE.ALREADY_ACCEPTED':
            # silent this error
            already_accepted_error = True
            break

    if not already_accepted_error:
        raise err
```

You always get a correct response on success, or an exception otherwise.


Further more, `applaudgen` provides full function yet simple interfaces to perform tasks on App Store Connect:
```
connection = ApplaudConnection(APPSTORE_ISSUER_ID, APPSTORE_KEY_ID, APPSTORE_PRIVATE_KEY)
response = connection.beta_group_list().filter(app=[app_id1, app_id2], name="Example Tester Group", is_internal_group=False).include(BetaGroupListEndpoint.Include.APP).get()

for group in beta_groups.data:
    print(group.id, group.attributes.created_date, group.relationships.app.data.id)
```

Above code lists all **external** beta groups that named `Example Tester Group` in apps with `id`s `app_id1` and `app_id2`, and the response **includes** related corresponding id of the owner app.

## TODO

- [ ] Generates Swift client library
- [ ] Python syntactic sugar to simplify the initialization of deep inner classes
