---
name: perjalanan-dinas
description: Membuat surat perintah perjalanan dinas (SPPD) beserta rincian biayanya ketika pegawai PT Arunika ditugaskan ke kota lain untuk urusan kantor (visit klien, audit, instalasi, pelatihan di luar kota). Juga menjawab pertanyaan uang harian, batas penginapan, moda transportasi, dan tenggat pengajuan perjalanan dinas. Bukan untuk cuti atau perjalanan pribadi.
allowed-tools: isi_sppd
---

# Perjalanan dinas (SOP-PD-02)

## Membuat SPPD
1. Pastikan Anda punya: nama pegawai, jabatan, tingkat (Staf, Supervisor, Manajer, Kepala Divisi, Direksi), unit,
   maksud perjalanan, kota tujuan, tanggal berangkat dan kembali, moda transportasi.
2. Bila ada yang belum disebut, TANYAKAN dalam satu pesan. Tingkat boleh disimpulkan dari jabatan:
   "Manajer ..." → Manajer, "Kepala Divisi ..." → Kepala Divisi, "Direktur ..." → Direksi,
   "Staf ..."/"Analis ..."/"Engineer ..." → Staf, "Supervisor ..." → Supervisor.
3. Panggil `isi_sppd` dengan tanggal YYYY-MM-DD. Kota asal selalu Jakarta dan tidak perlu diisi.
4. Sistem menghitung sendiri lama perjalanan, uang harian, penginapan, tiket, transportasi lokal, pemberi tugas,
   nomor, dan peringatan. JANGAN menghitung biaya sendiri.
5. Bila tool mengembalikan galat (mis. moda tidak tersedia ke kota itu), sampaikan ke pengguna dan tanyakan pilihannya.
6. Sampaikan nomor SPPD, total estimasi, pemberi tugas, dan semua peringatan. SPPD ditandatangani pemberi tugas;
   Anda tidak bisa mengajukan atau mencairkan uang muka.

## Menjawab pertanyaan tarif dan aturan
Baca `rujukan/sop-perjalanan-dinas.md` dengan `baca_rujukan`. Tentukan kategori kota (Pasal 3) dulu, baru baca
tabel tingkat × kategori. Sebutkan angka persis dalam Rupiah dan pasalnya.

## Kesalahan yang sering terjadi
- Menghitung malam sama dengan hari. Berangkat 13, kembali 15 = 3 hari, 2 malam (sistem yang menghitung).
- Memilih "Pesawat" ke Bandung — tidak ada penerbangan reguler; tanyakan apakah kereta api.
- Membuat SPPD untuk cuti pribadi — tolak dan arahkan ke kebijakan cuti.
