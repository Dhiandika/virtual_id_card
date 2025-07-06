import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import glob
import datetime
from flask import Flask, request, render_template, send_file, jsonify
import io
import base64

app = Flask(__name__)

# Global set untuk menyimpan No KTP yang sudah digunakan agar tidak duplikat
# CATATAN PENTING: Dalam aplikasi web produksi, ini harus diganti dengan database
# (misalnya SQLite, PostgreSQL) untuk persistensi data dan penanganan konkurensi
# yang lebih baik antar banyak pengguna. Variabel global ini hanya untuk demo/pengembangan.
generated_ktp_numbers = set()
# Counter untuk 3 digit terakhir KTP
ktp_sequential_counter = 0

# --- Konfigurasi Layout untuk Berbagai Ukuran Kanvas ---
LAYOUT_CONFIGS = {
    "standard": { # Ukuran 900x570
        "width": 900,
        "height": 570,
        "header_start_x": 50,
        "header_start_y": 50,
        "font_header_size": 35,
        "info_start_x_label": 50,
        "info_start_x_colon": 250, # Disesuaikan agar lebih dekat ke label
        "info_start_x_value": 270, # Disesuaikan agar lebih dekat ke titik dua
        "info_start_y": 180,
        "line_height": 35, # Disesuaikan agar jarak vertikal lebih rapat
        "font_label_size": 25,
        "font_value_size": 25,
        "photo_width": 250,
        "photo_height": 350,
        "photo_x_offset_from_right": 50,
        "photo_y": 120,
        "circle_margin": 15,
        "font_date_size": 22,
        "watermark_font_size": 150,
        "watermark_max_width_ratio": 0.8,
        "watermark_max_height_ratio": 0.6,
        "date_y_offset_from_photo_bottom": 10
    },
    "full_hd": { # Ukuran 1920x1080
        "width": 1920,
        "height": 1080,
        "header_start_x": 100,
        "header_start_y": 100,
        "font_header_size": 60,
        "info_start_x_label": 100,
        "info_start_x_colon": 450, # Disesuaikan agar lebih dekat ke label
        "info_start_x_value": 500, # Disesuaikan agar lebih dekat ke titik dua
        "info_start_y": 350,
        "line_height": 65, # Disesuaikan agar jarak vertikal lebih rapat
        "font_label_size": 45,
        "font_value_size": 45,
        "photo_width": 500,
        "photo_height": 700,
        "photo_x_offset_from_right": 100,
        "photo_y": 200,
        "circle_margin": 30,
        "font_date_size": 40,
        "watermark_font_size": 300,
        "watermark_max_width_ratio": 0.8,
        "watermark_max_height_ratio": 0.6,
        "date_y_offset_from_photo_bottom": 20
    }
}

def hex_to_rgb(hex_color):
    """Mengkonversi string heksadesimal warna ke tuple RGB."""
    hex_color = hex_color.lstrip('#')
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

def get_text_color_from_background(rgb_background_color):
    """
    Menentukan warna teks (hitam atau putih) berdasarkan luminansi warna latar belakang.
    Menggunakan rumus luminansi W3C (perceptual brightness) untuk kontras yang baik.
    """
    r, g, b = rgb_background_color
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if luminance > 0.5: # Jika background terang, gunakan teks gelap
        return "black"
    else: # Jika background gelap, gunakan teks terang
        return "white"

def generate_random_sequential_ktp_number():
    """
    Menghasilkan No KTP random 16 digit yang unik,
    dengan 3 digit terakhir berurutan (000-999).
    Jika counter penuh, 16 digit awal akan diacak ulang.
    """
    global ktp_sequential_counter

    # Bagian 16 digit awal (acak)
    # Setiap 1000 KTP, bagian dasar akan diacak ulang untuk menambah variasi
    if ktp_sequential_counter == 0 or ktp_sequential_counter >= 1000:
        ktp_sequential_counter = 0 # Reset counter
        base_16_digits = ''.join(random.choices(string.digits, k=16))
    else:
        base_16_digits = ''.join(random.choices(string.digits, k=16)) # Masih acak setiap kali

    # Bagian 3 digit terakhir (berurutan)
    sequential_part = str(ktp_sequential_counter).zfill(3)
    ktp_sequential_counter += 1

    full_ktp_number = base_16_digits + sequential_part

    # Cek duplikasi (walaupun sangat jarang untuk 19 digit)
    while full_ktp_number in generated_ktp_numbers:
        print("Warning: KTP number duplication detected. Regenerating base.")
        ktp_sequential_counter = 0 # Reset counter dan base jika ada duplikasi
        base_16_digits = ''.join(random.choices(string.digits, k=16))
        sequential_part = str(ktp_sequential_counter).zfill(3)
        full_ktp_number = base_16_digits + sequential_part
        ktp_sequential_counter += 1

    generated_ktp_numbers.add(full_ktp_number)
    return full_ktp_number

def create_ktp_image(user_data, custom_profile_photo_stream=None,
                      profile_folder="profile/", canvas_size_key="standard",
                      title_position="center", background_color_hex="#8B8B7A"):
    """
    Menghasilkan gambar KTP berdasarkan data yang diberikan.

    Args:
        user_data (dict): Kamus berisi data KTP.
        custom_profile_photo_stream (io.BytesIO, optional): Stream byte dari file foto profil yang diunggah.
        profile_folder (str): Nama folder tempat menyimpan foto-foto profil (untuk pilihan acak).
        canvas_size_key (str): Kunci untuk memilih konfigurasi layout ('standard' atau 'full_hd').
        title_position (str): Posisi judul KTP ('left' atau 'center').
        background_color_hex (str): Warna latar belakang KTP dalam format heksadesimal.

    Returns:
        io.BytesIO: Stream byte dari gambar KTP yang dihasilkan dalam format PNG.
    """
    config = LAYOUT_CONFIGS.get(canvas_size_key, LAYOUT_CONFIGS["standard"])

    width = config["width"]
    height = config["height"]
    
    rgb_background_color = hex_to_rgb(background_color_hex)
    image = Image.new("RGB", (width, height), rgb_background_color)
    draw = ImageDraw.Draw(image)

    # Tentukan warna teks utama berdasarkan background (hitam atau putih)
    text_color_dynamic = get_text_color_from_background(rgb_background_color)
    
    # --- Fonts ---
    try:
        # Pastikan font 'arial.ttf' dan 'arialbd.ttf' tersedia di sistem atau di direktori aplikasi
        font_header = ImageFont.truetype("arialbd.ttf", config["font_header_size"])
        font_label = ImageFont.truetype("arial.ttf", config["font_label_size"])
        font_value = ImageFont.truetype("arialbd.ttf", config["font_value_size"])
        font_date = ImageFont.truetype("arial.ttf", config["font_date_size"])
        font_bg_watermark = ImageFont.truetype("arialbd.ttf", config["watermark_font_size"])
    except IOError:
        print("Warning: Could not load Arial fonts. Using default PIL font.")
        font_header = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_bg_watermark = ImageFont.load_default()

    # Menyesuaikan warna watermark dan garis diagonal agar kontras dengan background tetapi tetap samar
    if text_color_dynamic == "white": # Background gelap, buat watermark lebih terang
        wm_r = min(255, rgb_background_color[0] + 50)
        wm_g = min(255, rgb_background_color[1] + 50)
        wm_b = min(255, rgb_background_color[2] + 50)
        line_color_r = min(255, rgb_background_color[0] + 20)
        line_color_g = min(255, rgb_background_color[1] + 20)
        line_color_b = min(255, rgb_background_color[2] + 20)
    else: # Background terang, buat watermark lebih gelap
        wm_r = max(0, rgb_background_color[0] - 50)
        wm_g = max(0, rgb_background_color[1] - 50)
        wm_b = max(0, rgb_background_color[2] - 50)
        line_color_r = max(0, rgb_background_color[0] - 20)
        line_color_g = max(0, rgb_background_color[1] - 20)
        line_color_b = max(0, rgb_background_color[2] - 20)

    text_color_watermark_rgb = (wm_r, wm_g, wm_b, 80) # Transparansi 80
    line_color = (line_color_r, line_color_g, line_color_b, 30) # Transparansi 30
    
    # --- Background Texture (Diagonal Lines) ---
    line_spacing = config["line_height"] / 3
    line_width = 1
    for i in range(-height, width, int(line_spacing)):
        draw.line([(i, 0), (i + height, height)], fill=line_color, width=line_width)

    # --- Latar belakang "GANG DESA" (watermark) ---
    # Konversi gambar ke RGBA untuk mendukung transparansi pada watermark dan foto
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    draw = ImageDraw.Draw(image)

    watermark_text = user_data.get('nama_penduduk', "GANG DESA").upper()
    current_watermark_font_size = config["watermark_font_size"]
    try:
        temp_watermark_font = ImageFont.truetype("arialbd.ttf", current_watermark_font_size)
    except IOError:
        temp_watermark_font = ImageFont.load_default()

    max_text_width = width * config["watermark_max_width_ratio"]
    max_text_height = height * config["watermark_max_height_ratio"]

    bbox = draw.textbbox((0, 0), watermark_text, font=temp_watermark_font)
    wm_width = bbox[2] - bbox[0]
    wm_height = bbox[3] - bbox[1]

    # Menyesuaikan ukuran font watermark agar pas
    while wm_width > max_text_width or wm_height > max_text_height:
        current_watermark_font_size -= 5
        if current_watermark_font_size < 30: # Batas minimum ukuran font
            current_watermark_font_size = 30
            break
        try:
            temp_watermark_font = ImageFont.truetype("arialbd.ttf", current_watermark_font_size)
        except IOError:
            temp_watermark_font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), watermark_text, font=temp_watermark_font)
        wm_width = bbox[2] - bbox[0]
        wm_height = bbox[3] - bbox[1]

    font_bg_watermark = temp_watermark_font

    watermark_positions = [
        (lambda w, h, wm_w, wm_h: (w - wm_w) / 2, lambda w, h, wm_w, wm_h: (h - wm_h) / 2 + 50) # Hanya satu watermark di tengah
    ]

    for pos_func_x, pos_func_y in watermark_positions:
        pos_x = pos_func_x(width, height, wm_width, wm_height)
        pos_y = pos_func_y(width, height, wm_width, wm_height)
        temp_text_layer = Image.new('RGBA', image.size, (255,255,255,0)) # Layer transparan
        temp_draw = ImageDraw.Draw(temp_text_layer)
        temp_draw.text((pos_x, pos_y), watermark_text, fill=text_color_watermark_rgb, font=font_bg_watermark)
        image = Image.alpha_composite(image, temp_text_layer) # Gabungkan layer watermark
        draw = ImageDraw.Draw(image) # Re-initialize draw object after alpha_composite

    # --- Judul KTP ---
    title_text = "KARTU TANDA PENDUDUK"
    gang_desa_title = user_data.get('nama_penduduk', "GANG DESA").upper()

    bbox_title = draw.textbbox((0, 0), title_text, font=font_header)
    title_width = bbox_title[2] - bbox_title[0]
    title_height = bbox_title[3] - bbox_title[1]

    bbox_gang = draw.textbbox((0, 0), gang_desa_title, font=font_header)
    gang_width = bbox_gang[2] - bbox_gang[0]
    gang_height = bbox_gang[3] - bbox_gang[1]

    header_y = config["header_start_y"]
    if title_position == "left":
        header_x = config["header_start_x"]
        draw.text((header_x, header_y), title_text, fill=text_color_dynamic, font=font_header)
        draw.text((header_x, header_y + title_height + 5), gang_desa_title, fill=text_color_dynamic, font=font_header)
    elif title_position == "center":
        title_x = (width - title_width) / 2
        gang_x = (width - gang_width) / 2
        draw.text((title_x, header_y), title_text, fill=text_color_dynamic, font=font_header)
        draw.text((gang_x, header_y + title_height + 5), gang_desa_title, fill=text_color_dynamic, font=font_header)

    # --- Informasi KTP (Kiri) ---
    start_x_label = config["info_start_x_label"]
    start_x_colon = config["info_start_x_colon"]
    start_x_value = config["info_start_x_value"]
    start_y = config["info_start_y"]
    line_height = config["line_height"]

    ktp_details = [
        ("No KTP", generate_random_sequential_ktp_number()),
        ("Nama", user_data.get('nama', '').upper()),
        ("Jenis Kelamin", user_data.get('jenis_kelamin', '').title()),
        ("Domisili", user_data.get('domisili', '').title()),
        ("Agama", user_data.get('agama', '').title()),
        ("Hobi", user_data.get('hobi', '').title()),
    ]

    for i, (label, value) in enumerate(ktp_details):
        y_pos = start_y + i * line_height
        draw.text((start_x_label, y_pos), label, fill=text_color_dynamic, font=font_label)
        draw.text((start_x_colon, y_pos), ":", fill=text_color_dynamic, font=font_label)
        draw.text((start_x_value, y_pos), str(value), fill=text_color_dynamic, font=font_value)

    # --- Bagian Foto (Kanan) ---
    photo_width = config["photo_width"]
    photo_height = config["photo_height"]
    photo_x = width - photo_width - config["photo_x_offset_from_right"]
    photo_y = config["photo_y"]

    # Warna background kotak foto (misalnya pink/magenta dari referensi ktp_virtual.png)
    # Ini adalah area di mana foto akan ditempatkan
    draw.rectangle([photo_x, photo_y,
                    photo_x + photo_width, photo_y + photo_height],
                    fill="#BB257A") # Warna solid untuk kotak foto

    # Target ukuran untuk foto adalah dimensi kotak foto itu sendiri
    target_photo_width = photo_width
    target_photo_height = photo_height

    profile_img = None
    if custom_profile_photo_stream:
        try:
            profile_img = Image.open(custom_profile_photo_stream).convert("RGBA")
        except Exception as e:
            print(f"Error processing uploaded profile photo: {e}. Akan mencoba mencari dari folder.")
    
    if profile_img is None: # Jika tidak ada stream yang valid, coba dari folder 'profile/'
        if not os.path.exists(profile_folder):
            os.makedirs(profile_folder)
            print(f"Folder '{profile_folder}' dibuat.")

        # Cari file gambar di folder 'profile/'
        photo_files = glob.glob(os.path.join(profile_folder, "*.[Pp][Nn][Gg]")) + \
                      glob.glob(os.path.join(profile_folder, "*.[Jj][Pp][Gg]")) + \
                      glob.glob(os.path.join(profile_folder, "*.[Jj][Pp][Ee][Gg]"))
        if photo_files:
            photo_to_load_path = random.choice(photo_files) # Pilih acak
            print(f"Memilih foto secara acak dari '{profile_folder}': {photo_to_load_path}")
            try:
                profile_img = Image.open(photo_to_load_path).convert("RGBA")
            except Exception as e:
                print(f"Error loading random profile photo '{photo_to_load_path}': {e}. Area foto akan kosong.")
        else:
            print(f"Warning: Tidak ada foto ditemukan di folder '{profile_folder}'. Area foto akan kosong.")

    if profile_img:
        try:
            original_width, original_height = profile_img.size
            
            # Hitung rasio aspek target area foto
            target_aspect = target_photo_width / target_photo_height
            original_aspect = original_width / original_height

            # Lakukan cropping agar foto pas dengan rasio aspek target tanpa distorsi
            if original_aspect > target_aspect:
                # Foto asli lebih lebar dari area target, crop horizontal
                new_width = int(original_height * target_aspect)
                left = (original_width - new_width) / 2
                top = 0
                right = (original_width + new_width) / 2
                bottom = original_height
            else:
                # Foto asli lebih tinggi dari area target, crop vertikal
                new_height = int(original_width / target_aspect)
                left = 0
                top = (original_height - new_height) / 2
                right = original_width
                bottom = (original_height + new_height) / 2
            
            profile_img = profile_img.crop((left, top, right, bottom)) # Lakukan cropping
            profile_img = profile_img.resize((target_photo_width, target_photo_height), Image.Resampling.LANCZOS) # Ubah ukuran ke target

            # Tidak perlu mask lingkaran, langsung paste ke area persegi panjang
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Paste foto profil ke gambar KTP
            image.paste(profile_img, (photo_x, photo_y), profile_img) # Menggunakan foto sebagai mask untuk transparansi
            draw = ImageDraw.Draw(image) # Re-initialize draw object setelah paste

        except Exception as e:
            print(f"Error processing profile photo for pasting: {e}. Area foto akan kosong.")
    else:
        print("Tidak ada foto profil yang valid untuk diproses. Area foto akan kosong.")


    # --- Tanggal Pembuatan (Kanan Bawah Foto) ---
    date_label = "Tanggal Pembuatan:"
    current_date = datetime.date.today().strftime("%d - %m - %Y") # Format tanggal

    try:
        font_date_used = font_date
    except NameError:
        font_date_used = ImageFont.load_default()

    bbox_date_label = draw.textbbox((0, 0), date_label, font=font_date_used)
    date_label_width = bbox_date_label[2] - bbox_date_label[0]
    date_label_height = bbox_date_label[3] - bbox_date_label[1]

    bbox_date_value = draw.textbbox((0, 0), current_date, font=font_date_used)
    date_value_width = bbox_date_value[2] - bbox_date_value[0]
    date_value_height = bbox_date_value[3] - bbox_date_value[1]

    # Hitung posisi tanggal di bawah foto
    date_x = photo_x + (photo_width - date_label_width) / 2 # Tengah di bawah foto
    date_y = photo_y + photo_height + config["date_y_offset_from_photo_bottom"] # Di bawah foto dengan offset

    draw.text((date_x, date_y), date_label, fill=text_color_dynamic, font=font_date_used)
    draw.text((photo_x + (photo_width - date_value_width) / 2, date_y + date_label_height + 5), current_date, fill=text_color_dynamic, font=font_date_used)

    # Simpan gambar yang dihasilkan ke BytesIO object
    img_io = io.BytesIO()
    image.save(img_io, 'PNG') # Simpan sebagai PNG
    img_io.seek(0) # Pindahkan pointer ke awal stream agar bisa dibaca dari awal
    return img_io

@app.route('/')
def index():
    """Menampilkan halaman formulir input KTP."""
    return render_template('index.html')

@app.route('/generate_ktp_preview', methods=['POST'])
def generate_ktp_preview():
    """
    Menerima data dari formulir, menghasilkan gambar KTP,
    dan mengembalikannya sebagai base64 encoded string dalam format JSON untuk preview.
    """
    user_data = {
        'nama_penduduk': request.form['nama_penduduk'],
        'nama': request.form['nama'],
        # Mengatasi input 'Jenis Kelamin' dari opsi radio 'Lainnya'
        'jenis_kelamin': request.form.get('jenis_kelamin')
    }
    # Jika jenis kelamin yang dipilih adalah 'Lainnya', gunakan nilai dari input 'other_jenis_kelamin'
    if user_data['jenis_kelamin'] == 'Lainnya':
        user_data['jenis_kelamin'] = request.form.get('other_jenis_kelamin', '')

    user_data['domisili'] = request.form['domisili']
    user_data['agama'] = request.form['agama']
    user_data['hobi'] = request.form['hobi']

    selected_canvas_size = request.form['canvas_size']
    selected_title_position = request.form['title_position']
    background_color_hex = request.form['background_color']

    profile_photo_file = request.files.get('profile_photo')
    custom_profile_photo_stream = None
    if profile_photo_file and profile_photo_file.filename != '':
        # Penting: Karena BytesIO.read() hanya bisa dibaca sekali, kita perlu menyimpan
        # data file ini agar bisa digunakan kembali jika tombol download ditekan.
        # Untuk demo sederhana, kita akan membaca ulang stream jika ini dari file upload.
        # Dalam produksi, pertimbangkan untuk menyimpan file sementara di disk.
        custom_profile_photo_stream = io.BytesIO(profile_photo_file.read())
        profile_photo_file.seek(0) # Reset pointer file agar request.files.get bisa dibaca lagi untuk /download_ktp

    img_stream = create_ktp_image(user_data,
                                  custom_profile_photo_stream=custom_profile_photo_stream,
                                  canvas_size_key=selected_canvas_size,
                                  title_position=selected_title_position,
                                  background_color_hex=background_color_hex)
    
    # Encode gambar ke base64
    img_base64 = base64.b64encode(img_stream.getvalue()).decode('utf-8')
    return jsonify({'image': f'data:image/png;base64,{img_base64}'})

@app.route('/download_ktp', methods=['POST'])
def download_ktp():
    """
    Menerima data dari formulir, menghasilkan gambar KTP,
    dan mengembalikannya sebagai respons file untuk diunduh.
    """
    user_data = {
        'nama_penduduk': request.form['nama_penduduk'],
        'nama': request.form['nama'],
        # Mengatasi input 'Jenis Kelamin' dari opsi radio 'Lainnya'
        'jenis_kelamin': request.form.get('jenis_kelamin')
    }
    # Jika jenis kelamin yang dipilih adalah 'Lainnya', gunakan nilai dari input 'other_jenis_kelamin'
    if user_data['jenis_kelamin'] == 'Lainnya':
        user_data['jenis_kelamin'] = request.form.get('other_jenis_kelamin', '')

    user_data['domisili'] = request.form['domisili']
    user_data['agama'] = request.form['agama']
    user_data['hobi'] = request.form['hobi']

    selected_canvas_size = request.form['canvas_size']
    selected_title_position = request.form['title_position']
    background_color_hex = request.form['background_color']

    profile_photo_file = request.files.get('profile_photo')
    custom_profile_photo_stream = None
    if profile_photo_file and profile_photo_file.filename != '':
        # Penting: Pastikan stream dibaca dari awal untuk proses unduhan
        custom_profile_photo_stream = io.BytesIO(profile_photo_file.read())

    img_stream = create_ktp_image(user_data,
                                  custom_profile_photo_stream=custom_profile_photo_stream,
                                  canvas_size_key=selected_canvas_size,
                                  title_position=selected_title_position,
                                  background_color_hex=background_color_hex)
    
    filename = f"ktp_{user_data['nama'].replace(' ', '_').lower()}_{selected_canvas_size}.png"

    return send_file(img_stream, mimetype='image/png', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    # Pastikan folder 'profile' ada saat aplikasi dimulai
    if not os.path.exists("profile"):
        os.makedirs("profile")
        print("Folder 'profile/' dibuat.")
    # Jalankan aplikasi Flask dalam mode debug (cocok untuk pengembangan)
    app.run(debug=True)
