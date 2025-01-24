import os
import asyncio
from telethon import TelegramClient
from datetime import datetime
import subprocess

# Telegram configuration
API_ID = 26968169  # Coloque seu API_ID aqui
API_HASH = '5768aedba5732b11a1288965b57472e7'  # Coloque seu API_HASH aqui
PHONE_NUMBER = -5516982194939  # Coloque seu número de telefone aqui
CHAT_ID = -1002441869048  # Coloque o ID do chat de destino aqui

# Texto para sobrepor nas mídias
TEXT_LINE1 = "DraLarissa.github.io"
TEXT_LINE2 = "+"

# Initialize Telegram client
client = None

async def add_text_to_media(input_path):
    """Adiciona texto à mídia usando FFmpeg"""
    try:
        output_path = f"{os.path.splitext(input_path)[0]}_with_text{os.path.splitext(input_path)[1]}"
        
        # Comando FFmpeg para adicionar texto centralizado
        command = [
            'ffmpeg', '-i', input_path,
            '-vf', f"drawtext=text='{TEXT_LINE1}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2-30,"
                   f"drawtext=text='{TEXT_LINE2}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2+10",
            '-y', output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if process.returncode == 0 and os.path.exists(output_path):
            os.remove(input_path)  # Remove arquivo original
            return output_path
        return input_path
    except Exception as e:
        print(f"Erro ao adicionar texto: {e}")
        return input_path

async def init_telegram():
    """Inicializa o cliente do Telegram"""
    global client
    if not all([API_ID, API_HASH, PHONE_NUMBER, CHAT_ID]):
        print("Por favor, configure API_ID, API_HASH, PHONE_NUMBER e CHAT_ID no script")
        return False
    
    try:
        client = TelegramClient('bot_session', API_ID, API_HASH)
        await client.start(phone=PHONE_NUMBER)
        print("Conectado ao Telegram com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao conectar ao Telegram: {e}")
        return False

async def process_links():
    """Processa links do arquivo e envia para o Telegram"""
    print("Processador de mídia iniciado!")
    
    while True:
        try:
            if os.path.exists('links.txt'):
                with open('links.txt', 'r') as file:
                    links = file.readlines()
                
                # Limpa o arquivo após ler
                open('links.txt', 'w').close()
                
                for link in links:
                    link = link.strip()
                    if link:
                        try:
                            print(f"\nBaixando: {link}")
                            # Baixa usando gallery-dl
                            process = await asyncio.create_subprocess_shell(
                                f'gallery-dl {link}',
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            await process.communicate()
                            
                            # Procura arquivos baixados
                            for root, _, files in os.walk('.'):
                                for file in files:
                                    if file.endswith(('.jpg', '.jpeg', '.png', '.mp4', '.gif')):
                                        file_path = os.path.join(root, file)
                                        try:
                                            # Adiciona texto
                                            print(f"Adicionando texto em: {file_path}")
                                            file_path = await add_text_to_media(file_path)
                                            
                                            # Envia para o Telegram
                                            print(f"Enviando: {file_path}")
                                            await client.send_file(CHAT_ID, file_path)
                                            print(f"Enviado com sucesso: {file_path}")
                                            
                                            # Remove arquivo após enviar
                                            if os.path.exists(file_path):
                                                os.remove(file_path)
                                            
                                            # Espera 30 segundos entre envios
                                            await asyncio.sleep(30)
                                        except Exception as e:
                                            print(f"Erro ao enviar {file_path}: {e}")
                                            if os.path.exists(file_path):
                                                os.remove(file_path)
                        except Exception as e:
                            print(f"Erro ao processar {link}: {e}")
            
            # Espera antes de verificar novos links
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            await asyncio.sleep(5)

async def main():
    print("=== Processador de Mídia com Telegram ===")
    print("1. Conectando ao Telegram...")
    
    if not await init_telegram():
        print("Falha ao inicializar Telegram. Saindo...")
        return
    
    print("2. O programa vai monitorar 'links.txt' para novos links")
    print("3. Cada link será processado e enviado para o chat ID:", CHAT_ID)
    print("4. Pressione Ctrl+C para parar o programa")
    print("\nIniciando processador...")
    
    try:
        await process_links()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário")
    except Exception as e:
        print(f"\nErro no programa: {str(e)}")
    finally:
        if client:
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
