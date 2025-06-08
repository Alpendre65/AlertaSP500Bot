import time
import logging
from datetime import datetime, time as dt_time
from dotenv import load_dotenv
from sp500_monitor import SP500Monitor
from telegram_bot import TelegramBot
from config import Config
from keep_alive import keep_alive

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('sp500_bot.log'),
              logging.StreamHandler()])

logger = logging.getLogger(__name__)


def format_alert_message(price_data, timestamp, movers_data=None):
    change_emoji = "📈" if price_data['change_percent'] >= 0 else "📉"
    sign = "+" if price_data['change_percent'] >= 0 else ""

    message = f"""🔔 **S&P 500 Hourly Update**

💰 **Current Price:** ${price_data['price']:.2f}
{change_emoji} **Change:** {sign}{price_data['change']:.2f} ({sign}{price_data['change_percent']:.2f}%)"""

    if movers_data:
        message += "\n\n📊 **Market Movers:**"

        if 'top_gainer' in movers_data:
            g = movers_data['top_gainer']
            message += f"\n🟢 **Top Gainer:** {g['name']} ({g['symbol']}) +{g['change_percent']:.2f}%"

        if 'top_loser' in movers_data:
            l = movers_data['top_loser']
            message += f"\n🔴 **Top Loser:** {l['name']} ({l['symbol']}) {l['change_percent']:.2f}%"

    message += f"\n\n📅 **Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n*Powered by Yahoo Finance*"
    return message


def main():
    config = Config()
    sp500_monitor = SP500Monitor()
    telegram_bot = TelegramBot(config.telegram_token, config.telegram_chat_id)

    logger.info("Bot de monitoramento do S&P 500 iniciado")
    last_alert_hour = None

    while True:
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # Horário de funcionamento da bolsa (horário de Lisboa)
            market_open = dt_time(14, 30)
            market_close = dt_time(21, 0)

            if current_time.weekday(
            ) < 5 and market_open <= current_time.time() <= market_close:
                price_data = sp500_monitor.get_current_price()

                if price_data:
                    logger.info(
                        f"Preço atual do S&P 500 : $ {price_data['price']:.2f}"
                    )

                    if last_alert_hour != current_hour:
                        movers_data = sp500_monitor.get_top_movers()
                        message = format_alert_message(price_data,
                                                       current_time,
                                                       movers_data)

                        if telegram_bot.send_message(message):
                            last_alert_hour = current_hour
                            logger.info(
                                f"Alerta enviado para a hora {current_hour}")
                else:
                    logger.warning("Falha ao obter dados do S&P 500")
            else:
                logger.info(
                    "⏱ Fora do horário da bolsa - nenhuma mensagem enviada")

        except Exception as e:
            logger.error(f"Erro no loop principal: {str(e)}")

        time.sleep(60)


if __name__ == "__main__":
    keep_alive()
    main()

