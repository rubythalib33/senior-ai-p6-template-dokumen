"""Hitung field program SPPD sesuai SOP-PD-02 (pemberi tugas, lama, rincian biaya, peringatan, nomor)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import (DIREKSI, KEPALA_DIVISI, UNIT_KODE, jalankan, ke_tanggal, muat_data, nomor_baru,  # noqa: E402
                     rupiah, tanggal_id, terbilang_rupiah)

T = muat_data(__file__, "tarif.json")
KOLOM = {"I": 0, "II": 1, "III": 2}


def kategori(kota):
    for k, daftar in T["kategori_kota"].items():
        if kota.lower() in (x.lower() for x in daftar):
            return k
    return "III"


def nama_baku(kota, tabel):
    for k in tabel:
        if k.lower() == kota.lower():
            return k
    return None


def hitung(a, hari_ini, register):
    hari_ini = ke_tanggal(hari_ini)
    pergi, pulang = ke_tanggal(a["tanggal_berangkat"]), ke_tanggal(a["tanggal_kembali"])
    if pulang < pergi:
        raise ValueError("tanggal_kembali lebih awal dari tanggal_berangkat; periksa kembali tanggalnya ke pengguna")
    if pergi < hari_ini:
        raise ValueError(f"tanggal_berangkat {pergi:%Y-%m-%d} sudah lewat (hari ini {hari_ini:%Y-%m-%d}); SPPD tidak dapat dibuat mundur")
    hari = (pulang - pergi).days + 1
    malam = hari - 1
    if hari > T["maks_hari"]:
        raise ValueError(f"lama perjalanan {hari} hari melebihi batas {T['maks_hari']} hari per SPPD (SOP-PD-02 Pasal 7); "
                         "minta pengguna memecah dengan persetujuan Direksi")
    kota = a["kota_tujuan"].strip()
    if kota.lower() == T["kota_asal"].lower():
        raise ValueError("kota tujuan sama dengan kota kantor (Jakarta); perjalanan dalam kota bukan perjalanan dinas")
    kat, kol, tk = kategori(kota), None, a["tingkat"]
    kol = KOLOM[kat]
    moda = a["moda_transportasi"]
    biaya = [("Uang harian", hari, "hari", T["uang_harian"][tk][kol])]
    if malam:
        biaya.append(("Penginapan (batas atas)", malam, "malam", T["penginapan_maks"][tk][kol]))
    kereta = nama_baku(kota, T["tiket_kereta_pp"])
    if moda == "Pesawat":
        if nama_baku(kota, T["tanpa_penerbangan"]):
            raise ValueError(f"tidak ada penerbangan reguler Jakarta–{kota} (SOP-PD-02 Pasal 6 ayat 2); tanyakan apakah memakai kereta api")
        k = nama_baku(kota, T["tiket_pesawat_pp"])
        harga = T["tiket_pesawat_pp"][k] if k else T["tiket_pesawat_default"].get(kat, T["tiket_pesawat_default"]["II"])
        biaya.append(("Tiket pesawat pergi-pulang (estimasi, at cost)", 1, "paket", harga))
    elif moda in ("Kereta api", "Bus", "Kendaraan dinas"):
        if not kereta:
            raise ValueError(f"moda {moda} hanya untuk kota yang terjangkau kereta api dari Jakarta (SOP-PD-02 Pasal 6); "
                             f"{kota} tidak termasuk, tanyakan moda lain ke pengguna")
        if moda == "Kereta api":
            biaya.append(("Tiket kereta api pergi-pulang (estimasi, at cost)", 1, "paket", T["tiket_kereta_pp"][kereta]))
        elif moda == "Bus":
            biaya.append(("Tiket bus pergi-pulang (estimasi, at cost)", 1, "paket",
                          round(T["tiket_kereta_pp"][kereta] * T["bus_persen_kereta"] / 100)))
    if moda == "Kendaraan dinas":
        biaya.append(("BBM dan tol kendaraan dinas", hari, "hari", T["bbm_tol_per_hari"]))
    else:
        biaya.append(("Transportasi lokal", hari, "hari", T["transport_lokal"][kol]))

    baris, total = [], 0
    for i, (k, v, s, t) in enumerate(biaya, 1):
        total += v * t
        baris.append({"no": i, "komponen": k, "volume": v, "satuan": s, "tarif": rupiah(t), "jumlah": rupiah(v * t)})

    if tk in ("Staf", "Supervisor", "Manajer"):
        pemberi, nama_pemberi = "Kepala " + a["unit"], KEPALA_DIVISI[a["unit"]]
    elif tk == "Kepala Divisi":
        pemberi, nama_pemberi = "Direktur Operasional", DIREKSI["Direktur Operasional"]
    else:
        pemberi, nama_pemberi = "Direktur Utama", DIREKSI["Direktur Utama"]

    peringatan = []
    if (pergi - hari_ini).days < T["min_hari_pengajuan"]:
        peringatan.append(f"SPPD diajukan kurang dari {T['min_hari_pengajuan']} hari sebelum keberangkatan "
                          "(SOP-PD-02 Pasal 8 ayat 1); perlu persetujuan khusus pemberi tugas.")
    nomor = nomor_baru("SPPD/" + UNIT_KODE[a["unit"]], register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini), "pemberi_tugas": pemberi, "nama_pemberi_tugas": nama_pemberi,
               "kota_asal": T["kota_asal"], "lama_hari": hari, "lama_malam": malam, "biaya": baris,
               "total": rupiah(total), "total_terbilang": terbilang_rupiah(total), "peringatan": peringatan,
               "tanggal_berangkat": tanggal_id(pergi, hari=True), "tanggal_kembali": tanggal_id(pulang, hari=True),
               "ketentuan": [f"Uang muka maksimal {T['uang_muka_persen']}% dari total biaya, dicairkan paling lambat H-2.",
                             "Bukti tiket, boarding pass, dan tagihan hotel diserahkan paling lambat 5 hari kerja setelah kembali.",
                             "Kelebihan uang muka dikembalikan; kekurangan dibayarkan setelah verifikasi Divisi Keuangan."]}
    ringkasan = (f"SPPD {nomor}: {a['nama_pegawai']} ke {kota} (kategori {kat}) {hari} hari/{malam} malam dengan {moda.lower()}, "
                 f"total estimasi Rp{rupiah(total)}, pemberi tugas {pemberi}.")
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan, "nilai": {"total": total, "kategori": kat}}


if __name__ == "__main__":
    jalankan(hitung)
