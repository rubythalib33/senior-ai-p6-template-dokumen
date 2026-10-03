"""Hitung field program surat penawaran sesuai SOP-MKT-06 (harga, PPN, masa berlaku, ketentuan, penanda tangan, nomor)."""
import os
import re
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import DIREKSI, KEPALA_DIVISI, jalankan, ke_tanggal, nomor_baru, rupiah, tanggal_id, terbilang_rupiah  # noqa: E402

PPN, BATAS_TTD, BATAS_LEGAL = 11, 500000000, 1000000000


def hitung(a, hari_ini, register):
    hari_ini = ke_tanggal(hari_ini)
    items, subtotal = [], 0
    for i, it in enumerate(a["items"], 1):
        if it["jumlah"] <= 0 or it["harga_satuan"] <= 0:
            raise ValueError(f"item {i}: jumlah dan harga_satuan harus lebih dari 0")
        j = it["jumlah"] * it["harga_satuan"]
        subtotal += j
        items.append(dict(it, no=i, harga_satuan=rupiah(it["harga_satuan"]), jumlah_harga=rupiah(j)))
    ppn = round(subtotal * PPN / 100)
    total = subtotal + ppn
    peringatan = []
    hari = a["masa_berlaku_hari"]
    if not 14 <= hari <= 60:
        baru = min(max(hari, 14), 60)
        peringatan.append(f"Masa berlaku {hari} hari di luar rentang 14–60 hari; disesuaikan menjadi {baru} hari (SOP-MKT-06 Pasal 4).")
        hari = baru
    berlaku = hari_ini + timedelta(days=hari)
    dp = [int(x) for x in re.findall(r"(\d{1,3})\s*%", a["syarat_pembayaran"])]
    if dp and dp[0] > 50:
        peringatan.append(f"Uang muka {dp[0]}% melebihi batas 50%; perlu persetujuan Kepala Divisi Keuangan (Pasal 5).")
    if total > BATAS_TTD:
        jab, nama = "Direktur Komersial", DIREKSI["Direktur Komersial"]
    else:
        jab, nama = "Kepala Divisi Pemasaran", KEPALA_DIVISI["Divisi Pemasaran"]
    if a["jabatan_penandatangan"].strip().lower() != jab.lower():
        peringatan.append(f"Penanda tangan disesuaikan dari '{a['jabatan_penandatangan']}' menjadi {jab} ({nama}) "
                          f"karena nilai Rp{rupiah(total)} (SOP-MKT-06 Pasal 6).")
    if total > BATAS_LEGAL:
        peringatan.append("Nilai di atas Rp1.000.000.000: wajib ditinjau Legal sebelum dikirim (Pasal 6).")
    nomor = nomor_baru("PNW/MKT", register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini), "lampiran": "-", "items": items,
               "subtotal": rupiah(subtotal), "ppn_persen": PPN, "ppn": rupiah(ppn), "total": rupiah(total),
               "total_terbilang": terbilang_rupiah(total), "jabatan_penandatangan": jab, "nama_penandatangan": nama,
               "ketentuan": [f"Penawaran berlaku {hari} hari, sampai {tanggal_id(berlaku)}.",
                             f"Syarat pembayaran: {a['syarat_pembayaran'].rstrip('.')}.",
                             f"Harga sudah termasuk PPN {PPN}%."],
               "peringatan": peringatan}
    ringkasan = (f"Surat penawaran {nomor} ke {a['nama_klien']}: total Rp{rupiah(total)} termasuk PPN, berlaku sampai "
                 f"{tanggal_id(berlaku)}, ditandatangani {jab}.")
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan, "nilai": {"total": total}}


if __name__ == "__main__":
    jalankan(hitung)
