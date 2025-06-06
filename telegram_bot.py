"""
Telegram bot module for sending S&P 500 alerts
"""

import requests
import logging
from typing import Optional
from utils import retry_on_failure

logger = logging.getLogger(__name__)

class TelegramBot:
    """Class to handle Telegram bot operations"""
    
    def __init__(self, token: str, chat_id: str):
        """
        Initialize Telegram bot
        
        Args:
            token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout = 10
        
        # Test bot connectivity on initialization
        self._test_bot_connection()
    
    def _test_bot_connection(self) -> bool:
        """
        Test if the bot token is valid and can connect to Telegram API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    bot_name = bot_info['result']['first_name']
                    logger.info(f"Telegram bot connected successfully: {bot_name}")
                    return True
                else:
                    logger.error("Telegram bot token is invalid")
                    return False
            else:
                logger.error(f"Failed to connect to Telegram API: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing bot connection: {str(e)}")
            return False
    
    @retry_on_failure(max_retries=3, delay=2)
    def send_message(self, message: str) -> bool:
        """
        Send a message to the configured chat
        
        Args:
            message: Message text to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            logger.debug(f"Sending message to chat {self.chat_id}")
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("Message sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"HTTP error sending message: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while sending Telegram message")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error while sending Telegram message")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return False
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify bot functionality
        
        Returns:
            True if test message was sent successfully, False otherwise
        """
        test_message = "🤖 S&P 500 Monitoring Bot is now active!\n\nYou will receive hourly updates about the S&P 500 index price."
        return self.send_message(test_message)
    
    def get_chat_info(self) -> Optional[dict]:
        """
        Get information about the chat
        
        Returns:
            Chat information or None if failed
        """
        try:
            url = f"{self.base_url}/getChat"
            payload = {'chat_id': self.chat_id}
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat info: {str(e)}")
            return None
