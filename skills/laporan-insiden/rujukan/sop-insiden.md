# SOP-INS-05 · Manajemen Insiden Layanan TI PT Arunika Data Nusantara

Versi 2.3 · berlaku 1 Januari 2026 · pemilik: Divisi Teknologi Informasi. Ilustratif (perusahaan fiktif).

## Pasal 1 · Definisi
Insiden layanan TI adalah gangguan atau penurunan kualitas layanan TI (aplikasi, jaringan, email, VPN, server,
layanan AI) dan setiap kejadian keamanan informasi (akses tidak sah, kebocoran data, malware).
Kecelakaan kerja, keluhan SDM, dan kerusakan fasilitas gedung BUKAN insiden layanan TI.

## Pasal 2 · Dampak
- **Tinggi**: seluruh perusahaan atau satu fungsi inti tidak dapat bekerja (mis. absensi, email, ERP mati untuk semua),
  atau ada dugaan kebocoran data pribadi/pelanggan.
- **Sedang**: satu divisi atau sekelompok pengguna terganggu, atau layanan melambat signifikan tetapi masih bisa dipakai.
- **Rendah**: sedikit pengguna atau fungsi pendukung, ada cara kerja alternatif.

## Pasal 3 · Urgensi
- **Tinggi**: gangguan masih berlangsung dan berdampak finansial/hukum, atau memburuk dengan cepat.
- **Sedang**: perlu ditangani pada hari yang sama.
- **Rendah**: dapat dijadwalkan.

## Pasal 4 · Matriks severity
| Urgensi \ Dampak | Tinggi | Sedang | Rendah |
|---|---|---|---|
| Tinggi | P1 | P2 | P3 |
| Sedang | P2 | P3 | P4 |
| Rendah | P3 | P4 | P4 |

## Pasal 5 · Target pemulihan dan penanggung jawab
| Severity | Nama | Target pemulihan | Penanggung jawab |
|---|---|---|---|
| P1 | Kritis | 2 jam | Direktur Operasional |
| P2 | Tinggi | 4 jam | Kepala Divisi Teknologi Informasi |
| P3 | Sedang | 1 hari kerja | Manajer Infrastruktur TI |
| P4 | Rendah | 3 hari kerja | Supervisor Service Desk |

## Pasal 6 · Pelaporan
1. Insiden P1 dilaporkan ke penanggung jawab paling lambat 30 menit setelah terdeteksi; P2 paling lambat 2 jam.
2. Laporan insiden bernomor `INS/TI/<tahun>/<bulan>/<nomor urut 4 digit>` memuat linimasa, dampak, akar masalah,
   tindakan pemulihan, dan tindak lanjut pencegahan ber-PIC dan bertenggat.
3. Insiden P1 dan P2 wajib ditindaklanjuti dengan **postmortem** tertulis paling lambat 5 hari kerja setelah pulih.
4. Akar masalah yang belum diketahui ditulis "Masih diinvestigasi"; laporan diperbarui setelah investigasi selesai.

## Pasal 7 · Insiden keamanan
Dugaan kebocoran data diperlakukan minimal P2 dan wajib diberitahukan kepada Petugas Pelindungan Data paling lambat
1 x 24 jam.
