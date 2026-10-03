---
name: nota-dinas
description: Menyusun nota dinas, yaitu surat resmi INTERNAL antar-jabatan atau antar-unit di PT Arunika untuk permohonan, pemberitahuan, laporan singkat, atau undangan internal (mis. permohonan akses data ke Divisi TI, pemberitahuan pemeliharaan server ke seluruh kepala divisi). Juga menjawab aturan tata naskah dinas - penomoran, sifat, tembusan, bahasa baku. Bukan untuk surat ke pihak luar perusahaan.
allowed-tools: isi_nota_dinas
---

# Nota dinas (SOP-TND-03)

## Menyusun nota dinas
1. Pastikan Anda tahu: jabatan pengirim (Dari) dan penerima (Kepada), perihal, isi yang ingin disampaikan, nama dan
   jabatan penanda tangan. Sifat, tembusan, dan lampiran boleh ditanyakan; bila pengguna tidak menyebut, pakai
   sifat "Biasa", tembusan kosong, lampiran "-".
2. Tulis Kepada, Dari, dan Tembusan sebagai JABATAN. Bila pengguna menyebut nama ("ke Bu Lestari"), tanyakan atau
   gunakan jabatannya bila sudah disebut.
3. Susun `isi` 2–4 paragraf (lihat pola di bawah), bahasa Indonesia baku tanpa singkatan tidak baku.
   Jangan menulis penutup "Demikian disampaikan..." — sudah ada di template.
4. Panggil `isi_nota_dinas`. Nomor dan tanggal diisi sistem.
5. Sampaikan nomor nota dinas dan peringatan apa adanya; tawarkan perbaikan bila ada peringatan bahasa.

## Pola isi yang baik
- Pembuka: "Sehubungan dengan rencana pilot model prediksi keterlambatan pembayaran yang dimulai November 2026, ..."
- Isi: kebutuhan konkret dengan data — periode, sistem, jumlah, tanggal.
- Harapan: "Kami mohon persetujuan Bapak/Ibu paling lambat 16 Oktober 2026 agar ..."
Contoh buruk: "Mohon dibantu ya Bu utk akses datanya, urgent!!" (tidak baku, tanpa data, tanpa tenggat).

## Menjawab pertanyaan tata naskah
Baca `rujukan/tata-naskah.md` dengan `baca_rujukan`, lalu jawab dengan menyebut pasalnya.
