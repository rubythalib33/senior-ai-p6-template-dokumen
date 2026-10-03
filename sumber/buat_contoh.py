"""Buat contoh/<template>.json (argumen LLM + field program), validasi, render ke contoh/hasil/, dan pratinjau PNG.

Field program dihitung oleh skrip skill di skills/<skill>/skrip/hitung.py (aturan SOP), bukan diketik tangan.

Jalankan dari root repo:  python sumber/buat_contoh.py   (pratinjau PNG butuh Microsoft Word + PyMuPDF di Windows)
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from render import NAMA_TEMPLATE, render, rupiah, tanggal_id, terbilang_rupiah, validasi  # noqa: E402

PPN = 11


def baris_harga(items):
    out, sub = [], 0
    for i, it in enumerate(items, 1):
        j = it["jumlah"] * it["harga_satuan"]
        sub += j
        out.append(dict(it, no=i, harga_satuan=rupiah(it["harga_satuan"]), jumlah_harga=rupiah(j)))
    ppn = round(sub * PPN / 100)
    return out, {"subtotal": rupiah(sub), "ppn_persen": PPN, "ppn": rupiah(ppn), "total": rupiah(sub + ppn),
                 "total_terbilang": terbilang_rupiah(sub + ppn)}


def contoh_memo():
    llm = {
        "unit_pemohon": "Divisi Data & AI", "nama_pemohon": "Dimas Prasetyo", "jabatan_pemohon": "Manajer Data Engineering",
        "perihal": "Pengadaan 12 unit laptop dan docking station untuk tim data",
        "jenis_pengadaan": "Barang",
        "latar_belakang": ("Tim data bertambah 12 orang pada kuartal IV 2026 untuk proyek asisten back-office berbasis LLM. "
                           "Laptop yang ada tidak mampu menjalankan notebook dan kontainer pengembangan secara lokal, sehingga "
                           "pekerjaan menumpuk di server bersama. Tanpa perangkat baru, jadwal pilot Desember 2026 mundur "
                           "minimal satu bulan."),
        "items": [{"uraian": "Laptop pengembang", "spesifikasi": "CPU 8 core, RAM 32 GB, SSD 1 TB, layar 14 inci, garansi 3 tahun",
                   "jumlah": 12, "satuan": "unit", "harga_satuan": 18500000},
                  {"uraian": "Docking station USB-C", "spesifikasi": "2 layar eksternal, LAN gigabit, daya 100 W",
                   "jumlah": 12, "satuan": "unit", "harga_satuan": 2150000}],
        "kebutuhan_tanggal": "2026-11-16", "sumber_anggaran": "Anggaran Capex Divisi Data & AI 2026"}
    items, angka = baris_harga(llm["items"])
    program = dict(angka, items=items, nomor="MPP/DAI/2026/10/0042", tanggal=tanggal_id("2026-10-05"),
                   kepada="Kepala Unit Pengadaan", kebutuhan_tanggal=tanggal_id(llm["kebutuhan_tanggal"]),
                   metode_pengadaan="Pemilihan langsung", min_penawaran=3,
                   dasar_metode="SOP Pengadaan SOP-PGD-01 Pasal 5 ayat (2): nilai di atas Rp200 juta s.d. Rp1 miliar",
                   peringatan=["Dalam 90 hari terakhir Divisi Data & AI sudah mengajukan pembelian laptop senilai "
                               "Rp96.000.000. Pastikan permintaan ini bukan pemecahan paket (SOP-PGD-01 Pasal 9)."],
                   lampiran=["Spesifikasi teknis / kerangka acuan kerja", "Minimal 3 penawaran harga tertulis dari vendor berbeda",
                             "Harga perkiraan sendiri (HPS)", "Konfirmasi ketersediaan anggaran dari Divisi Keuangan"],
                   persetujuan=[{"tingkat": "1", "jabatan": "Kepala Divisi Data & AI"},
                                {"tingkat": "2", "jabatan": "Kepala Divisi Keuangan"},
                                {"tingkat": "3", "jabatan": "Direktur Operasional"}])
    return llm, program


def contoh_sppd():
    llm = {"nama_pegawai": "Rina Kartika", "jabatan": "Manajer Implementasi AI", "tingkat": "Manajer",
           "unit": "Divisi Data & AI", "maksud_perjalanan": "Pendampingan go-live asisten back-office di kantor cabang Makassar",
           "kota_tujuan": "Makassar", "tanggal_berangkat": "2026-10-13", "tanggal_kembali": "2026-10-15",
           "moda_transportasi": "Pesawat"}
    komponen = [("Uang harian", 3, "hari", 530000), ("Penginapan", 2, "malam", 1250000),
                ("Tiket pesawat pergi-pulang (perkiraan)", 1, "paket", 4200000), ("Transportasi lokal", 3, "hari", 300000)]
    biaya, total = [], 0
    for i, (k, v, s, t) in enumerate(komponen, 1):
        total += v * t
        biaya.append({"no": i, "komponen": k, "volume": v, "satuan": s, "tarif": rupiah(t), "jumlah": rupiah(v * t)})
    program = {"nomor": "SPPD/DAI/2026/10/0117", "tanggal": tanggal_id("2026-10-06"),
               "pemberi_tugas": "Kepala Divisi Data & AI", "nama_pemberi_tugas": "Hendra Wijaya", "kota_asal": "Jakarta",
               "lama_hari": 3, "lama_malam": 2, "biaya": biaya, "total": rupiah(total),
               "total_terbilang": terbilang_rupiah(total), "peringatan": [],
               "tanggal_berangkat": tanggal_id(llm["tanggal_berangkat"], hari=True),
               "tanggal_kembali": tanggal_id(llm["tanggal_kembali"], hari=True),
               "ketentuan": ["Uang muka maksimal 80% dari total biaya, dicairkan paling lambat H-2.",
                             "Bukti tiket, boarding pass, dan tagihan hotel diserahkan paling lambat 5 hari kerja setelah kembali.",
                             "Kelebihan uang muka dikembalikan; kekurangan dibayarkan setelah verifikasi Divisi Keuangan."]}
    return llm, program


def contoh_nota():
    llm = {"kepada": "Kepala Divisi Keuangan", "dari": "Kepala Divisi Data & AI",
           "tembusan": ["Direktur Operasional", "Kepala Divisi Teknologi Informasi"], "sifat": "Segera",
           "lampiran": "1 berkas", "perihal": "Permohonan akses data transaksi untuk pilot prediksi keterlambatan pembayaran",
           "isi": ["Dalam rangka pilot model prediksi keterlambatan pembayaran pelanggan yang dijadwalkan mulai November 2026, "
                   "Divisi Data & AI memerlukan akses baca ke data transaksi penagihan periode Januari 2024 sampai September 2026.",
                   "Data akan diproses di lingkungan analitik internal, tanpa menyalin data identitas pelanggan ke luar sistem. "
                   "Rincian kolom yang dibutuhkan dan kontrol akses yang diusulkan kami lampirkan.",
                   "Kami mohon persetujuan Bapak paling lambat 16 Oktober 2026 agar pengujian model dapat dimulai sesuai jadwal."],
           "nama_penandatangan": "Hendra Wijaya", "jabatan_penandatangan": "Kepala Divisi Data & AI"}
    program = {"nomor": "ND/DAI/2026/10/0031", "tanggal": tanggal_id("2026-10-07"),
               "tembusan_teks": ", ".join(llm["tembusan"]) or "-"}
    return llm, program


def contoh_notulen():
    llm = {"judul_rapat": "Evaluasi pilot asisten back-office minggu ke-2", "tanggal_rapat": "2026-10-08",
           "waktu_mulai": "13:30", "waktu_selesai": "14:45", "tempat": "Ruang Rapat Lt. 7 dan daring",
           "pimpinan_rapat": "Hendra Wijaya", "notulis": "Sari Utami",
           "peserta": ["Hendra Wijaya (Kepala Divisi Data & AI)", "Dimas Prasetyo (Manajer Data Engineering)",
                       "Rina Kartika (Manajer Implementasi AI)", "Bayu Saputra (Unit Pengadaan)", "Sari Utami (Sekretariat)"],
           "agenda": ["Hasil uji pemicuan skill", "Keluhan pengguna unit pengadaan", "Rencana perluasan ke Divisi Keuangan"],
           "pembahasan": [{"agenda": "Hasil uji pemicuan skill",
                           "ringkasan": "Ketepatan pemicuan 36 dari 40 prompt. Kesalahan terbanyak: permintaan penawaran ke klien terpicu sebagai pengadaan."},
                          {"agenda": "Keluhan pengguna unit pengadaan",
                           "ringkasan": "Nomor memo sempat tidak urut karena dua pengguna membuat memo bersamaan; perlu penomoran terpusat."},
                          {"agenda": "Rencana perluasan ke Divisi Keuangan",
                           "ringkasan": "Keuangan meminta skill reimbursement; SOP-nya sedang direvisi dan baru final akhir Oktober."}],
           "keputusan": ["Deskripsi skill surat penawaran dipertegas dengan kata kunci klien eksternal.",
                         "Penomoran dokumen dipindah ke layanan terpusat sebelum perluasan.",
                         "Perluasan ke Divisi Keuangan ditunda sampai SOP reimbursement final."],
           "tindak_lanjut": [{"tugas": "Revisi deskripsi skill surat penawaran dan uji ulang 40 prompt", "pic": "Rina Kartika", "tenggat": "2026-10-15"},
                             {"tugas": "Rancang layanan penomoran dokumen terpusat", "pic": "Dimas Prasetyo", "tenggat": "2026-10-22"},
                             {"tugas": "Kumpulkan SOP reimbursement versi final", "pic": "", "tenggat": ""}]}
    tl = []
    for i, t in enumerate(llm["tindak_lanjut"], 1):
        tl.append({"no": i, "tugas": t["tugas"], "pic": t["pic"] or "–",
                   "tenggat": tanggal_id(t["tenggat"]) if t["tenggat"] else "–",
                   "catatan": "PIC dan tenggat belum ditentukan" if not t["pic"] else ""})
    program = {"nomor": "NOT/DAI/2026/10/0009", "tanggal": tanggal_id("2026-10-08"),
               "tanggal_rapat": tanggal_id(llm["tanggal_rapat"], hari=True),
               "pembahasan": [dict(p, no=i) for i, p in enumerate(llm["pembahasan"], 1)],
               "tindak_lanjut": tl,
               "peringatan": ["Tindak lanjut no. 3 belum memiliki PIC dan tenggat; tetapkan sebelum notulen diedarkan."]}
    return llm, program


def contoh_insiden():
    llm = {"judul": "Latensi asisten LLM internal naik 3 kali lipat",
           "layanan_terdampak": "Asisten back-office (server LLM Qwen3.5-4B, GPU T4)",
           "waktu_mulai": "2026-10-09 08:40", "waktu_terdeteksi": "2026-10-09 09:05", "waktu_pulih": "2026-10-09 10:20",
           "dampak": "Sedang", "urgensi": "Tinggi",
           "dampak_uraian": "Sekitar 60 pengguna unit pengadaan dan sekretariat menunggu 30–60 detik per jawaban; tidak ada data yang hilang.",
           "ringkasan": ("Waktu jawab asisten naik dari sekitar 10 detik menjadi 30–60 detik. Penyebabnya GPU server "
                         "di-throttle oleh batas daya sehingga clock turun ke sekitar 400 MHz. Layanan pulih setelah "
                         "dipindah ke host GPU lain."),
           "linimasa": [{"waktu": "2026-10-09 08:40", "kejadian": "Latensi p50 mulai naik di dasbor."},
                        {"waktu": "2026-10-09 09:05", "kejadian": "Keluhan pertama dari unit pengadaan; insiden dibuka."},
                        {"waktu": "2026-10-09 09:30", "kejadian": "nvidia-smi menunjukkan clock SM 360–435 MHz, alasan throttle SW power cap."},
                        {"waktu": "2026-10-09 10:20", "kejadian": "Layanan dipindah ke host GPU baru; latensi kembali normal."}],
           "akar_masalah": "Host GPU membatasi daya kartu di 70 W pada suhu 76 °C sehingga clock turun ke sekitar 25% dari maksimum. Tidak ada perubahan kode atau konfigurasi.",
           "tindakan_pemulihan": "Server LLM dipindah ke host GPU lain dan cache model dihangatkan ulang; latensi diverifikasi kembali ke sekitar 10 detik.",
           "tindak_lanjut": [{"tugas": "Tambahkan alarm clock SM dan alasan throttle GPU ke dasbor", "pic": "Dimas Prasetyo", "tenggat": "2026-10-16"},
                             {"tugas": "Tulis runbook pindah host GPU", "pic": "Rina Kartika", "tenggat": "2026-10-20"}],
           "pelapor": "Bayu Saputra"}
    program = {"nomor": "INS/TI/2026/10/0004", "tanggal": tanggal_id("2026-10-09"), "severity": "P2",
               "severity_label": "P2 · Tinggi — target pemulihan 4 jam", "sev_warna": "D97706", "status": "Pulih",
               "durasi": "1 jam 40 menit", "jabatan_penanggung_jawab": "Kepala Divisi Teknologi Informasi",
               "waktu_mulai": tanggal_id(llm["waktu_mulai"], jam=True),
               "waktu_terdeteksi": tanggal_id(llm["waktu_terdeteksi"], jam=True),
               "waktu_pulih": tanggal_id(llm["waktu_pulih"], jam=True),
               "linimasa": [{"waktu": l["waktu"][11:] + " WIB", "kejadian": l["kejadian"]} for l in llm["linimasa"]],
               "tindak_lanjut": [dict(t, no=i, tenggat=tanggal_id(t["tenggat"])) for i, t in enumerate(llm["tindak_lanjut"], 1)],
               "peringatan": []}
    return llm, program


def contoh_penawaran():
    llm = {"nama_klien": "PT Contoh Klien Sejahtera", "alamat_klien": "Jl. Ilustrasi No. 8, Surabaya 60271",
           "up": "Ibu Maya Lestari, Kepala Divisi Analitik",
           "perihal": "Penawaran pelatihan Generative AI untuk tim analitik",
           "pembuka": ("Menindaklanjuti diskusi pada 2 Oktober 2026 mengenai rencana pemanfaatan generative AI di tim analitik "
                       "Bapak/Ibu, bersama ini kami sampaikan penawaran pelatihan praktik tiga hari beserta pendampingan "
                       "identifikasi use case pertama."),
           "ruang_lingkup": ["Pelatihan praktik 3 hari: prompt engineering, RAG, dan evaluasi model untuk 25 peserta",
                             "Lab cloud siap pakai selama pelatihan, termasuk akses GPU",
                             "Pendampingan 1 paket untuk memilih dan membuat prototipe use case pertama"],
           "items": [{"uraian": "Pelatihan Generative AI 3 hari", "jumlah": 25, "satuan": "peserta", "harga_satuan": 4500000},
                     {"uraian": "Pendampingan use case dan prototipe", "jumlah": 1, "satuan": "paket", "harga_satuan": 25000000}],
           "masa_berlaku_hari": 30, "syarat_pembayaran": "50% setelah PO terbit, 50% setelah berita acara serah terima",
           "nama_penandatangan": "Andini Putri", "jabatan_penandatangan": "Kepala Divisi Pemasaran"}
    items, angka = baris_harga(llm["items"])
    program = dict(angka, items=items, nomor="PNW/MKT/2026/10/0058", tanggal=tanggal_id("2026-10-05"), lampiran="-",
                   ketentuan=[f"Penawaran berlaku {llm['masa_berlaku_hari']} hari, sampai {tanggal_id('2026-11-04')}.",
                              f"Syarat pembayaran: {llm['syarat_pembayaran']}.",
                              f"Harga sudah termasuk PPN {PPN}%."])
    return llm, program


SKILL_TEMPLATE = {"memo_pengadaan": ("pengadaan-barang-jasa", "2026-10-05"), "sppd": ("perjalanan-dinas", "2026-10-06"),
                  "nota_dinas": ("nota-dinas", "2026-10-07"), "notulen_rapat": ("notulen-rapat", "2026-10-08"),
                  "laporan_insiden": ("laporan-insiden", "2026-10-09"), "surat_penawaran": ("surat-penawaran", "2026-10-05")}


def program_dari_skill(nama, llm, register):
    """Field program dihitung oleh skrip skill (SOP), sama seperti di runtime notebook."""
    skill, hari_ini = SKILL_TEMPLATE[nama]
    skrip = os.path.join(ROOT, "skills", skill, "skrip", "hitung.py")
    masuk = json.dumps({"argumen": llm, "hari_ini": hari_ini, "register": register}, ensure_ascii=False).encode("utf8")
    r = subprocess.run([sys.executable, skrip], input=masuk, capture_output=True, timeout=60)
    hasil = json.loads(r.stdout.decode("utf8"))
    assert hasil["ok"], (nama, hasil)
    return hasil["program"], hasil["ringkasan"]


CONTOH = {"memo_pengadaan": contoh_memo, "sppd": contoh_sppd, "nota_dinas": contoh_nota,
          "notulen_rapat": contoh_notulen, "laporan_insiden": contoh_insiden, "surat_penawaran": contoh_penawaran}


def ke_pdf_word(docx_paths):
    """Konversi .docx -> .pdf memakai Microsoft Word (hanya untuk pratinjau lokal di Windows)."""
    daftar = ";".join(os.path.abspath(p) for p in docx_paths)
    ps = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"foreach ($p in '{daftar}'.Split(';')) {{ $d = $w.Documents.Open($p, $false, $true); "
          "$d.ExportAsFixedFormat(($p -replace '\\.docx$', '.pdf'), 17); $d.Close($false) }; $w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


if __name__ == "__main__":
    hasil = os.path.join(ROOT, "contoh", "hasil")
    os.makedirs(hasil, exist_ok=True)
    if os.path.exists(os.path.join(hasil, "register_contoh.json")):
        os.remove(os.path.join(hasil, "register_contoh.json"))
    keluaran = []
    for nama in NAMA_TEMPLATE:
        llm, _ilustrasi = CONTOH[nama]()
        program, ringkasan = program_dari_skill(nama, llm, os.path.join(hasil, "register_contoh.json"))
        print("  ", ringkasan)
        galat = validasi(nama, llm)
        assert not galat, (nama, galat)
        with open(os.path.join(ROOT, "contoh", nama + ".json"), "w", encoding="utf8") as f:
            json.dump({"llm": llm, "program": program}, f, ensure_ascii=False, indent=2)
        konteks = dict(llm, **program)
        keluaran.append(render(nama, konteks, os.path.join(hasil, nama + ".docx")))
        print("ok", nama)
    if "--pratinjau" in sys.argv:
        import fitz
        ke_pdf_word(keluaran)
        os.makedirs(os.path.join(ROOT, "pratinjau"), exist_ok=True)
        for p in keluaran:
            pdf = p[:-5] + ".pdf"
            doc = fitz.open(pdf)
            for i, hal in enumerate(doc):
                hal.get_pixmap(dpi=110).save(os.path.join(ROOT, "pratinjau", f"{os.path.basename(p)[:-5]}-{i + 1}.png"))
            print("pratinjau", os.path.basename(pdf), len(doc), "halaman")
