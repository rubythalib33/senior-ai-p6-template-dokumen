"""Hitung field program memo pengadaan sesuai SOP-PGD-01 (nilai, metode, persetujuan, lampiran, peringatan, nomor)."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import (KEPALA_DIVISI, UNIT_KODE, jalankan, ke_tanggal, muat_data, nomor_baru,  # noqa: E402
                     rupiah, tanggal_id, terbilang_rupiah)

ATURAN = muat_data(__file__, "aturan.json")
RIWAYAT = muat_data(__file__, "riwayat_pengadaan.json")
_KATA_UMUM = {"jasa", "pengadaan", "pembelian", "sewa", "unit", "paket", "baru"}


def metode_untuk(nilai, jenis):
    k = ATURAN["konsultansi"]
    if jenis == "Jasa konsultansi" and nilai > k["batas_bawah"]:
        return k
    for m in ATURAN["metode"]:
        if m["batas_atas"] is None or nilai <= m["batas_atas"]:
            return m


def kata_kunci(uraian):
    kata = [w for w in re.findall(r"[a-z0-9]+", uraian.lower()) if len(w) > 2 and w not in _KATA_UMUM]
    return kata[0] if kata else ""


def sejenis(argumen, hari_ini):
    """Pengadaan sejenis oleh unit yang sama dalam jendela 90 hari (Pasal 9)."""
    kunci = {kata_kunci(it["uraian"]) for it in argumen["items"]} - {""}
    hasil = []
    for r in RIWAYAT:
        selisih = (hari_ini - ke_tanggal(r["tanggal"])).days
        if r["unit"] == argumen["unit_pemohon"] and 0 <= selisih <= ATURAN["jendela_pemecahan_hari"] \
                and kata_kunci(r["uraian"]) in kunci:
            hasil.append(r)
    return hasil


def hitung(argumen, hari_ini, register):
    hari_ini = ke_tanggal(hari_ini)
    items, subtotal = [], 0
    for i, it in enumerate(argumen["items"], 1):
        if it["jumlah"] <= 0 or it["harga_satuan"] <= 0:
            raise ValueError(f"item {i}: jumlah dan harga_satuan harus lebih dari 0")
        j = it["jumlah"] * it["harga_satuan"]
        subtotal += j
        items.append(dict(it, no=i, harga_satuan=rupiah(it["harga_satuan"]), jumlah_harga=rupiah(j)))
    ppn = round(subtotal * ATURAN["ppn_persen"] / 100)
    total = subtotal + ppn

    butuh = ke_tanggal(argumen["kebutuhan_tanggal"])
    if butuh < hari_ini:
        raise ValueError(f"kebutuhan_tanggal {butuh:%Y-%m-%d} sudah lewat (hari ini {hari_ini:%Y-%m-%d}); "
                         "tanyakan tanggal kebutuhan yang benar ke pengguna (SOP-PGD-01 Pasal 10)")

    peringatan = []
    lalu = sejenis(argumen, hari_ini)
    nilai_dasar = total
    if lalu:
        nilai_lalu = sum(r["nilai"] for r in lalu)
        nilai_dasar = total + nilai_lalu
        m_sendiri, m_gabung = metode_untuk(total, argumen["jenis_pengadaan"]), metode_untuk(nilai_dasar, argumen["jenis_pengadaan"])
        teks = "; ".join(f"{r['uraian']} Rp{rupiah(r['nilai'])} ({tanggal_id(r['tanggal'])})" for r in lalu)
        akibat = (f"metode naik dari {m_sendiri['metode']} menjadi {m_gabung['metode']}"
                  if m_sendiri["metode"] != m_gabung["metode"] else f"metode tetap {m_gabung['metode']}")
        peringatan.append(f"Ada pengadaan sejenis oleh {argumen['unit_pemohon']} dalam 90 hari terakhir: {teks}. "
                          f"Nilai gabungan Rp{rupiah(nilai_dasar)} dipakai untuk metode dan persetujuan ({akibat}); "
                          "pastikan ini bukan pemecahan paket (SOP-PGD-01 Pasal 9).")
    m = metode_untuk(nilai_dasar, argumen["jenis_pengadaan"])
    if (butuh - hari_ini).days < m["waktu_proses_hari"]:
        peringatan.append(f"Tanggal kebutuhan {tanggal_id(butuh)} kurang dari waktu proses minimal {m['waktu_proses_hari']} "
                          f"hari untuk {m['metode']}; Unit Pengadaan dapat menolak percepatan (Pasal 10).")

    persetujuan, tingkat = [], 1
    for p in ATURAN["persetujuan"]:
        if nilai_dasar > p["di_atas"] or p["di_atas"] == 0:
            jab = p["jabatan"].replace("Kepala Divisi pemohon", "Kepala " + argumen["unit_pemohon"])
            if jab in [x["jabatan"] for x in persetujuan]:
                continue
            persetujuan.append({"tingkat": str(tingkat), "jabatan": jab})
            tingkat += 1

    lampiran = ["Spesifikasi teknis atau kerangka acuan kerja", "Konfirmasi ketersediaan anggaran dari Divisi Keuangan"]
    if m["min_penawaran"] >= 2:
        lampiran.append(f"Minimal {m['min_penawaran']} {'proposal teknis dan biaya' if m['metode'] == 'Seleksi' else 'penawaran harga tertulis'} dari penyedia berbeda")
    if m["metode"] in ("Pemilihan langsung", "Tender", "Seleksi"):
        lampiran.append("Harga perkiraan sendiri (HPS)")
    if m["metode"] == "Tender":
        lampiran.append("Rencana kerja dan susunan panitia tender")
    if argumen["jenis_pengadaan"] == "Jasa konsultansi":
        lampiran.append("Kerangka acuan kerja (KAK) dan proposal teknis")
    if argumen["jenis_pengadaan"] == "Pekerjaan konstruksi" and nilai_dasar > 200000000:
        lampiran.append("Kajian teknis dan gambar kerja")

    nomor = nomor_baru("MPP/" + UNIT_KODE[argumen["unit_pemohon"]], register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini), "kepada": ATURAN["kepada"], "items": items,
               "subtotal": rupiah(subtotal), "ppn_persen": ATURAN["ppn_persen"], "ppn": rupiah(ppn),
               "total": rupiah(total), "total_terbilang": terbilang_rupiah(total),
               "metode_pengadaan": m["metode"], "min_penawaran": m["min_penawaran"], "dasar_metode": m["pasal"],
               "peringatan": peringatan, "lampiran": lampiran, "persetujuan": persetujuan,
               "kebutuhan_tanggal": tanggal_id(butuh)}
    ringkasan = (f"Memo {nomor}: total Rp{rupiah(total)} (termasuk PPN {ATURAN['ppn_persen']}%), metode {m['metode']}, "
                 f"minimal {m['min_penawaran']} penawaran pembanding, persetujuan: "
                 + " → ".join(p["jabatan"] for p in persetujuan) + ".")
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan,
            "nilai": {"total": total, "nilai_dasar": nilai_dasar}}


if __name__ == "__main__":
    jalankan(hitung)
