"""Hitung field program notulen sesuai SOP-RPT-04 (nomor, tanggal, penomoran baris, pemeriksaan tindak lanjut)."""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import jalankan, ke_tanggal, nomor_baru, tanggal_id  # noqa: E402


def tambah_hari_kerja(d, n):
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def hitung(a, hari_ini, register):
    hari_ini = ke_tanggal(hari_ini)
    tgl = ke_tanggal(a["tanggal_rapat"])
    if tgl > hari_ini:
        raise ValueError(f"tanggal_rapat {tgl:%Y-%m-%d} belum terjadi; notulen hanya untuk rapat yang sudah berlangsung "
                         "(SOP-RPT-04 Pasal 1)")
    if a["waktu_selesai"] <= a["waktu_mulai"]:
        raise ValueError("waktu_selesai harus setelah waktu_mulai (format HH:MM); periksa ke pengguna")
    peringatan, tl = [], []
    for i, t in enumerate(a["tindak_lanjut"], 1):
        kurang = [k for k in ("pic", "tenggat") if not (t.get(k) or "").strip()]
        catatan = ""
        if kurang:
            catatan = " dan ".join({"pic": "PIC", "tenggat": "tenggat"}[k] for k in kurang) + " belum ditentukan"
            peringatan.append(f"Tindak lanjut no. {i} ('{t['tugas'][:60]}') belum memiliki {catatan.replace(' belum ditentukan', '')}; "
                              "lengkapi sebelum notulen diedarkan (SOP-RPT-04 Pasal 3 ayat 6).")
        tenggat = (t.get("tenggat") or "").strip()
        if tenggat and ke_tanggal(tenggat) < tgl:
            peringatan.append(f"Tenggat tindak lanjut no. {i} ({tanggal_id(tenggat)}) lebih awal dari tanggal rapat.")
        tl.append({"no": i, "tugas": t["tugas"], "pic": (t.get("pic") or "").strip() or "–",
                   "tenggat": tanggal_id(tenggat) if tenggat else "–", "catatan": catatan})
    batas = tambah_hari_kerja(tgl, 1)
    if hari_ini > batas:
        peringatan.append(f"Notulen seharusnya diedarkan paling lambat {tanggal_id(batas)} (1 hari kerja setelah rapat, "
                          "SOP-RPT-04 Pasal 4 ayat 1).")
    nomor = nomor_baru("NOT/SEK", register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini), "tanggal_rapat": tanggal_id(tgl, hari=True),
               "pembahasan": [dict(p, no=i) for i, p in enumerate(a["pembahasan"], 1)], "tindak_lanjut": tl,
               "peringatan": peringatan}
    ringkasan = (f"Notulen {nomor}: {a['judul_rapat']} ({tanggal_id(tgl, hari=True)}), {len(a['peserta'])} peserta, "
                 f"{len(a['keputusan'])} keputusan, {len(tl)} tindak lanjut.")
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan}


if __name__ == "__main__":
    jalankan(hitung)
