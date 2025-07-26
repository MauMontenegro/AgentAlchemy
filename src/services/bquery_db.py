import os

class BigQueryConfig:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.private_key_id = os.getenv("GCP_PRIVATE_KEY_ID")
        self.private_key = os.getenv("GCP_PRIVATE_KEY", "").replace('\\n', '\n')
        self.client_email = os.getenv("GCP_CLIENT_EMAIL")
        self.client_id = os.getenv("GCP_CLIENT_ID")
    
    def get_credentials_dict(self):
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email.replace('@', '%40')}"
        }