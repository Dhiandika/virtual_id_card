# 📇 Proyek Pembuat KTP Virtual

Aplikasi web inovatif berbasis **Flask** yang dirancang untuk memfasilitasi pembuatan **KTP (Kartu Tanda Penduduk) virtual** yang dapat disesuaikan sepenuhnya. Aplikasi ini memungkinkan pengguna untuk:

- Memasukkan data pribadi.
- Mengatur visual KTP sesuai preferensi.
- Mengunggah atau menggunakan foto profil acak.
- Melihat preview KTP secara instan.
- Mengunduh hasil akhir dalam format gambar PNG.

Ideal untuk simulasi, proyek kreatif, portofolio, atau sekadar hiburan.

---

## 🚀 Fitur Utama

- **Kustomisasi Data Lengkap**  
  Isi nama lengkap, jenis kelamin, domisili, agama, dan hobi untuk membuat KTP yang unik.

- **Ukuran Kanvas & Posisi Judul Fleksibel**  
  - `Standard`: 900x570 px  
  - `Full HD`: 1920x1080 px  
  Pilih posisi judul di kiri (tradisional) atau tengah (modern).

- **Manajemen Foto Profil Cerdas**  
  - Unggah sendiri atau biarkan sistem memilih acak dari folder `profile/`.  
  - Foto otomatis dicrop agar pas dan tidak distorsi.

- **Warna Background & Teks Adaptif**  
  Pilih warna latar menggunakan color picker. Warna teks otomatis menyesuaikan (hitam/putih) untuk keterbacaan maksimal.

- **Watermark Dinamis**  
  Nama daerah/penduduk ditampilkan sebagai watermark transparan di latar belakang KTP.

- **Preview Instan & Unduh Mudah**  
  Lihat hasil sebelum mengunduh. Format output: `.png`.

---

## 📁 Struktur Proyek

```
📦ktp/
 ┣ 📂profile/             # Gambar foto profil acak (jika tidak diunggah manual)
 ┃ ┣ 📜Ander – 02.png     
 ┃ ┗ 📜Wumpus.png         
 ┣ 📂templates/           # Template HTML Flask
 ┃ ┗ 📜index.html         
 ┣ 📜.gitattributes       
 ┣ 📜app.py               # File utama backend Flask
 ┣ 📜ktp_virtual.png      # Contoh hasil output KTP
 ┣ 📜main.py              # (Opsional) Skrip alternatif
 ┣ 📜README.md            
 ┣ 📜refrensi.png         # Referensi desain
 ┣ 📜requirements.txt     # Dependensi proyek
 ┗ 📜website.png          # Screenshot UI aplikasi
````

---

## ⚙️ Persyaratan Sistem

* **Python 3.7+**
* **pip** (Python package installer)

---

## 🔧 Instalasi

1. **Clone atau Unduh Proyek**

   ```bash
   git clone <URL_REPOSITORI_ANDA>
   cd ktp
   ```

2. **Buat Virtual Environment**

   ```bash
   python -m venv venv
   ```

3. **Aktifkan Environment**

   * Windows:

     ```bash
     .\venv\Scripts\activate
     ```
   * macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

4. **Instal Dependensi**

   ```bash
   pip install -r requirements.txt
   ```

5. **(Opsional) Buat Folder `profile/`**

   ```bash
   mkdir profile
   ```

6. **(Opsional) Siapkan Font Arial**

   * Letakkan `arial.ttf` dan `arialbd.ttf` di direktori proyek.
   * Atau pastikan font Arial tersedia di sistem Anda.

---

## ▶️ Menjalankan Aplikasi

```bash
# Aktifkan virtual environment dulu (jika belum)
python app.py
# atau
flask run
```

Buka browser ke: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 🖱️ Cara Menggunakan

1. Isi data KTP (nama, jenis kelamin, domisili, agama, hobi, dll).
2. Pilih ukuran canvas dan posisi judul.
3. Pilih warna latar belakang.
4. Upload foto profil (opsional).
5. Klik `Preview KTP` → Lihat hasil.
6. Klik `Unduh KTP` → Gambar PNG akan diunduh.

---

## 🌐 Opsi Deployment Gratis

Beberapa platform gratis yang cocok untuk meng-host proyek Flask ini:

| Platform           | Kelebihan                                  |
| ------------------ | ------------------------------------------ |
| **Heroku**         | Integrasi Git, mudah digunakan, cold start |
| **Render**         | Tidak sleep, performa stabil, UI modern    |
| **PythonAnywhere** | Fokus Python, akses bash via browser       |

> Pastikan membaca batasan resource pada tiap platform.

---

## 📝 Lisensi

**Made by Dhiandika**
© 2025, All Rights Reserved.


