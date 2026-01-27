import json
import asyncio
from telethon import TelegramClient

# --- KONFIGURASI ---
api_id = 'APINYA' 
api_hash = 'HASHNYA'
phone_number = '+62KONOHA' # Format: +628...

# Target Channel
channel_username = '@Warkop_CR'

# Taggar Target
target_tags = [
    '#airdrop', '#waitlist', '#update', '#instant', 
    '#info', '#yapping', '#testnet', '#garapan', '#retro'
]

output_file = 'data_warkop_cr.json'

async def main():
    client = TelegramClient('session_warkop_json', api_id, api_hash)
    await client.start(phone_number)
    print(f"Login sukses! Mengambil data dari {channel_username}...")

    try:
        entity = await client.get_entity(channel_username)
    except Exception as e:
        print(f"Error: Tidak bisa menemukan grup/channel. {e}")
        return

    data_list = []
    
    # Set untuk melacak teks yang sudah disimpan (Anti-Duplikat)
    seen_texts = set()
    
    print("Sedang memproses pesan... (Pesan duplikat akan di-skip)")

    # Loop pesan (Default: Terbaru ke Terlama)
    async for message in client.iter_messages(entity):
        if message.text:
            text_original = message.text
            text_lower = text_original.lower()
            
            # 1. Cek Taggar
            matched_tags = [tag for tag in target_tags if tag in text_lower]
            
            if matched_tags:
                # 2. Cek Anti-Duplikat (Berdasarkan isi teks)
                # Jika teks ini sudah pernah dilihat sebelumnya, skip.
                if text_original in seen_texts:
                    print(f"[-] Skip duplikat (ID: {message.id})")
                    continue
                
                # Jika belum, masukkan ke daftar 'seen'
                seen_texts.add(text_original)

                # --- Proses Penyimpanan Data ---
                if hasattr(entity, 'username') and entity.username:
                    msg_link = f"https://t.me/{entity.username}/{message.id}"
                else:
                    clean_id = str(message.chat_id).replace('-100', '')
                    msg_link = f"https://t.me/c/{clean_id}/{message.id}"

                post_object = {
                    "id": message.id,
                    "date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
                    "timestamp": int(message.date.timestamp()),
                    "link": msg_link,
                    "sender_id": message.sender_id,
                    "tags_detected": matched_tags,
                    "content": {
                        "full_text": text_original,
                        "has_media": bool(message.media),
                        "views": message.views if message.views else 0
                    }
                }
                
                data_list.append(post_object)
                print(f"[+] Disimpan ID: {message.id} | Tags: {matched_tags}")

    # Simpan ke JSON
    if data_list:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
            
        print(f"\nSELESAI! {len(data_list)} data unik tersimpan di '{output_file}'")
    else:
        print("\nTidak ada data yang ditemukan.")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())