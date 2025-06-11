import time
import logging
from datetime import datetime, time as dt_time
from dotenv import load_dotenv
from telegram_bot import TelegramBot
from config import Config
from market_monitor import MarketMonitor
from keep_alive import keep_alive

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('market_bot.log'),
              logging.StreamHandler()])

logger = logging.getLogger(__name__)


def format_market_message(title, price_data, movers_data):
    change_emoji = "📈" if price_data['change_percent'] >= 0 else "📉"
    sign = "+" if price_data['change_percent'] >= 0 else ""

    message = f"""
📊 {title}

💰 Preço atual: ${price_data['price']:.2f}
{change_emoji} Variação: {sign}{price_data['change']:.2f} ({sign}{price_data['change_percent']:.2f}%)"""

    if movers_data:
        if 'top_gainer' in movers_data:
            g = movers_data['top_gainer']
            message += f"\n🟢 Maior Alta: {g['name']} ({g['symbol']}) +{g['change_percent']:.2f}%"
        if 'top_loser' in movers_data:
            l = movers_data['top_loser']
            message += f"\n🔴 Maior Queda: {l['name']} ({l['symbol']}) {l['change_percent']:.2f}%"

    message += f"\n\n🕒 {price_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
    return message


def main():
    config = Config()
    bot = TelegramBot(config.telegram_token, config.telegram_chat_id)
    logger.info("\u2705 Bot de monitoramento iniciado")

    indices = {
        "S&P 500": {
            "symbol": "^GSPC",
            "reference_stocks":
            ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "META"]
        },
        "Nasdaq": {
            "symbol": "^IXIC",
            "reference_stocks":
            ["AMZN", "AAPL", "NVDA", "ADBE", "INTC", "TSLA"]
        },
        "Dow Jones": {
            "symbol": "^DJI",
            "reference_stocks": ["JNJ", "WMT", "PG", "UNH", "HD", "V"]
        }
    }

    last_alert_hour = None

    while True:
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            market_open = dt_time(14, 30)
            market_close = dt_time(21, 0)

            if current_time.weekday(
            ) < 5 and market_open <= current_time.time() <= market_close:
                if last_alert_hour != current_hour:
                    messages = []
                    for key in indices:
                        symbol = indices[key]["symbol"]
                        stocks = indices[key]["reference_stocks"]
                        monitor = MarketMonitor(symbol, stocks)
                        price_data = monitor.get_current_price()
                        movers_data = monitor.get_top_movers()

                        if price_data:
                            message = format_market_message(
                                key, price_data, movers_data)
                            messages.append(message)

                    full_message = "\n\n".join(messages)
                    if bot.send_message(full_message):
                        last_alert_hour = current_hour
                        logger.info("Mensagem enviada com sucesso")
                else:
                    logger.info("Mensagem já enviada nesta hora")
            else:
                logger.info(
                    "⏱ Fora do horário da bolsa - nenhuma mensagem enviada")

        except Exception as e:
            logger.error(f"Erro no loop principal: {str(e)}")

        time.sleep(60)


if __name__ == "__main__":
    keep_alive()
    main()


