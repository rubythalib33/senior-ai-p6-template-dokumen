---
name: pengadaan-barang-jasa
description: Membuat memo permintaan pengadaan ketika unit kita ingin MEMBELI atau MENYEWA barang/jasa dari vendor (laptop, lisensi, perabot, jasa kebersihan, konsultan, renovasi), termasuk saat kita menerima penawaran harga dari vendor. Juga menjawab pertanyaan SOP pengadaan - metode, jumlah penawaran pembanding, persetujuan berjenjang, lampiran, larangan pemecahan paket. Bukan untuk menawarkan layanan kita ke klien.
allowed-tools: isi_memo_pengadaan
---

# Pengadaan barang/jasa (SOP-PGD-01) — varian template/pseudokode

1. Kumpulkan data pemohon, barang/jasa, tanggal kebutuhan, sumber anggaran, dan alasan; tanyakan yang belum ada.
2. Hitung dan isi field berikut dengan algoritma ini, lalu panggil `isi_memo_pengadaan`:

```
subtotal = jumlah(item.jumlah × item.harga_satuan)
nilai    = subtotal × 1,11                      # termasuk PPN 11%
ppn_persen = 11

jika jenis_pengadaan == "Jasa konsultansi" dan nilai > 50.000.000:
    metode = "Seleksi";             min_penawaran = 3
jika tidak, jika nilai <= 50.000.000:
    metode = "Pembelian langsung";  min_penawaran = 1
jika tidak, jika nilai <= 200.000.000:
    metode = "Pengadaan langsung";  min_penawaran = 2
jika tidak, jika nilai <= 1.000.000.000:
    metode = "Pemilihan langsung";  min_penawaran = 3
jika tidak:
    metode = "Tender";              min_penawaran = 3

persetujuan = ["Kepala " + unit_pemohon]          # mis. "Kepala Divisi Data & AI"
jika nilai > 50.000.000:    tambahkan "Kepala Divisi Keuangan" (bila belum ada)
jika nilai > 200.000.000:   tambahkan "Direktur Operasional"
jika nilai > 1.000.000.000: tambahkan "Direktur Utama"

kode = {Divisi Data & AI: DAI, Divisi Teknologi Informasi: TI, Divisi Keuangan: KEU,
        Divisi SDM & Umum: SDM, Divisi Pemasaran: MKT, Divisi Operasional: OPS}
nomor = "MPP/" + kode[unit_pemohon] + "/" + tahun + "/" + bulan_2_digit + "/0001"
```

3. Sampaikan nomor memo, total, metode, dan persetujuan. Anda tidak bisa mengirim memo ke sistem pengadaan.
