---
name: surat-penawaran
description: Membuat surat penawaran harga (quotation) dari PT Arunika kepada KLIEN eksternal ketika KITA yang MENJUAL layanan atau produk kita (pelatihan, workshop, konsultasi AI, implementasi sistem). Juga menjawab aturan penawaran ke klien - masa berlaku, syarat pembayaran, siapa penanda tangan. Bukan untuk penawaran yang kita terima dari vendor saat membeli (itu pengadaan).
allowed-tools: isi_surat_penawaran
---

# Surat penawaran ke klien (SOP-MKT-06)

## Cek arah transaksi dulu
- Kita menjual ke klien → skill ini.
- Vendor menawarkan sesuatu kepada kita / kita mau membeli → BUKAN skill ini; gunakan skill `pengadaan-barang-jasa`.

## Membuat surat penawaran
1. Pastikan Anda punya: nama dan alamat klien, pihak yang dituju (U.p.), perihal, konteks kebutuhan klien,
   ruang lingkup, komponen harga (uraian, jumlah, satuan, harga satuan), syarat pembayaran, nama penanda tangan.
2. Yang belum disebut TANYAKAN dalam satu pesan. Jangan mengarang harga atau nama klien.
3. Masa berlaku: 30 hari bila pengguna tidak menyebut. Syarat pembayaran standar: "50% setelah PO terbit, 50% setelah
   berita acara serah terima".
4. Panggil `isi_surat_penawaran` dengan harga Rupiah bilangan bulat. `pembuka` 2–3 kalimat yang menyebut konteks klien.
5. Nomor, PPN, total, tanggal berlaku, dan penanda tangan yang sah diisi sistem (penanda tangan bisa disesuaikan
   menurut nilai). Sampaikan nomor, total, dan semua peringatan.

## Menjawab pertanyaan aturan
Baca `rujukan/sop-penawaran.md` dengan `baca_rujukan`, lalu jawab dengan menyebut pasalnya.
