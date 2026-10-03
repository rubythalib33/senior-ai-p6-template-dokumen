---
name: pengadaan-barang-jasa
description: Membuat memo permintaan pengadaan ketika unit kita ingin MEMBELI atau MENYEWA barang/jasa dari vendor (laptop, lisensi, perabot, jasa kebersihan, konsultan, renovasi), termasuk saat kita menerima penawaran harga dari vendor. Juga menjawab pertanyaan SOP pengadaan - metode, jumlah penawaran pembanding, persetujuan berjenjang, lampiran, larangan pemecahan paket. Bukan untuk menawarkan layanan kita ke klien.
allowed-tools: isi_memo_pengadaan
---

# Pengadaan barang/jasa (SOP-PGD-01) — varian instruksi naratif

Kumpulkan data pemohon, barang/jasa (uraian, spesifikasi, jumlah, satuan, harga satuan), tanggal kebutuhan, sumber
anggaran, dan alasan; tanyakan yang belum ada. Bila semuanya sudah ada, LANGSUNG panggil tool — jangan meminta konfirmasi dulu; memo masih draf dan bisa direvisi. Spesifikasi yang singkat (mis. "printer laser A3") dipakai apa adanya. Lalu panggil `isi_memo_pengadaan`. Pada varian ini Anda sendiri yang
mengisi metode, jumlah penawaran, persetujuan, PPN, dan nomor berdasarkan aturan berikut.

Nilai pengadaan adalah jumlah seluruh rincian ditambah PPN sebelas persen. Untuk pembelian kecil yang nilainya tidak
lebih dari lima puluh juta rupiah, cukup dilakukan pembelian langsung dengan satu bukti harga. Jika nilainya sudah
melewati lima puluh juta tetapi belum melewati dua ratus juta, gunakan pengadaan langsung dengan dua penawaran tertulis.
Nilai di atas dua ratus juta sampai satu miliar memakai pemilihan langsung dengan tiga penawaran, sedangkan nilai di
atas satu miliar harus melalui tender dengan minimal tiga peserta. Pengecualiannya jasa konsultansi: begitu nilainya
lebih dari lima puluh juta, metodenya seleksi dengan tiga proposal.

Persetujuan bertingkat dan kumulatif. Kepala divisi pemohon selalu menyetujui. Kepala Divisi Keuangan ikut menyetujui
kalau nilainya lebih dari lima puluh juta, Direktur Operasional ikut bila lebih dari dua ratus juta, dan Direktur Utama
ikut bila lebih dari satu miliar. Tuliskan jabatan persetujuan dengan nama divisi lengkap, misalnya
"Kepala Divisi Data & AI".

Nomor memo berbentuk MPP/kode unit/tahun/bulan/nomor urut empat digit, dengan kode unit DAI, TI, KEU, SDM, MKT, atau
OPS; gunakan nomor urut 0001.

Sampaikan nomor memo, total, metode, dan persetujuan ke pengguna. Anda tidak bisa mengirim memo ke sistem pengadaan.
