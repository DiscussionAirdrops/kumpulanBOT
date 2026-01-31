# Ino Crypto Alert 🚀 | Hybrid AI Bot (Telegram & Discord)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Groq AI Powered](https://img.shields.io/badge/AI-Powered%20by%20Groq-purple)](https://groq.com/)

**Ino Crypto Alert** adalah bot komunitas *hybrid* canggih yang dirancang untuk mempermudah manajemen informasi airdrop dan trading crypto. Bot ini menjembatani Telegram dan Discord secara otomatis, dilengkapi kecerdasan buatan (AI) untuk interaksi dan rekapitulasi otomatis.

Bot ini sudah berjalan secara live di komunitas [**Warkop CR**](https://t.me/Warkop_CR).

---

## 📹 Video Tutorial & Demo

Lihat penjelasan lengkap tentang fitur, cara kerja, dan demo bot ini di video berikut:

[![Video Tutorial Ino Crypto Alert](https://img.youtube.com/vi/up9KJmIcrYc/maxresdefault.jpg)](https://youtu.be/up9KJmIcrYc)
> *Klik gambar di atas untuk menonton video.*

---

## ✨ Fitur Utama

Bot ini menggabungkan otomatisasi, database, dan AI menjadi satu kesatuan yang kuat:

### 🤖 Kecerdasan Buatan (AI)
* **AI Chat Persona:** Bot bisa diajak ngobrol santai, menjawab pertanyaan seputar crypto, atau sekadar bercanda dengan gaya bahasa yang natural (Powered by Groq/Llama 3). Gunakan command `/tanya` atau mention botnya.
* **Smart Auto-Recap:** Tidak perlu rekap manual! Setiap jam 00:00 WIB, bot otomatis menarik data airdrop hari itu, menggunakan AI untuk merangkumnya menjadi list yang rapi, dan mempostingnya ke grup.

### 🔄 Hybrid Bridge (Tele-Discord)
* **Auto-Forwarder:** Pesan yang mengandung hashtag tertentu (contoh: `#airdrop`, `#testnet`) di grup Telegram admin akan otomatis diteruskan ke channel Discord.
* **Image Support:** Tidak hanya teks, gambar (attachment) dari Telegram juga ikut terkirim ke Discord dengan mulus.

### 💾 Multi-Database System
Data tersimpan aman dan terstruktur di tiga tempat sekaligus untuk keandalan dan fleksibilitas:
* **SQLite:** Penyimpanan lokal untuk backup cepat.
* **MySQL:** Database utama untuk produksi yang kuat.
* **Firebase Firestore:** Sinkronisasi real-time (cocok jika ingin dihubungkan ke frontend website/aplikasi).

### 🛡️ Keamanan & Utilitas
* **Anti-Spam Filter:** Otomatis menghapus pesan member yang mengandung kata kunci spam berbahaya.
* **Discord Verification:** Sistem verifikasi member baru di Discord menggunakan captcha.
* **Crypto Tools:** Cek harga coin real-time (contoh: ketik `BTC`), kalkulator konversi kurs, dan perbaikan link Twitter (X.com) otomatis.
* **API Endpoint:** Menyediakan server Flask mini untuk mengakses data airdrop via API JSON.

---

## 🛠️ Tech Stack

* **Bahasa:** Python 3.x
* **Platform:** `python-telegram-bot`, `discord.py`
* **Database:** `mysql-connector`, `sqlite3`, `firebase-admin`
* **AI/LLM:** Groq API (Llama 3 model)
* **API Server:** Flask
* **Scheduler:** JobQueue (bawaan library telegram)

---

## 🚀 Instalasi & Penggunaan

### Prasyarat
Pastikan Anda telah menginstal:
* Python 3.9 atau lebih baru.
* Database MySQL (lokal atau remote).
* Akun & Project di Firebase (untuk Firestore).
* API Key dari Groq.

### Langkah-langkah

1.  **Clone Repositori**
    ```bash
    git clone [https://github.com/DiscussionAirdrops/kumpulanBOT.git](https://github.com/DiscussionAirdrops/kumpulanBOT.git)
    cd kumpulanBOT/botAI
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(Catatan: Jika file `requirements.txt` belum tersedia, install library utama manual: `pip install python-telegram-bot discord.py mysql-connector-python firebase-admin groq flask simpleeval requests aiohttp`)*

3.  **Konfigurasi Environment Variables (.env)**
    **PENTING:** Jangan pernah hardcode credential Anda di file `.py`! Buat file `.env` di root folder dan isi sesuai credential Anda:

    ```env
    # Telegram
    TELEGRAM_BOT_TOKEN=token_bot_telegram_anda
    TARGET_TELEGRAM_CHAT_ID=-100xxxxxxxxx

    # Discord
    DISCORD_BOT_TOKEN=token_bot_discord_anda
    ID_DISCORD_BRIDGE=id_channel_discord_untuk_forward

    # AI
    GROQ_API_KEY=gsk_xxxxxxxxxxxx

    # Database MySQL
    MYSQL_HOST=localhost
    MYSQL_USER=root
    MYSQL_PASSWORD=password_mysql_anda
    MYSQL_DB=nama_database

    # Firebase (Letakkan file serviceAccountKey.json di folder project)
    FIREBASE_CRED_PATH=serviceAccountKey.json
    ```

4.  **Jalankan Bot**
    ```bash
    python nama_file_bot_anda.py
    ```

---

## 💬 Command Telegram

| Command | Deskripsi | Akses |
| :--- | :--- | :--- |
| `/start` | Memulai interaksi dengan bot. | Publik |
| `/tanya [pertanyaan]` | Bertanya apa saja kepada AI Bot. | Publik |
| `/recap` | Menampilkan 10 daftar airdrop terakhir (versi AI). | Admin |
| `/rekaphari` | Menampilkan rekap semua airdrop hari ini. | Admin |
| `/recap_now` | Memicu postingan rekap harian saat ini juga (manual trigger). | Admin |
| `/stats` | Melihat statistik jumlah data airdrop. | Admin |

---

## 🤝 Komunitas & Support

Jika ada pertanyaan seputar kode ini, kendala instalasi, atau ingin berdiskusi tentang airdrop terbaru, silakan bergabung dengan komunitas kami:

* 🌐 **Telegram Group:** [Discussion Airdrops](https://t.me/DiscussionAirdrops)
* 🐦 **X (Twitter):** [@inokrambol](https://x.com/inokrambol)

### ☕ Traktir Developer

Jika tools dan *source code* ini bermanfaat, membantu komunitas Anda, atau memberi Anda cuan, dukungan Anda sangat berarti agar saya semangat terus update fitur-fitur baru!

* 💎 **EVM Address (ETH/BSC/Base/Polygon):**
    `0x2473EF56532306bEB024a0Af1065470771d92920`
* 🎁 **Saweria (IDR - OVO/Gopay/Dana):**
    [https://saweria.co/rakian](https://saweria.co/rakian)

---
**Happy Coding & Happy Cuan! 🚀**
