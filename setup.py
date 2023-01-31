import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jupyterhub-gcp-iap-authenticator",
    python_requires='>=3.6.0',
    version="0.1.0",
    author="Tom Tang",
    author_email="tly1980@gmail.com",
    description="JupyterHub authenticator for Cloud IAP. Works for JupyterHub 3.0+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GoogleCloudPlatform/jupyterhub-gcp-proxies-authenticator",
    packages=setuptools.find_packages(),
    license='Apache 2.0',
    install_requires=[
        "jupyterhub",
        "tornado>=5.0",
        'pyjwt>=1.7.1'
    ],
    entry_points={
        'jupyterhub.authenticators': [
            'gcp_iap_auth = gcpiapauthenticator.gcpiapauthenticator:GCPIAPAuthenticator'
        ]
    },
)
