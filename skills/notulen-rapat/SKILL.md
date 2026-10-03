---
name: notulen-rapat
description: Menyusun notulen resmi dari catatan, poin-poin, atau transkrip rapat yang SUDAH berlangsung - peserta, agenda, pembahasan, keputusan, dan tindak lanjut ber-PIC dan bertenggat. Juga menjawab aturan notulen (tenggat peredaran, isi wajib). Bukan untuk menjadwalkan atau mengundang rapat.
allowed-tools: isi_notulen_rapat
---

# Notulen rapat (SOP-RPT-04)

## Menyusun notulen
1. Ambil dari catatan pengguna: judul, tanggal, waktu mulai–selesai, tempat, pimpinan rapat, notulis, peserta, agenda,
   pembahasan per agenda, keputusan, tindak lanjut.
2. Identitas rapat yang tidak ada di catatan (tanggal, waktu, tempat, pimpinan, notulis) TANYAKAN dalam satu pesan.
3. Pisahkan **keputusan** dari **pembahasan**: keputusan = hal yang disepakati ("disepakati", "diputuskan", "setuju");
   pembahasan = ringkasan diskusi. Jangan menyalin transkrip kata per kata.
4. Tindak lanjut: satu tugas per butir, `pic` satu nama, `tenggat` YYYY-MM-DD. Bila catatan tidak menyebut PIC atau
   tenggat, isi string kosong "" — JANGAN mengarang. Sistem akan menandainya.
   "Jumat ini" atau "minggu depan" diubah ke tanggal berdasarkan tanggal rapat.
5. Panggil `isi_notulen_rapat`. Nomor dan tanggal diisi sistem.
6. Sampaikan nomor notulen dan semua peringatan (mis. tindak lanjut tanpa PIC) apa adanya.

## Menjawab pertanyaan aturan
Baca `rujukan/sop-notulen.md` dengan `baca_rujukan`, lalu jawab dengan menyebut pasalnya.
