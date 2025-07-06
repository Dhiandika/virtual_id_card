import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import glob
import datetime

# Global set untuk menyimpan No KTP yang sudah digunakan agar tidak duplikat
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
    # Perbaikan: Membuat tuple langsung dengan tanda kurung dan slicing yang benar
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

def generate_random_sequential_ktp_number():
    """
    Menghasilkan No KTP random 16 digit yang unik,
    dengan 3 digit terakhir berurutan (000-999).
    Jika counter penuh, 16 digit awal akan diacak ulang.
    """
    global ktp_sequential_counter

    # Bagian 16 digit awal (acak)
    if ktp_sequential_counter == 0 or ktp_sequential_counter >= 1000:
        ktp_sequential_counter = 0 # Reset counter
        base_16_digits = ''.join(random.choices(string.digits, k=16))
    else:
        # Untuk menjaga keunikan lebih baik, bagian 16 digit awal juga diacak setiap kali,
        # atau setidaknya diacak ulang jika terjadi duplikasi.
        # Saat ini, base_16_digits akan diacak ulang setiap kali counter reset,
        # yang berarti setiap 1000 KTP, base akan berubah.
        # Jika ingin benar-benar unik di luar 1000 KTP, base_16_digits harus disimpan
        # atau diacak ulang setiap kali. Untuk tujuan ini, kita biarkan seperti ini.
        base_16_digits = ''.join(random.choices(string.digits, k=16))


    # Bagian 3 digit terakhir (berurutan)
    sequential_part = str(ktp_sequential_counter).zfill(3)
    ktp_sequential_counter += 1

    full_ktp_number = base_16_digits + sequential_part

    # Cek duplikasi (walaupun sangat jarang)
    while full_ktp_number in generated_ktp_numbers:
        print("Warning: KTP number duplication detected. Regenerating base.")
        ktp_sequential_counter = 0
        base_16_digits = ''.join(random.choices(string.digits, k=16))
        sequential_part = str(ktp_sequential_counter).zfill(3)
        full_ktp_number = base_16_digits + sequential_part
        ktp_sequential_counter += 1

    generated_ktp_numbers.add(full_ktp_number)
    return full_ktp_number

def create_ktp_image(user_data, output_filename="ktp_gang_desa_final.png",
                      custom_profile_photo_path=None,
                      profile_folder="profile/",
                      canvas_size_key="standard",
                      title_position="center"): # Tambahkan parameter title_position
    """
    Menghasilkan gambar KTP berdasarkan data yang diberikan.

    Args:
        user_data (dict): Kamus berisi data KTP.
        output_filename (str): Nama file untuk menyimpan gambar KTP.
        custom_profile_photo_path (str, optional): Path ke file foto profil spesifik.
        profile_folder (str): Nama folder tempat menyimpan foto-foto profil.
        canvas_size_key (str): Kunci untuk memilih konfigurasi layout ('standard' atau 'full_hd').
        title_position (str): Posisi judul KTP ('left' atau 'center').
    """
    config = LAYOUT_CONFIGS.get(canvas_size_key, LAYOUT_CONFIGS["standard"])

    width = config["width"]
    height = config["height"]
    hex_background_color = "#8B8B7A"
    rgb_background_color = hex_to_rgb(hex_background_color)
    image = Image.new("RGB", (width, height), rgb_background_color)
    draw = ImageDraw.Draw(image)

    # --- Fonts ---
    try:
        # Pastikan font 'arial.ttf' dan 'arialbd.ttf' tersedia di lingkungan eksekusi
        font_header = ImageFont.truetype("arialbd.ttf", config["font_header_size"])
        font_label = ImageFont.truetype("arial.ttf", config["font_label_size"])
        # Font untuk nilai (jawaban) dibuat bold
        font_value = ImageFont.truetype("arialbd.ttf", config["font_value_size"])
        font_date = ImageFont.truetype("arial.ttf", config["font_date_size"])
        font_bg_watermark = ImageFont.truetype("arialbd.ttf", config["watermark_font_size"]) # Gunakan arialbd untuk watermark
    except IOError:
        print("Warning: Could not load Arial fonts. Using default PIL font.")
        # Fallback ke font default jika Arial tidak ditemukan
        font_header = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default() # Fallback tetap tidak bold jika arialbd tidak ada
        font_date = ImageFont.load_default()
        font_bg_watermark = ImageFont.load_default()

    text_color_dark = "black"
    # Penyederhanaan akses elemen tuple
    wm_r = min(255, rgb_background_color[0] + 50)
    wm_g = min(255, rgb_background_color[1] + 50)
    wm_b = min(255, rgb_background_color[2] + 50)
    text_color_watermark_rgb = (wm_r, wm_g, wm_b, 80) # Watermark dengan alpha transparan

    # --- Background Texture (Diagonal Lines) ---
    line_spacing = config["line_height"] / 3 # Skala jarak garis dengan line_height
    # Penyederhanaan akses elemen tuple
    line_color = (min(255, rgb_background_color[0] + 20),
                  min(255, rgb_background_color[1] + 20),
                  min(255, rgb_background_color[2] + 20), 30) # Garis dengan alpha transparan
    line_width = 1
    # Menggambar garis diagonal dari kiri atas ke kanan bawah
    for i in range(-height, width, int(line_spacing)): # Pastikan spacing adalah integer
        draw.line([(i, 0), (i + height, height)], fill=line_color, width=line_width)

    # --- Latar belakang "GANG DESA" (watermark) ---
    # Konversi gambar ke RGBA untuk mendukung transparansi pada watermark
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    draw = ImageDraw.Draw(image) # Re-initialize draw object after mode change

    watermark_text = user_data.get('nama_penduduk', "GANG DESA").upper()
    current_watermark_font_size = config["watermark_font_size"]
    try: # Pastikan font_bg_watermark tersedia saat pertama kali digunakan
        temp_watermark_font = ImageFont.truetype("arialbd.ttf", current_watermark_font_size)
    except IOError:
        temp_watermark_font = ImageFont.load_default()


    # Logika untuk menyesuaikan ukuran font watermark agar tidak menghancurkan background
    max_text_width = width * config["watermark_max_width_ratio"]
    max_text_height = height * config["watermark_max_height_ratio"]

    # Menggunakan textbbox untuk mengukur teks
    bbox = draw.textbbox((0, 0), watermark_text, font=temp_watermark_font)
    wm_width = bbox[2] - bbox[0] # Penyederhanaan akses elemen bbox
    wm_height = bbox[3] - bbox[1] # Penyederhanaan akses elemen bbox


    while wm_width > max_text_width or wm_height > max_text_height:
        current_watermark_font_size -= 5
        if current_watermark_font_size < 30: # Batas minimum ukuran font
            current_watermark_font_size = 30
            break
        try:
            temp_watermark_font = ImageFont.truetype("arialbd.ttf", current_watermark_font_size)
        except IOError:
            temp_watermark_font = ImageFont.load_default() # Fallback
        bbox = draw.textbbox((0, 0), watermark_text, font=temp_watermark_font)
        wm_width = bbox[2] - bbox[0] # Penyederhanaan akses elemen bbox
        wm_height = bbox[3] - bbox[1] # Penyederhanaan akses elemen bbox

    font_bg_watermark = temp_watermark_font

    # Hanya menggambar watermark di posisi tengah untuk menghindari duplikasi
    watermark_positions = [
        (lambda w, h, wm_w, wm_h: (w - wm_w) / 2, lambda w, h, wm_w, wm_h: (h - wm_h) / 2 + 50) # Posisi tengah
    ]

    for pos_func_x, pos_func_y in watermark_positions:
        pos_x = pos_func_x(width, height, wm_width, wm_height)
        pos_y = pos_func_y(width, height, wm_width, wm_height)
        # Membuat layer sementara untuk watermark agar bisa di-alpha composite
        temp_text_layer = Image.new('RGBA', image.size, (255,255,255,0))
        temp_draw = ImageDraw.Draw(temp_text_layer)
        temp_draw.text((pos_x, pos_y), watermark_text, fill=text_color_watermark_rgb, font=font_bg_watermark)
        image = Image.alpha_composite(image, temp_text_layer)
        draw = ImageDraw.Draw(image) # Re-initialize draw object after alpha_composite


    # --- Judul KTP ---
    title_text = "KARTU TANDA PENDUDUK"
    gang_desa_title = user_data.get('nama_penduduk', "GANG DESA").upper()

    # Menggunakan textbbox untuk mengukur teks
    bbox_title = draw.textbbox((0, 0), title_text, font=font_header)
    title_width = bbox_title[2] - bbox_title[0] # Penyederhanaan akses elemen bbox
    title_height = bbox_title[3] - bbox_title[1] # Penyederhanaan akses elemen bbox

    bbox_gang = draw.textbbox((0, 0), gang_desa_title, font=font_header)
    gang_width = bbox_gang[2] - bbox_gang[0] # Penyederhanaan akses elemen bbox
    gang_height = bbox_gang[3] - bbox_gang[1] # Penyederhanaan akses elemen bbox

    header_y = config["header_start_y"]
    if title_position == "left":
        header_x = config["header_start_x"]
        draw.text((header_x, header_y), title_text, fill=text_color_dark, font=font_header)
        draw.text((header_x, header_y + title_height + 5), gang_desa_title, fill=text_color_dark, font=font_header)
    elif title_position == "center":
        title_x = (width - title_width) / 2
        gang_x = (width - gang_width) / 2
        draw.text((title_x, header_y), title_text, fill=text_color_dark, font=font_header)
        draw.text((gang_x, header_y + title_height + 5), gang_desa_title, fill=text_color_dark, font=font_header)

    # --- Informasi KTP (Kiri) ---
    start_x_label = config["info_start_x_label"]
    start_x_colon = config["info_start_x_colon"]
    start_x_value = config["info_start_x_value"]
    start_y = config["info_start_y"]
    line_height = config["line_height"]

    ktp_details = [
        ("No KTP", generate_random_sequential_ktp_number()),
        ("Nama", user_data.get('nama', '').upper()),
        ("Jenis Kelamin", user_data.get('jenis_kelamin', '').title()), # Pastikan kapitalisasi konsisten
        ("Domisili", user_data.get('domisili', '').title()),
        ("Agama", user_data.get('agama', '').title()),
        ("Hobi", user_data.get('hobi', '').title()),
    ]

    for i, (label, value) in enumerate(ktp_details):
        y_pos = start_y + i * line_height
        draw.text((start_x_label, y_pos), label, fill=text_color_dark, font=font_label)
        draw.text((start_x_colon, y_pos), ":", fill=text_color_dark, font=font_label)
        draw.text((start_x_value, y_pos), str(value), fill=text_color_dark, font=font_value) # Menggunakan font_value (bold)

    # --- Bagian Foto (Kanan) ---
    photo_width = config["photo_width"]
    photo_height = config["photo_height"]
    photo_x = width - photo_width - config["photo_x_offset_from_right"]
    photo_y = config["photo_y"]

    # Warna background kotak foto (pink/magenta dari referensi ktp_virtual.png)
    draw.rectangle([photo_x, photo_y,
                    photo_x + photo_width, photo_y + photo_height],
                    fill="#BB257A")

    # Lingkaran biru di dalam kotak foto
    circle_margin = config["circle_margin"]
    circle_x1 = photo_x + circle_margin
    circle_y1 = photo_y + circle_margin
    circle_x2 = photo_x + photo_width - circle_margin
    circle_y2 = photo_y + photo_height - circle_margin
    draw.ellipse([circle_x1, circle_y1, circle_x2, circle_y2], fill="#4257B7")

    # Load dan olah foto profil
    photo_to_load = None
    if custom_profile_photo_path and os.path.exists(custom_profile_photo_path):
        photo_to_load = custom_profile_photo_path
    else:
        # Jika user memilih 'n' atau custom_profile_photo_path tidak valid,
        # pilih random dari folder 'profile/'
        if os.path.isdir(profile_folder):
            photo_files = glob.glob(os.path.join(profile_folder, "*.[Pp][Nn][Gg]")) + \
                          glob.glob(os.path.join(profile_folder, "*.[Jj][Pp][Gg]")) + \
                          glob.glob(os.path.join(profile_folder, "*.[Jj][Pp][Ee][Gg]"))
            if photo_files:
                photo_to_load = random.choice(photo_files)
                print(f"Memilih foto secara acak dari '{profile_folder}': {photo_to_load}")
            else:
                print(f"Warning: Tidak ada foto ditemukan di folder '{profile_folder}'.")
        else:
            print(f"Warning: Folder '{profile_folder}' tidak ada.")

    if photo_to_load:
        try:
            profile_img = Image.open(photo_to_load).convert("RGBA")
            target_size_for_circle = (circle_x2 - circle_x1, circle_y2 - circle_y1)
            profile_img = profile_img.resize(target_size_for_circle, Image.Resampling.LANCZOS)

            mask = Image.new('L', target_size_for_circle, 0)
            mask_draw = ImageDraw.Draw(mask)
            # Penyederhanaan akses elemen tuple
            mask_draw.ellipse((0, 0, target_size_for_circle[0], target_size_for_circle[1]), fill=255)

            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            image.paste(profile_img, (circle_x1, circle_y1), mask)
            draw = ImageDraw.Draw(image) # Re-initialize draw object after paste
        except Exception as e:
            print(f"Error processing profile photo '{photo_to_load}': {e}. Area foto akan kosong.")
    else:
        print("Tidak ada jalur foto yang disediakan atau ditemukan. Area foto akan kosong.")

    # --- Tanggal Pembuatan (Kanan Bawah Foto) ---
    date_label = "Tanggal Pembuatan:"
    current_date = datetime.date.today().strftime("%d - %m - %Y")

    try:
        font_date_used = font_date
    except NameError:
        font_date_used = ImageFont.load_default()

    # Menggunakan textbbox untuk mengukur teks
    bbox_date_label = draw.textbbox((0, 0), date_label, font=font_date_used)
    date_label_width = bbox_date_label[2] - bbox_date_label[0] # Penyederhanaan akses elemen bbox
    date_label_height = bbox_date_label[3] - bbox_date_label[1] # Penyederhanaan akses elemen bbox

    bbox_date_value = draw.textbbox((0, 0), current_date, font=font_date_used)
    date_value_width = bbox_date_value[2] - bbox_date_value[0] # Penyederhanaan akses elemen bbox
    date_value_height = bbox_date_value[3] - bbox_date_value[1] # Penyederhanaan akses elemen bbox


    date_x = photo_x + (photo_width - date_label_width) / 2
    date_y = photo_y + photo_height + config["date_y_offset_from_photo_bottom"]

    draw.text((date_x, date_y), date_label, fill=text_color_dark, font=font_date_used)
    draw.text((photo_x + (photo_width - date_value_width) / 2, date_y + date_label_height + 5), current_date, fill=text_color_dark, font=font_date_used)

    image.save(output_filename)
    print(f"Gambar KTP disimpan sebagai: {output_filename}")

# --- Fungsi Utama untuk Interaksi Pengguna ---
def main():
    print("--- Pembuatan KTP Virtual ---")

    # Pilihan ukuran kanvas
    while True:
        canvas_choice = input("Pilih ukuran kanvas:\n1. Standard (900x570)\n2. Full HD (1920x1080)\nMasukkan pilihan (1/2): ")
        if canvas_choice == '1':
            selected_canvas_size = "standard"
            break
        elif canvas_choice == '2':
            selected_canvas_size = "full_hd"
            break
        else:
            print("Pilihan tidak valid. Harap masukkan 1 atau 2.")

    # Pilihan posisi judul
    while True:
        title_choice = input("Pilih posisi judul KTP:\n1. Kiri\n2. Tengah\nMasukkan pilihan (1/2): ")
        if title_choice == '1':
            selected_title_position = "left"
            break
        elif title_choice == '2':
            selected_title_position = "center"
            break
        else:
            print("Pilihan tidak valid. Harap masukkan 1 atau 2.")

    user_data = {}
    user_data['nama_penduduk'] = input("Masukkan nama dari penduduk/daerah (contoh: HPC Bread Boys): ")
    user_data['nama'] = input("Masukkan Nama: ")

    # Input jenis kelamin dengan pilihan angka
    while True:
        gender_choice = input("Pilih Jenis Kelamin:\n1. Laki-laki\n2. Perempuan\n3. Lainnya (input manual)\nMasukkan pilihan (1/2/3): ")
        if gender_choice == '1':
            user_data['jenis_kelamin'] = 'Laki-laki'
            break
        elif gender_choice == '2':
            user_data['jenis_kelamin'] = 'Perempuan'
            break
        elif gender_choice == '3':
            user_data['jenis_kelamin'] = input("Masukkan Jenis Kelamin lainnya: ")
            break
        else:
            print("Pilihan tidak valid. Harap masukkan 1, 2, atau 3.")

    user_data['domisili'] = input("Masukkan Domisili: ")
    user_data['agama'] = input("Masukkan Agama: ")
    user_data['hobi'] = input("Masukkan Hobi: ")

    profile_choice = input("Apakah Anda ingin menggunakan gambar profil dari file spesifik? (y/n): ").lower()
    profile_image_path = None
    if profile_choice == 'y':
        profile_image_path = input("Masukkan path lengkap ke file gambar profil Anda (contoh: profile/Bartender.png): ")
        profile_image_path = profile_image_path.replace('\\', '/')

    if not os.path.exists("profile"):
        os.makedirs("profile")
        print("Folder 'profile/' dibuat. Harap letakkan gambar profil Anda di sana jika Anda ingin menggunakan fitur pencarian otomatis.")

    ktp_image = create_ktp_image(user_data,
                                  output_filename=f"ktp_{user_data['nama'].replace(' ', '_').lower()}_{selected_canvas_size}.png",
                                  custom_profile_photo_path=profile_image_path,
                                  profile_folder="profile/",
                                  canvas_size_key=selected_canvas_size,
                                  title_position=selected_title_position)

    # ktp_image.show() # Uncomment this line if you want to display the image immediately after creation

if __name__ == "__main__":
    main()
