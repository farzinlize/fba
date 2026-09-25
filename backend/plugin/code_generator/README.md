# Code Generator

Code generator plugin for common business code.

- Maintain code generation business configuration and model column information.
- Generate common business code manually or by automatically importing database tables.
- Preview, write, and download generated code.

## Plugin type

- Application-level plugin

## Configuration

The `[settings]` section of the plugin directory `plugin.toml` contains:

```toml
[settings]
CODE_GENERATOR_DOWNLOAD_ZIP_FILENAME = 'fba_generator'
```

The project `backend/core/conf.py` already includes these fields:

```python
##################################################
# [ Plugin ] code_generator
##################################################
CODE_GENERATOR_DOWNLOAD_ZIP_FILENAME: str
```

## Settings

- `CODE_GENERATOR_DOWNLOAD_ZIP_FILENAME`: Filename of the downloadable generated-code archive.

## Usage

1. Install and enable the plugin, then restart the backend service.
2. Maintain business configuration and model column information.
3. Preview, generate, and download code.
4. Generated code is written directly to disk; use this only in development.

## Uninstallation

- After uninstalling, remove related base settings and plugin settings from `backend/core/conf.py`.
- Remove any code generation pages or automation integrations that depend on this plugin.

## Contact

- Author: `wu-clan`
- Feedback: Submit an issue or pull request.
