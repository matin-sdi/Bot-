from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, AIORateLimiter
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum, Bip39SeedGenerator, Bip84, Bip84Coins, Bip44Changes
import requests
import time
import sys
import logging
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8431733682:AAFrzZoxdGaq9B9Dc2beaDqgE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('bc1qp6ejw8ptj9l9pkscmlf8fhhkrrjeawgpyjvtq8')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if '|' in text:
        parts = text.split('|')
        h = parts[0].strip()
        max_attempts = int(parts[1].strip())
        
        await update.message.reply_text(f'Shoroo dar {max_attempts} talash...\n')
        
        found_target = False
        found_balance = False
        attempts = 0
        batch_size = 250
        rest_time = 1300

        while attempts < max_attempts and not found_target:
            attempts += 1
            
            try:
                mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
                seed = Bip39SeedGenerator(str(mnemonic)).Generate()
                bip84_ctx = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
                address = bip84_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
                
                await update.message.reply_text(f'\n🎯 Talash {attempts}/{max_attempts}\n🔑 Mnemonic: {mnemonic}\n🏦 Address: {address}')
                
                if address.strip() == h.strip():
                    await update.message.reply_text('\n' + '='*50 + '\n✅✅✅ A D R E S S   M A K S O O D   P E I D A   S H O D ! ✅✅✅\n' + '='*50 + f'\n🔑 Phrase: {mnemonic}\n🏦 Address: {address}')
                    found_target = True
                    break
                
                await update.message.reply_text('🔍 Check kardan mojoodi az Blockstream API...')
                try:
                    response = requests.get(f"https://blockstream.info/api/address/{address}", timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'chain_stats' in data:
                            funded = data['chain_stats'].get('funded_txo_sum', 0)
                            spent = data['chain_stats'].get('spent_txo_sum', 0)
                            balance_btc = (funded - spent) / 100000000
                            
                            if balance_btc > 0:
                                msg = '\n' + '⭐'*50 + '\n💰💰💰 A D R E S S   B A   M O J O O D I   P E I D A   S H O D ! 💰💰💰\n' + '⭐'*50 + f'\n🔑 Phrase: {mnemonic}\n🏦 Address: {address}\n💰 Mojoodi: {balance_btc:.8f} BTC'
                                
                                try:
                                    btc_price_response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json", timeout=5)
                                    if btc_price_response.status_code == 200:
                                        btc_price = btc_price_response.json()['bpi']['USD']['rate_float']
                                        usd_value = balance_btc * btc_price
                                        msg += f'\n💵 Gheymat ($): ${usd_value:,.2f}'
                                except:
                                    pass
                                    
                                await update.message.reply_text(msg)
                                found_balance = True
                                break
                            
                            else:
                                await update.message.reply_text(f'📭 Mojoodi: 0 BTC')
                                
                        else:
                            await update.message.reply_text('❌ Data structure gheyre standard')
                    
                    elif response.status_code == 429:
                        await update.message.reply_text('⚠️ Rate limit shodid, sabr konid...')
                        await asyncio.sleep(5)
                        attempts -= 1
                        continue
                        
                    else:
                        await update.message.reply_text(f'❌ HTTP Error {response.status_code}')
                        
                except requests.exceptions.Timeout:
                    await update.message.reply_text('⏰ Timeout dar ersaal darkhast')
                except requests.exceptions.ConnectionError:
                    await update.message.reply_text('🌐 Connection Error - internet ra check konid')
                except Exception as e:
                    await update.message.reply_text(f'❌ Error dar API: {str(e)}')
                
                await asyncio.sleep(0.5)
                
                if attempts % batch_size == 0 and attempts < max_attempts and not found_target:
                    remaining_attempts = max_attempts - attempts
                    if remaining_attempts > 0:
                        await update.message.reply_text(f'\n⏳ {batch_size} talash anjam shod. Estefade az {attempts} talash.\n📊 {remaining_attempts} talash baghi moonde.\n😴 Esteraahat baraye {rest_time/60} daghighe ({rest_time}s)...')
                        
                        for remaining in range(rest_time, 0, -1):
                            mins, secs = divmod(remaining, 60)
                            time_str = f'{mins:02d}:{secs:02d}'
                            sys.stdout.write(f'\r🕒 Bazgasht baad az: {time_str}   ')
                            sys.stdout.flush()
                            await asyncio.sleep(1)
                        
                        await update.message.reply_text(f'\n✅ Bazgasht az esterahat! Edame talash...')
                        
            except Exception as e:
                await update.message.reply_text(f'❌ Error dar generate: {str(e)}')
                continue

        final = '\n' + '='*60 + '\n'
        if found_target:
            final += '✅ Natije: Address maksood peida shod!'
        elif found_balance:
            final += '⚠️  Natije: Address ba mojoodi peida shod vali maksood nabud'
        else:
            final += '❌ Natije: Hich address jadidi peida nashod'
        final += f'\n📊 Majmoo talash ha: {attempts}\n' + '='*60
        
        await update.message.reply_text(final)
    else:
        await update.message.reply_text("Lotfan be format address|tedad ersal konid")

def main():
    application = Application.builder()\
        .token(TOKEN)\
        .rate_limiter(AIORateLimiter(max_retries=3))\
        .build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()