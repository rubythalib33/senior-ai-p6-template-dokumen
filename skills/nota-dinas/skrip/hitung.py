"""Hitung field program nota dinas sesuai SOP-TND-03 (nomor, tanggal, tembusan) dan periksa aturan penulisan."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import UNIT_KODE, jalankan, nomor_baru, tanggal_id, unit_dari_teks  # noqa: E402

JABATAN = re.compile(r"\b(kepala|direktur|manajer|supervisor|staf|seluruh|sekretaris|ketua|koordinator|divisi|unit)\b", re.I)
SINGKATAN = {"yg": "yang", "dgn": "dengan", "utk": "untuk", "krn": "karena", "tsb": "tersebut", "dll": "dan lain-lain",
             "sdh": "sudah", "blm": "belum", "tdk": "tidak", "jg": "juga"}


def hitung(a, hari_ini, register):
    unit = unit_dari_teks(a["dari"])
    if not unit:
        raise ValueError("field 'dari' harus jabatan yang menyebut unitnya, mis. 'Kepala Divisi Keuangan' "
                         "(SOP-TND-03 Pasal 3); tanyakan jabatan pengirim ke pengguna")
    peringatan = []
    for kolom in ("kepada", "dari"):
        if not JABATAN.search(a[kolom]):
            peringatan.append(f"'{kolom}' sebaiknya jabatan, bukan nama orang: '{a[kolom]}' (SOP-TND-03 Pasal 3 ayat 1).")
    teks = " ".join(a["isi"]).lower()
    salah = sorted({s for s in SINGKATAN if re.search(rf"\b{s}\b", teks)})
    if salah:
        peringatan.append("Singkatan tidak baku: " + ", ".join(f"{s} → {SINGKATAN[s]}" for s in salah)
                          + " (SOP-TND-03 Pasal 5 ayat 2).")
    if len(a["isi"]) > 4:
        peringatan.append(f"Isi {len(a['isi'])} paragraf; idealnya 2–4 paragraf agar muat satu halaman (Pasal 4 ayat 5).")
    if a["perihal"].strip().endswith("."):
        peringatan.append("Perihal tidak diakhiri titik (Pasal 3 ayat 5).")
    nomor = nomor_baru("ND/" + UNIT_KODE[unit], register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini),
               "tembusan_teks": ", ".join(t.strip() for t in a["tembusan"] if t.strip()) or "-"}
    ringkasan = f"Nota dinas {nomor} dari {a['dari']} kepada {a['kepada']}, sifat {a['sifat'].lower()}, perihal: {a['perihal']}."
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan}


if __name__ == "__main__":
    jalankan(hitung)
