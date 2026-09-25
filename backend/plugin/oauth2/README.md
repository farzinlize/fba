# OAuth2

OAuth 2.0 login plugin supporting social platforms such as GitHub and Google.

- Log in through GitHub or Google.
- Link and unlink third-party accounts.
- Configure redirects after login and account linking.

## Plugin type

- Application-level plugin

## Configuration

Add the following to `backend/.env`:

```env
# [ Plugin ] oauth2
OAUTH2_GITHUB_CLIENT_ID='test'
OAUTH2_GITHUB_CLIENT_SECRET='test'
OAUTH2_GOOGLE_CLIENT_ID='test'
OAUTH2_GOOGLE_CLIENT_SECRET='test'
```

The `[settings]` section of the plugin directory `plugin.toml` contains:

```toml
[settings]
OAUTH2_FRONTEND_BINDING_REDIRECT_URI = 'http://localhost:5173/profile'
OAUTH2_FRONTEND_LOGIN_REDIRECT_URI = 'http://localhost:5173/oauth2/callback'
OAUTH2_GITHUB_REDIRECT_URI = 'http://127.0.0.1:8000/api/v1/oauth2/github/callback'
OAUTH2_GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8000/api/v1/oauth2/google/callback'
OAUTH2_STATE_EXPIRE_SECONDS = 180
OAUTH2_STATE_REDIS_PREFIX = 'fba:oauth2:state'
```

The project `backend/core/conf.py` already includes these fields:

```python
##################################################
# [ Plugin ] oauth2
##################################################
# .env
OAUTH2_GITHUB_CLIENT_ID: str
OAUTH2_GITHUB_CLIENT_SECRET: str
OAUTH2_GOOGLE_CLIENT_ID: str
OAUTH2_GOOGLE_CLIENT_SECRET: str

# Base configuration (in plugin.toml)
OAUTH2_STATE_REDIS_PREFIX: str
OAUTH2_STATE_EXPIRE_SECONDS: int
OAUTH2_GITHUB_REDIRECT_URI: str
OAUTH2_GOOGLE_REDIRECT_URI: str
OAUTH2_FRONTEND_LOGIN_REDIRECT_URI: str
OAUTH2_FRONTEND_BINDING_REDIRECT_URI: str
```

## Settings

- `OAUTH2_FRONTEND_BINDING_REDIRECT_URI`: Frontend redirect URL after account linking.
- `OAUTH2_FRONTEND_LOGIN_REDIRECT_URI`: Frontend redirect URL after third-party login.
- `OAUTH2_GITHUB_REDIRECT_URI`: GitHub OAuth callback URL.
- `OAUTH2_GOOGLE_REDIRECT_URI`: Google OAuth callback URL.
- `OAUTH2_STATE_EXPIRE_SECONDS`: OAuth state lifetime.
- `OAUTH2_STATE_REDIS_PREFIX`: Redis key prefix for OAuth state.

## Usage

1. Install and enable the plugin, then create OAuth applications on GitHub and Google.
2. Add the assigned Client IDs and Client Secrets to the project environment variables.
3. Ensure the platform callback URLs match `OAUTH2_GITHUB_REDIRECT_URI` and `OAUTH2_GOOGLE_REDIRECT_URI`.
4. Configure frontend redirects for login and account linking.
5. Restart the backend service, then use third-party login, account linking, and unlinking.

## Uninstallation

- After uninstalling, remove related environment variables, base settings, and plugin settings from `backend/core/conf.py`.
- Remove third-party login and account linking integrations from the frontend login page or profile page.

## Contact

- Author: `wu-clan`
- Feedback: Submit an issue or pull request.
