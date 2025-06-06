import os
import sys
import logging

logger = logging.getLogger(__name__)


class Config:

    def __init__(self):
        self.telegram_token = self._get_env_var('TELEGRAM_TOKEN')
        self.telegram_chat_id = self._get_env_var('TELEGRAM_CHAT_ID')
        self.twelve_data_api_key = self._get_env_var('TWELVE_DATA_API_KEY')

        # Validação opcional
        self._validate()

    def _get_env_var(self, name):
        value = os.getenv(name)
        if not value:
            logger.error(f"Environment variable {name} is not set")
            sys.exit(1)
        return value

    def _validate(self):
        logger.info("Configuration validated successfully")
