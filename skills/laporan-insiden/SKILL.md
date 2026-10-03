---
name: laporan-insiden
description: Membuat laporan insiden layanan TI (aplikasi atau sistem down, lambat, error, VPN/email/jaringan putus, serangan atau kebocoran data) dan menentukan severity P1–P4 dengan matriks dampak × urgensi. Juga menjawab aturan insiden - severity, target pemulihan, tenggat pelaporan, postmortem. Bukan untuk kecelakaan kerja, keluhan SDM, atau kerusakan gedung.
allowed-tools: isi_laporan_insiden
---

# Laporan insiden layanan TI (SOP-INS-05)

## Membuat laporan
1. Kumpulkan: judul singkat, layanan terdampak, waktu mulai, waktu terdeteksi, waktu pulih (kosong bila belum),
   siapa yang terdampak, kronologi, akar masalah (atau "Masih diinvestigasi"), tindakan pemulihan, tindak lanjut,
   nama pelapor. Bila tanggal tidak disebut, gunakan tanggal hari ini. Hal penting yang tidak diketahui → TANYAKAN.
2. Nilai **dampak** (siapa terdampak):
   - Tinggi: seluruh perusahaan atau fungsi inti mati untuk semua, atau dugaan kebocoran data;
   - Sedang: satu divisi/sekelompok pengguna, atau layanan melambat tapi masih bisa dipakai;
   - Rendah: sedikit pengguna, ada cara kerja alternatif.
3. Nilai **urgensi** (seberapa cepat): Tinggi bila masih berlangsung dan merugikan atau memburuk; Sedang bila masih
   berlangsung/berpotensi berulang dan perlu selesai hari ini; Rendah bila sudah pulih dan tidak berulang, atau bisa
   dijadwalkan.
4. Panggil `isi_laporan_insiden` dengan waktu "YYYY-MM-DD HH:MM". Severity, status, durasi, penanggung jawab, nomor
   diisi sistem dari matriks — JANGAN menentukan P1–P4 sendiri.
5. Sampaikan nomor laporan, severity, target pemulihan, penanggung jawab, dan semua peringatan (mis. kewajiban postmortem).

## Menjawab pertanyaan aturan
Baca `rujukan/sop-insiden.md` dengan `baca_rujukan`. Untuk pertanyaan severity, baca matriks Pasal 4 (baris = urgensi,
kolom = dampak) dan target pemulihan Pasal 5.
