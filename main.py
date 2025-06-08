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
              logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def esta_no_horario_da_bolsa(agora):
    return agora.weekday() < 5 and dt_time(14, 30) <= agora.time() <= dt_time(21, 0)


def formatar_mensagem(dados_indices, timestamp):
    def emoji(change): return "📈" if change >= 0 else "📉"
    def sinal(change): return "+" if change >= 0 else ""

    mensagem = f"🔔 **Atualização Horária dos Mercados**\n"

    for nome, dados in dados_indices.items():
        p = dados['preco']
        ch = dados['variacao']
        ch_pct = dados['variacao_pct']
        gainer = dados['top_gainer']
        loser = dados['top_loser']

        mensagem += f"""
📊 **{nome}**
💰 Preço: ${p:.2f}
{emoji(ch_pct)} Variação: {sinal(ch)}{ch:.2f} ({sinal(ch_pct)}{ch_pct:.2f}%)
🟢 Maior Alta: {gainer['name']} ({gainer['symbol']}) +{gainer['change_percent']:.2f}%
🔴 Maior Queda: {loser['name']} ({loser['symbol']}) {loser['change_percent']:.2f}%
"""

    mensagem += f"\n🕒 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n*Powered by Yahoo Finance*"
    return mensagem


def main():
    config = Config()
    bot = TelegramBot(config.telegram_token, config.telegram_chat_id)
    monitor = SP500Monitor()
    logger.info("Bot de monitoramento iniciado")

    ultima_hora_alerta = None

    while True:
        try:
            agora = datetime.now()
            hora_atual = agora.hour

            if esta_no_horario_da_bolsa(agora):
                if hora_atual != ultima_hora_alerta:
                    dados = {}

                    for indice in ['spx', 'nasdaq', 'dow']:
                        preco = monitor.get_current_price(symbol=indice)
                        movers = monitor.get_top_movers(symbol=indice)
                        if preco and movers:
                            dados[indice.upper()] = {
                                'preco': preco['price'],
                                'variacao': preco['change'],
                                'variacao_pct': preco['change_percent'],
                                'top_gainer': movers['top_gainer'],
                                'top_loser': movers['top_loser']
                            }

                    if dados:
                        mensagem = formatar_mensagem(dados, agora)
                        if bot.send_message(mensagem):
                            ultima_hora_alerta = hora_atual
                            logger.info("✅ Mensagem horária enviada com sucesso.")
                    else:
                        logger.warning("⚠️ Dados insuficientes para gerar alerta.")

            else:
                logger.info("⏱ Fora do horário da bolsa - nenhuma mensagem enviada")

        except Exception as e:
            logger.error(f"Erro no loop principal: {str(e)}")

        time.sleep(60)


if __name__ == "__main__":
    keep_alive()
    main()
