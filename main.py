import time
import logging
from datetime import datetime, time as dt_time
from dotenv import load_dotenv
from market_monitor import MarketMonitor
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


def format_alert_message(index_name, price_data, movers_data, timestamp):
    change_emoji = "📈" if price_data['change_percent'] >= 0 else "📉"
    sign = "+" if price_data['change_percent'] >= 0 else ""

    message = f"""📊 **{index_name}**

💰 **Preço atual:** ${price_data['price']:.2f}
{change_emoji} **Variação:** {sign}{price_data['change']:.2f} ({sign}{price_data['change_percent']:.2f}%)
"""

    if movers_data:
        g = movers_data['top_gainer']
        l = movers_data['top_loser']
        message += f"""🟢 **Maior Alta:** {g['name']} ({g['symbol']}) +{g['change_percent']:.2f}%
🔴 **Maior Queda:** {l['name']} ({l['symbol']}) {l['change_percent']:.2f}%"""

    message += f"\n\n🕒 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    return message


def main():
    config = Config()
    telegram_bot = TelegramBot(config.telegram_token, config.telegram_chat_id)

    indices = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones"}

    monitors = {symbol: MarketMonitor(symbol) for symbol in indices}
    last_alert_hour = None

    logger.info("Bot de monitoramento iniciado")

    while True:
        try:
            current_time = datetime.now()
            current_hour = current_time.hour

            market_open = dt_time(14, 30)
            market_close = dt_time(21, 0)

            if current_time.weekday(
            ) < 5 and market_open <= current_time.time() <= market_close:
                if last_alert_hour != current_hour:
                    full_message = "🔔 **Atualização de Mercado**\n"

                    for symbol, name in indices.items():
                        monitor = monitors[symbol]
                        price_data = monitor.get_current_price()
                        movers_data = monitor.get_top_movers()

                        if price_data:
                            message = format_alert_message(
                                name, price_data, movers_data, current_time)
                            full_message += f"\n\n{message}"
                        else:
                            full_message += f"\n\n⚠️ Falha ao obter dados de {name}"

                    if telegram_bot.send_message(full_message):
                        last_alert_hour = current_hour
                        logger.info(f"Mensagem enviada às {current_hour}h")

            else:
                logger.info(
                    "⏱ Fora do horário da bolsa - nenhuma mensagem enviada")

        except Exception as e:
            logger.error(f"Erro no loop principal: {str(e)}")

        time.sleep(60)


if __name__ == "__main__":
    keep_alive()
    main()

