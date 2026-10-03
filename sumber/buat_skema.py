"""Tulis skema/<template>.json: definisi tool function calling (field yang diisi LLM) + daftar field program.

Prinsip: LLM kecil hanya mengisi fakta dari permintaan pengguna. Semua yang ditentukan SOP atau aritmetika
(nomor dokumen, tanggal surat, total, PPN, terbilang, metode pengadaan, rantai persetujuan, tarif) diisi program.

Jalankan dari root repo:  python sumber/buat_skema.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNIT = ["Divisi Data & AI", "Divisi Teknologi Informasi", "Divisi Keuangan", "Divisi SDM & Umum",
        "Divisi Pemasaran", "Divisi Operasional"]
TINGKAT = ["Staf", "Supervisor", "Manajer", "Kepala Divisi", "Direksi"]
TANGGAL = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$", "description": "Format YYYY-MM-DD."}
JAM = {"type": "string", "pattern": r"^\d{2}:\d{2}$", "description": "Format HH:MM (24 jam, WIB)."}
WAKTU = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", "description": "Format YYYY-MM-DD HH:MM (WIB)."}
RUPIAH = {"type": "integer", "minimum": 0, "description": "Rupiah, bilangan bulat tanpa titik/koma, mis. 18500000."}


def teks(maks, desk, minimal=1):
    return {"type": "string", "minLength": minimal, "maxLength": maks, "description": desk}


def daftar_teks(maks_item, maks_len, desk, minimal=1):
    return {"type": "array", "minItems": minimal, "maxItems": maks_item, "items": teks(maks_len, "Satu butir."),
            "description": desk}


def tool(nama, desk, props, wajib):
    return {"type": "function", "function": {
        "name": "isi_" + nama, "description": desk,
        "parameters": {"type": "object", "properties": props, "required": wajib, "additionalProperties": False}}}


ATURAN = (" Isi hanya dari informasi yang diberikan pengguna; bila ada field wajib yang tidak diketahui, "
          "tanyakan ke pengguna, jangan mengarang. Nomor dokumen, tanggal surat, total, pajak, dan persetujuan "
          "diisi otomatis oleh sistem.")

SKEMA = {
    "memo_pengadaan": {
        "tool": tool("memo_pengadaan",
                     "Isi memo permintaan pengadaan barang/jasa internal (kita yang membeli dari vendor)." + ATURAN,
                     {"unit_pemohon": {"type": "string", "enum": UNIT, "description": "Unit kerja pemohon."},
                      "nama_pemohon": teks(60, "Nama lengkap pemohon."),
                      "jabatan_pemohon": teks(60, "Jabatan pemohon, mis. 'Manajer Data Engineering'."),
                      "perihal": teks(100, "Ringkas apa yang dibeli, mis. 'Pengadaan 12 unit laptop untuk tim data'."),
                      "jenis_pengadaan": {"type": "string", "enum": ["Barang", "Jasa lainnya", "Jasa konsultansi",
                                                                     "Pekerjaan konstruksi"]},
                      "latar_belakang": teks(900, "Alasan kebutuhan dan dampak bila tidak dipenuhi, 2–5 kalimat.", 40),
                      "items": {"type": "array", "minItems": 1, "maxItems": 15, "description": "Daftar barang/jasa.",
                                "items": {"type": "object", "additionalProperties": False,
                                          "required": ["uraian", "spesifikasi", "jumlah", "satuan", "harga_satuan"],
                                          "properties": {
                                              "uraian": teks(80, "Nama barang/jasa."),
                                              "spesifikasi": teks(200, "Spesifikasi minimum."),
                                              "jumlah": {"type": "integer", "minimum": 1},
                                              "satuan": teks(20, "Mis. unit, lisensi, paket, bulan."),
                                              "harga_satuan": RUPIAH}}},
                      "kebutuhan_tanggal": dict(TANGGAL, description="Tanggal paling lambat barang/jasa dibutuhkan, YYYY-MM-DD."),
                      "sumber_anggaran": teks(100, "Mis. 'Anggaran Capex Divisi Data & AI 2026'.")},
                     ["unit_pemohon", "nama_pemohon", "jabatan_pemohon", "perihal", "jenis_pengadaan",
                      "latar_belakang", "items", "kebutuhan_tanggal", "sumber_anggaran"]),
        "field_program": {
            "nomor": "Nomor memo sesuai SOP penomoran", "tanggal": "Tanggal memo (format Indonesia)",
            "kepada": "Penerima memo sesuai SOP (unit pengadaan)", "items": "Baris item + no, jumlah_harga (diformat)",
            "subtotal": "Rupiah terformat", "ppn_persen": "Tarif PPN", "ppn": "Rupiah terformat",
            "total": "Rupiah terformat", "total_terbilang": "Terbilang total",
            "metode_pengadaan": "Metode sesuai ambang nilai SOP", "min_penawaran": "Jumlah penawaran pembanding minimal",
            "dasar_metode": "Pasal SOP yang dipakai", "peringatan": "Daftar peringatan (mis. indikasi pemecahan paket)",
            "lampiran": "Checklist lampiran wajib sesuai metode", "persetujuan": "Rantai persetujuan [{tingkat, jabatan}]",
            "kebutuhan_tanggal": "Ditulis ulang ke format Indonesia"}},

    "sppd": {
        "tool": tool("sppd", "Isi surat perintah perjalanan dinas (SPPD) untuk seorang pegawai." + ATURAN,
                     {"nama_pegawai": teks(60, "Nama pegawai yang berangkat."),
                      "jabatan": teks(60, "Jabatan pegawai."),
                      "tingkat": {"type": "string", "enum": TINGKAT, "description": "Tingkat jabatan untuk tarif."},
                      "unit": {"type": "string", "enum": UNIT},
                      "maksud_perjalanan": teks(200, "Tujuan dinas, mis. 'Audit implementasi model di kantor klien'."),
                      "kota_tujuan": teks(40, "Nama kota tujuan."),
                      "tanggal_berangkat": TANGGAL, "tanggal_kembali": TANGGAL,
                      "moda_transportasi": {"type": "string", "enum": ["Pesawat", "Kereta api", "Bus", "Kendaraan dinas"]}},
                     ["nama_pegawai", "jabatan", "tingkat", "unit", "maksud_perjalanan", "kota_tujuan",
                      "tanggal_berangkat", "tanggal_kembali", "moda_transportasi"]),
        "field_program": {
            "nomor": "Nomor SPPD", "tanggal": "Tanggal surat", "pemberi_tugas": "Jabatan pemberi tugas sesuai SOP",
            "nama_pemberi_tugas": "Nama pemberi tugas", "kota_asal": "Kota kantor asal", "lama_hari": "Jumlah hari",
            "lama_malam": "Jumlah malam", "biaya": "Rincian [{no, komponen, volume, satuan, tarif, jumlah}] dari tabel tarif",
            "total": "Rupiah terformat", "total_terbilang": "Terbilang", "peringatan": "Daftar peringatan",
            "ketentuan": "Ketentuan pertanggungjawaban", "tanggal_berangkat": "Format Indonesia",
            "tanggal_kembali": "Format Indonesia"}},

    "nota_dinas": {
        "tool": tool("nota_dinas", "Isi nota dinas: surat resmi internal antar-unit." + ATURAN,
                     {"kepada": teks(80, "Jabatan penerima, mis. 'Kepala Divisi Keuangan'."),
                      "dari": teks(80, "Jabatan pengirim."),
                      "tembusan": {"type": "array", "maxItems": 6, "items": teks(80, "Jabatan."),
                                   "description": "Jabatan penerima tembusan; boleh kosong."},
                      "sifat": {"type": "string", "enum": ["Biasa", "Segera", "Sangat segera", "Rahasia"]},
                      "lampiran": teks(60, "Mis. '1 berkas' atau '-'."),
                      "perihal": teks(100, "Pokok surat."),
                      "isi": daftar_teks(6, 900, "Paragraf isi surat, 1–6 paragraf, bahasa resmi."),
                      "nama_penandatangan": teks(60, "Nama penanda tangan."),
                      "jabatan_penandatangan": teks(80, "Jabatan penanda tangan.")},
                     ["kepada", "dari", "tembusan", "sifat", "lampiran", "perihal", "isi", "nama_penandatangan",
                      "jabatan_penandatangan"]),
        "field_program": {"nomor": "Nomor nota dinas", "tanggal": "Tanggal surat",
                          "tembusan_teks": "Tembusan digabung dengan koma, atau '-'"}},

    "notulen_rapat": {
        "tool": tool("notulen_rapat", "Isi notulen rapat dari catatan atau transkrip yang diberikan pengguna." + ATURAN,
                     {"judul_rapat": teks(120, "Judul rapat."),
                      "tanggal_rapat": TANGGAL, "waktu_mulai": JAM, "waktu_selesai": JAM,
                      "tempat": teks(80, "Ruang rapat atau tautan daring."),
                      "pimpinan_rapat": teks(60, "Nama pimpinan rapat."),
                      "notulis": teks(60, "Nama notulis."),
                      "peserta": daftar_teks(30, 80, "Nama (dan jabatan) peserta."),
                      "agenda": daftar_teks(10, 120, "Butir agenda."),
                      "pembahasan": {"type": "array", "minItems": 1, "maxItems": 10,
                                     "items": {"type": "object", "additionalProperties": False,
                                               "required": ["agenda", "ringkasan"],
                                               "properties": {"agenda": teks(120, "Butir agenda."),
                                                              "ringkasan": teks(900, "Ringkasan diskusi.")}}},
                      "keputusan": daftar_teks(15, 300, "Keputusan rapat; kosongkan bila tidak ada.", 0),
                      "tindak_lanjut": {"type": "array", "maxItems": 20,
                                        "items": {"type": "object", "additionalProperties": False,
                                                  "required": ["tugas", "pic", "tenggat"],
                                                  "properties": {"tugas": teks(200, "Tugas."),
                                                                 "pic": teks(60, "Nama PIC; '' bila tidak disebut.", 0),
                                                                 "tenggat": {"type": "string",
                                                                             "pattern": r"^(\d{4}-\d{2}-\d{2})?$",
                                                                             "description": "YYYY-MM-DD; '' bila tidak disebut."}}}}},
                     ["judul_rapat", "tanggal_rapat", "waktu_mulai", "waktu_selesai", "tempat", "pimpinan_rapat",
                      "notulis", "peserta", "agenda", "pembahasan", "keputusan", "tindak_lanjut"]),
        "field_program": {"nomor": "Nomor notulen", "tanggal": "Tanggal penandatanganan",
                          "tanggal_rapat": "Format 'Hari, tanggal'", "pembahasan": "+ no",
                          "tindak_lanjut": "+ no, catatan (mis. 'PIC belum ditentukan'), tenggat diformat",
                          "peringatan": "Daftar peringatan"}},

    "laporan_insiden": {
        "tool": tool("laporan_insiden", "Isi laporan insiden layanan TI." + ATURAN,
                     {"judul": teks(120, "Judul singkat insiden."),
                      "layanan_terdampak": teks(120, "Nama layanan/sistem yang terganggu."),
                      "waktu_mulai": WAKTU, "waktu_terdeteksi": WAKTU,
                      "waktu_pulih": {"type": "string", "pattern": r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})?$",
                                      "description": "YYYY-MM-DD HH:MM; '' bila belum pulih."},
                      "dampak": {"type": "string", "enum": ["Tinggi", "Sedang", "Rendah"],
                                 "description": "Tinggi: banyak pengguna/fungsi inti; Sedang: sebagian; Rendah: sedikit/fungsi minor."},
                      "urgensi": {"type": "string", "enum": ["Tinggi", "Sedang", "Rendah"],
                                  "description": "Seberapa cepat harus ditangani."},
                      "dampak_uraian": teks(600, "Siapa dan apa yang terdampak."),
                      "ringkasan": teks(600, "Ringkasan kejadian 2–4 kalimat."),
                      "linimasa": {"type": "array", "minItems": 1, "maxItems": 20,
                                   "items": {"type": "object", "additionalProperties": False,
                                             "required": ["waktu", "kejadian"],
                                             "properties": {"waktu": WAKTU, "kejadian": teks(300, "Apa yang terjadi.")}}},
                      "akar_masalah": teks(800, "Akar masalah; tulis 'Masih diinvestigasi' bila belum diketahui."),
                      "tindakan_pemulihan": teks(800, "Langkah yang sudah dilakukan."),
                      "tindak_lanjut": {"type": "array", "maxItems": 10,
                                        "items": {"type": "object", "additionalProperties": False,
                                                  "required": ["tugas", "pic", "tenggat"],
                                                  "properties": {"tugas": teks(200, "Tindakan pencegahan."),
                                                                 "pic": teks(60, "Nama PIC; '' bila belum ada.", 0),
                                                                 "tenggat": {"type": "string",
                                                                             "pattern": r"^(\d{4}-\d{2}-\d{2})?$"}}}},
                      "pelapor": teks(60, "Nama pelapor.")},
                     ["judul", "layanan_terdampak", "waktu_mulai", "waktu_terdeteksi", "waktu_pulih", "dampak",
                      "urgensi", "dampak_uraian", "ringkasan", "linimasa", "akar_masalah", "tindakan_pemulihan",
                      "tindak_lanjut", "pelapor"]),
        "field_program": {"nomor": "Nomor laporan", "tanggal": "Tanggal laporan",
                          "severity": "P1–P4 dari matriks dampak × urgensi", "severity_label": "Nama severity + SLA",
                          "sev_warna": "Warna heksadesimal pita severity", "status": "Pulih / Berlangsung",
                          "durasi": "Durasi gangguan", "jabatan_penanggung_jawab": "Penanggung jawab sesuai severity",
                          "linimasa": "waktu diformat", "tindak_lanjut": "+ no, tenggat diformat",
                          "peringatan": "Daftar peringatan", "waktu_*": "Format Indonesia"}},

    "surat_penawaran": {
        "tool": tool("surat_penawaran",
                     "Isi surat penawaran harga ke klien eksternal (kita yang menjual layanan/produk)." + ATURAN,
                     {"nama_klien": teks(100, "Nama organisasi klien."),
                      "alamat_klien": teks(200, "Alamat klien."),
                      "up": teks(80, "Nama/jabatan yang dituju (U.p.)."),
                      "perihal": teks(100, "Mis. 'Penawaran Pelatihan Generative AI untuk Tim Analitik'."),
                      "pembuka": teks(700, "Paragraf pembuka: konteks kebutuhan klien dan apa yang ditawarkan.", 40),
                      "ruang_lingkup": daftar_teks(10, 200, "Butir ruang lingkup pekerjaan."),
                      "items": {"type": "array", "minItems": 1, "maxItems": 10,
                                "items": {"type": "object", "additionalProperties": False,
                                          "required": ["uraian", "jumlah", "satuan", "harga_satuan"],
                                          "properties": {"uraian": teks(120, "Komponen yang ditawarkan."),
                                                         "jumlah": {"type": "integer", "minimum": 1},
                                                         "satuan": teks(20, "Mis. paket, peserta, hari."),
                                                         "harga_satuan": RUPIAH}}},
                      "masa_berlaku_hari": {"type": "integer", "minimum": 7, "maximum": 90},
                      "syarat_pembayaran": teks(200, "Mis. '50% di muka, 50% setelah BAST'."),
                      "nama_penandatangan": teks(60, "Nama penanda tangan."),
                      "jabatan_penandatangan": teks(80, "Jabatan penanda tangan.")},
                     ["nama_klien", "alamat_klien", "up", "perihal", "pembuka", "ruang_lingkup", "items",
                      "masa_berlaku_hari", "syarat_pembayaran", "nama_penandatangan", "jabatan_penandatangan"]),
        "field_program": {"nomor": "Nomor surat keluar", "tanggal": "Tanggal surat", "lampiran": "Mis. '-'",
                          "items": "+ no, harga diformat", "subtotal": "Rupiah", "ppn_persen": "Tarif PPN",
                          "ppn": "Rupiah", "total": "Rupiah", "total_terbilang": "Terbilang",
                          "ketentuan": "Masa berlaku (tanggal), syarat pembayaran, pajak"}},
}

if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "skema"), exist_ok=True)
    for nama, isi in SKEMA.items():
        with open(os.path.join(ROOT, "skema", nama + ".json"), "w", encoding="utf8") as f:
            json.dump(isi, f, ensure_ascii=False, indent=2)
        print("ditulis skema/" + nama + ".json")
