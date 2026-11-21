<!-- pack-python:override rule=pydantic by=python-web -->
### Web profile — settings and validation

- Configuration comes from Django settings; do not add `pydantic-settings`.
- Form input is validated by Django Forms/ModelForms at the request boundary.
- Pydantic remains the default for DTOs that cross a non-form boundary (JSON endpoints, service payloads, background jobs).
<!-- /pack-python:override -->
