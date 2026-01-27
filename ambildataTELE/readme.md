# kumpulanBOT

Repository kumpulan bot otomatis untuk berbagai keperluan automation.

**Creator:** [@inokrambol](https://twitter.com/inokrambol)

---

## Deskripsi

Repository ini berisi kumpulan bot otomatis yang dirancang untuk membantu berbagai tugas automation. Bot utama yang tersedia saat ini adalah **Telegram Post Collector** – bot untuk mengambil postingan dari grup Telegram berdasarkan hashtag tertentu dan menyimpannya dalam format **JSON**.

---

## Daftar Bot

| Bot | Deskripsi | Status |
|-----|-----------|--------|
| [ambildataTELE](#ambildatatele--telegram-post-collector) | Mengambil postingan Telegram berdasarkan hashtag | Aktif |

---

## ambildataTELE – Telegram Post Collector

### Tentang Bot

Bot ini dibuat untuk **mengambil (mengoleksi) postingan Telegram** dari sebuah grup Telegram publik yang mengandung hashtag tertentu.

> **Catatan:** Bot **tidak memfilter, menghapus, atau memodifikasi pesan**, hanya **mengambil dan menyimpan data postingan**.

### Target & Hashtag

**Grup Telegram Target:**
```
@Warkop_CR
```

**Hashtag yang Diambil:**

| Hashtag | Kategori |
|---------|----------|
| `#airdrop` | Crypto Airdrop |
| `#waitlist` | Waitlist Project |
| `#update` | Update Informasi |
| `#instant` | Reward Instant |
| `#info` | Informasi Umum |
| `#yapping` | Diskusi |
| `#testnet` | Testnet Project |
| `#garapan` | Project Garapan |
| `#retro` | Retroactive |

---

## Quick Start

### Prerequisites

- Python 3.8 atau lebih baru
- Akun Telegram aktif
- API ID & API Hash dari Telegram

### 1. Clone Repository

```bash
git clone https://github.com/DiscussionAirdrops/kumpulanBOT.git
cd kumpulanBOT/ambildataTELE
```

### 2. Install Dependencies

```bash
pip install telethon
```

### 3. Dapatkan API Credentials

1. Kunjungi [https://my.telegram.org/auth](https://my.telegram.org/auth)
2. Login dengan nomor Telegram
3. Pilih menu **API development tools**
4. Salin **API ID** dan **API Hash**

### 4. Jalankan Bot

```bash
python bot.py
```

Saat pertama kali dijalankan:
1. Telegram akan mengirim **kode OTP** ke akun Anda
2. Masukkan kode tersebut di terminal
3. Session akan tersimpan otomatis untuk penggunaan selanjutnya

### Output Data

Data postingan akan disimpan dalam format JSON:

```
data_warkop_cr.json
```

---

## Video Tutorial

**Link:** [https://youtu.be/7gHNw2CmCqo](https://youtu.be/7gHNw2CmCqo)

Video menjelaskan:
- Cara login Telegram API
- Cara menjalankan script
- Cara bot mengambil postingan Telegram
- Penjelasan alur kerja bot

---

## Keamanan

**PENTING: Jaga keamanan credentials Anda!**

| Jangan Lakukan | Sebaiknya Lakukan |
|----------------|-------------------|
| Upload file `.session` ke repository | Tambahkan `*.session` ke `.gitignore` |
| Bagikan file session ke orang lain | Simpan session di tempat yang aman |
| Gunakan akun Telegram utama | Gunakan akun Telegram cadangan |

### Contoh `.gitignore`

```gitignore
# Telegram session files
*.session
*.session-journal

# Python
__pycache__/
*.py[cod]

# Output data
*.json
```

## Catatan Penting

- Bot ini **mengambil postingan Telegram**, bukan melakukan moderasi
- Data diambil dari **grup Telegram publik**
- Gunakan bot ini secara **bijak** dan sesuai **kebijakan Telegram**
- Developer tidak bertanggung jawab atas penyalahgunaan bot

---

## Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository ini
2. Buat branch baru (`git checkout -b feature/NamaFitur`)
3. Commit perubahan (`git commit -m 'Menambahkan fitur baru'`)
4. Push ke branch (`git push origin feature/NamaFitur`)
5. Buat Pull Request

---

## Donasi

Jika project ini membantu dan Anda ingin mendukung pengembangan selanjutnya:

**EVM Address (Semua Jaringan):**
```
0x2473EF56532306bEB024a0Af1065470771d92920
```

Mendukung: Ethereum, BSC, Polygon, Arbitrum, Optimism, Base, Avalanche, dan semua jaringan EVM lainnya.

---

## Lisensi

Distributed under the MIT License. See `LICENSE` for more information.

---

Jangan lupa kasih star kalau repository ini membantu!

**GitHub:** [DiscussionAirdrops](https://github.com/DiscussionAirdrops)  
**Twitter:** [@inokrambol](https://twitter.com/inokrambol)
