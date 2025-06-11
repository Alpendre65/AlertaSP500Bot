import logging
import requests

logger = logging.getLogger(__name__)


class TelegramBot:

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(self.api_url, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("Mensagem enviada com sucesso para o Telegram")
            return True
        except requests.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {str(e)}")
            return False

