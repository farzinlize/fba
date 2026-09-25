# Email

Email plugin for sending verification codes, notifications, and other emails.

- Send email through SMTP.
- Supports verification codes and notifications.
- Configure the mail server, verification code lifetime, and Redis prefix through base settings.

## Plugin type

- Application-level plugin

## Configuration

Add the following to `backend/.env`:

```env
# [ Plugin ] email
EMAIL_USERNAME=''
EMAIL_PASSWORD=''
```

The `[settings]` section of the plugin directory `plugin.toml` contains:

```toml
[settings]
EMAIL_CAPTCHA_EXPIRE_SECONDS = 180
EMAIL_CAPTCHA_REDIS_PREFIX = 'fba:email:captcha'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
EMAIL_SSL = true
```

The project `backend/core/conf.py` already includes these fields:

```python
##################################################
# [ Plugin ] email
##################################################
# .env
EMAIL_USERNAME: str
EMAIL_PASSWORD: str

# Base configuration (in plugin.toml)
EMAIL_HOST: str
EMAIL_PORT: int
EMAIL_SSL: bool
EMAIL_CAPTCHA_REDIS_PREFIX: str
EMAIL_CAPTCHA_EXPIRE_SECONDS: int
```

## Settings

- `EMAIL_CAPTCHA_EXPIRE_SECONDS`: Email verification code lifetime.
- `EMAIL_CAPTCHA_REDIS_PREFIX`: Redis key prefix for email verification codes.
- `EMAIL_HOST`: SMTP server address.
- `EMAIL_PORT`: SMTP port.
- `EMAIL_SSL`: Whether SSL is enabled.

## Usage

1. Install and enable the plugin, then configure the SMTP account and password.
2. Set `EMAIL_HOST`, `EMAIL_PORT`, and `EMAIL_SSL` according to your email provider.
3. Restart the backend service, then use email through the system interface, Swagger, or business code.

## Uninstallation

- After uninstalling, remove related environment variables, base settings, and plugin settings from `backend/core/conf.py`.
- Remove business code integrations that use the email functionality.

## Contact

- Author: `wu-clan`
- Feedback: Submit an issue or pull request.
