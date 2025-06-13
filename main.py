import time
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
from market_monitor import MarketMonitor
from telegram_bot import TelegramBot
import os
from keep_alive import keep_alive

# Carregar variáveis do .env
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Inicializar bot com variáveis do ambiente
bot = TelegramBot(os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))

# Dicionário com os índices e suas ações de referência
indices = {
    "S&P 500": {
        "symbol": "^GSPC",
        "reference": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"]
    },
    "Nasdaq": {
        "symbol": "^IXIC",
        "reference": ["AAPL", "NVDA", "AMD", "TSLA", "GOOGL", "AMZN"]
    },
    "Dow Jones": {
        "symbol": "^DJI",
        "reference": ["JNJ", "UNH", "PG", "DIS", "HD", "V"]
    }
}


def format_market_message(title, price_data, movers):
    change_emoji = "🔼" if price_data['change_percent'] >= 0 else "🔽"
    sign = "+" if price_data['change_percent'] >= 0 else ""

    message = f"""📊 {title}

💰 Preço atual: ${price_data['price']:.2f}
{change_emoji} Variação: {sign}{price_data['change']:.2f} ({sign}{price_data['change_percent']:.2f}%)
🕒 {price_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"""

    if movers:
        top = movers.get("top_gainer", {})
        bottom = movers.get("top_loser", {})
        if top:
            message += f"\n\n🟢 Maior Alta: {top.get('name', top.get('symbol'))} ({top.get('symbol')}) +{top.get('change_percent', 0):.2f}%"
        if bottom:
            message += f"\n🔴 Maior Queda: {bottom.get('name', bottom.get('symbol'))} ({bottom.get('symbol')}) {bottom.get('change_percent', 0):.2f}%"

    return message


def is_market_open():
    now = datetime.now(pytz.timezone("Europe/Lisbon"))
    return now.weekday() < 5 and 14 <= now.hour < 21


def main():
    last_alert_hour = None

    while True:
        try:
            if is_market_open():
                current_hour = datetime.now(pytz.timezone("Europe/Lisbon")).hour
                if current_hour != last_alert_hour:
                    messages = []
                    for name, data in indices.items():
                        monitor = MarketMonitor(data["symbol"], data["reference"])
                        price = monitor.get_current_price()
                        movers = monitor.get_top_movers()

                        if price:
                            msg = format_market_message(name, price, movers)
                            messages.append(msg)

                    if messages:
                        bot.send_message("\n\n".join(messages))
                        last_alert_hour = current_hour
                        logger.info("✅ Mensagem enviada com sucesso")
                else:
                    logger.info("📩 Mensagem já enviada nesta hora")
            else:
                logger.info("⏰ Fora do horário da bolsa - nenhuma mensagem enviada")
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {str(e)}")
        time.sleep(60)


if __name__ == "__main__":
    keep_alive()
    main()




