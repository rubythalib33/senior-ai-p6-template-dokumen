---
name: pengadaan-barang-jasa
description: Membuat memo permintaan pengadaan ketika unit kita ingin MEMBELI atau MENYEWA barang/jasa dari vendor (laptop, lisensi, perabot, jasa kebersihan, konsultan, renovasi), termasuk saat kita menerima penawaran harga dari vendor. Juga menjawab pertanyaan SOP pengadaan - metode, jumlah penawaran pembanding, persetujuan berjenjang, lampiran, larangan pemecahan paket. Bukan untuk menawarkan layanan kita ke klien.
allowed-tools: isi_memo_pengadaan
---

# Pengadaan barang/jasa (SOP-PGD-01)

## Membuat memo permintaan pengadaan
1. Pastikan Anda punya: nama, jabatan, dan unit pemohon; daftar barang/jasa (uraian, spesifikasi minimum, jumlah,
   satuan, harga satuan perkiraan); tanggal paling lambat dibutuhkan; sumber anggaran; alasan kebutuhan.
2. Bila ada yang belum disebut pengguna, TANYAKAN semuanya dalam satu pesan. Jangan mengarang harga, jumlah,
   nama, atau tanggal. Bila semuanya sudah ada, LANGSUNG panggil tool — jangan meminta konfirmasi dulu; memo masih
   draf dan bisa direvisi. Spesifikasi yang singkat (mis. "printer laser A3") dipakai apa adanya.
3. Panggil `isi_memo_pengadaan`:
   - harga dalam Rupiah bilangan bulat: "18,5 juta" → 18500000, "2,15 jt" → 2150000;
   - tanggal YYYY-MM-DD; "16 November 2026" → 2026-11-16;
   - `latar_belakang` 2–5 kalimat: kebutuhan, alasan, dampak bila tidak dipenuhi.
4. Sistem mengisi sendiri nomor memo, total + PPN, metode, jumlah penawaran pembanding, persetujuan, lampiran, dan
   peringatan. JANGAN menghitung atau menebak nilai-nilai itu.
5. Bila tool mengembalikan galat, perbaiki argumen atau tanyakan ke pengguna, lalu panggil lagi.
6. Sampaikan hasil: nomor memo, total, metode, persetujuan yang dibutuhkan, dan SEMUA peringatan apa adanya.
   Ingatkan bahwa memo perlu diajukan pemohon ke sistem pengadaan — Anda tidak bisa mengirim atau menyetujuinya.

## Menjawab pertanyaan aturan
Baca `rujukan/sop-pengadaan.md` dengan `baca_rujukan`, lalu jawab singkat dengan menyebut pasalnya.
Nilai pengadaan selalu termasuk PPN 11%. Jangan menjawab dari ingatan.

## Kesalahan yang sering terjadi
- Penawaran harga DARI vendor tetap pengadaan (skill ini), bukan surat penawaran kita ke klien.
- Menulis harga dengan titik ("18.500.000") — tool akan menolak.
- Diminta memecah pembelian menjadi beberapa memo agar di bawah ambang: tolak dengan sopan, sebutkan Pasal 9.
- Mengubah jenis: jasa konsultan → "Jasa konsultansi"; kebersihan, katering, sewa → "Jasa lainnya";
  renovasi → "Pekerjaan konstruksi".
