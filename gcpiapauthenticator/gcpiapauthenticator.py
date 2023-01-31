
from jupyterhub.auth import Authenticator

from traitlets import Unicode

import jwt
import requests

class GCPIAPAuthenticator(Authenticator):

    auto_login = True

    login_service = 'gcp_iap_auth'

    check_header = Unicode(
        default_value='X-Goog-IAP-JWT-Assertion',
        config=True,
        help=""" Name of the header with GCP IAP JWT token""",
    )

    project_id = Unicode(
        '',
        config=True,
        help=""" Project id. """,
    )

    project_number = Unicode(
        '',
        config=True,
        help=""" Project number. """,
    )

    backend_service_name = Unicode(
        '',
        config=True,
        help=""" Name of the backend service where JupyterHub is deployed. Used
        with project_id, gets the backend service ID required to verify IAP.""",
    )

    backend_service_id = Unicode(
        '',
        config=True,
        help=""" An integer of the backend_service_id.""",
    )

    template_to_render = Unicode(
        config=True,
        help=""" HTML page to render once the user is authenticated. For example
        'welcome.html'. """
    )

    async def authenticate(self, handler, data):
        """Verify from GCP IAP Proxy JWT token.  """

        self.log.info('using authenticate function')

        _, user_email, _ = validate_iap_jwt_from_compute_engine(
            handler.request.headers.get(self.check_header, ""),
            self.project_number,
            self.backend_service_id
        )

        self.log.info(f'user_email: {user_email}')

        if user_email:
            username = user_email.lower().split("@")[0]
            user = {
                'name': username,
                'auth_state': {},
            }

            self.log.info(f'GCP IAP JWT token verifid, user is: {user}')
            return user


# Cloud IAP related functions.
# Validata IAP header values and extract the user email.

def validate_iap_jwt_from_compute_engine(iap_jwt, cloud_project_number,
                                         backend_service_id):
    """ Validates an IAP JWT for your (Compute|Container) Engine service.

    Args:
      iap_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.
      cloud_project_number: The project *number* for your Google Cloud project.
          This is returned by 'gcloud projects describe $PROJECT_ID', or
          in the Project Info card in Cloud Console.
      backend_service_id: The ID of the backend service used to access the
          application. See
          https://cloud.google.com/iap/docs/signed-headers-howto
          for details on how to get this value.

    Returns:
      (user_id, user_email, error_str).
    """
    expected_audience = '/projects/{}/global/backendServices/{}'.format(
        cloud_project_number, backend_service_id)
    return _validate_iap_jwt(iap_jwt, expected_audience)


def _validate_iap_jwt(iap_jwt, expected_audience):
    try:
        key_id = jwt.get_unverified_header(iap_jwt).get('kid')
        if not key_id:
            return (None, None, '**ERROR: no key ID**')
        key = get_iap_key(key_id)
        decoded_jwt = jwt.decode(
            iap_jwt, key,
            algorithms=['ES256'],
            issuer='https://cloud.google.com/iap',
            audience=expected_audience)
        return (decoded_jwt['sub'], decoded_jwt['email'], '')
    except (jwt.exceptions.InvalidTokenError,
            requests.exceptions.RequestException) as e:
        return (None, None, '**ERROR: JWT validation error {}**'.format(e))


def get_iap_key(key_id):
    """Retrieves a public key from the list published by Identity-Aware Proxy,
    re-fetching the key file if necessary.
    """
    key_cache = get_iap_key.key_cache
    key = key_cache.get(key_id)
    if not key:
        # Re-fetch the key file.
        resp = requests.get(
            'https://www.gstatic.com/iap/verify/public_key')
        if resp.status_code != 200:
            raise Exception(
                'Unable to fetch IAP keys: {} / {} / {}'.format(
                    resp.status_code, resp.headers, resp.text))
        key_cache = resp.json()
        get_iap_key.key_cache = key_cache
        key = key_cache.get(key_id)
        if not key:
            raise Exception('Key {!r} not found'.format(key_id))
    return key


# Used to cache the Identity-Aware Proxy public keys.  This code only
# refetches the file when a JWT is signed with a key not present in
# this cache.
get_iap_key.key_cache = {}
