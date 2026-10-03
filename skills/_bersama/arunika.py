"""Utilitas bersama skrip skill PT Arunika Data Nusantara (fiktif).

Setiap skrip skill dijalankan sebagai proses terpisah oleh runtime:
    stdin  : {"argumen": {...field dari LLM...}, "hari_ini": "YYYY-MM-DD", "register": "path/register.json"}
    stdout : {"ok": true, "program": {...field program...}, "ringkasan": "...", "peringatan": [...]}
             atau {"ok": false, "galat": "pesan yang bisa ditindaklanjuti model"}
Skrip menangani galatnya sendiri: tidak pernah mencetak traceback ke model.
"""
import json
import os
import re
import sys
from datetime import date, datetime

_DI_SINI = os.path.dirname(os.path.abspath(__file__))
_akar = _DI_SINI
while _akar != os.path.dirname(_akar) and not os.path.exists(os.path.join(_akar, "render.py")):
    _akar = os.path.dirname(_akar)
sys.path.insert(0, _akar)
from render import rupiah, tanggal_id, terbilang_rupiah  # noqa: E402,F401

UNIT_KODE = {"Divisi Data & AI": "DAI", "Divisi Teknologi Informasi": "TI", "Divisi Keuangan": "KEU",
             "Divisi SDM & Umum": "SDM", "Divisi Pemasaran": "MKT", "Divisi Operasional": "OPS"}
KEPALA_DIVISI = {"Divisi Data & AI": "Hendra Wijaya", "Divisi Teknologi Informasi": "Agus Salim",
                 "Divisi Keuangan": "Lestari Wulandari", "Divisi SDM & Umum": "Yuliana Siregar",
                 "Divisi Pemasaran": "Andini Putri", "Divisi Operasional": "Fajar Nugroho"}
DIREKSI = {"Direktur Utama": "Bambang Sutrisno", "Direktur Operasional": "Ratna Dewi",
           "Direktur Komersial": "Arif Hidayat"}
_KATA_UNIT = [(r"data\s*(&|dan)\s*ai", "Divisi Data & AI"), (r"teknologi informasi|\bti\b", "Divisi Teknologi Informasi"),
              (r"keuangan", "Divisi Keuangan"), (r"\bsdm\b|\bumum\b|sekretariat", "Divisi SDM & Umum"),
              (r"pemasaran|\bmarketing\b", "Divisi Pemasaran"), (r"operasional", "Divisi Operasional")]


def unit_dari_teks(teks):
    """Tebak unit dari teks jabatan, mis. 'Kepala Divisi Data & AI' -> 'Divisi Data & AI'. None bila tidak dikenali."""
    t = (teks or "").lower()
    for pola, unit in _KATA_UNIT:
        if re.search(pola, t):
            return unit
    return None


def ke_tanggal(x):
    if isinstance(x, date):
        return x
    try:
        return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"tanggal {x!r} tidak valid; gunakan format YYYY-MM-DD")


def nomor_baru(awalan, register, hari_ini):
    """Nomor berurutan per awalan per bulan, mis. MPP/DAI/2026/10/0042. Register disimpan di berkas JSON."""
    d = ke_tanggal(hari_ini)
    kunci = f"{awalan}/{d:%Y}/{d:%m}"
    data = {}
    if register and os.path.exists(register):
        with open(register, encoding="utf8") as f:
            data = json.load(f)
    data[kunci] = data.get(kunci, 0) + 1
    if register:
        os.makedirs(os.path.dirname(os.path.abspath(register)), exist_ok=True)
        with open(register, "w", encoding="utf8") as f:
            json.dump(data, f, indent=1)
    return f"{kunci}/{data[kunci]:04d}"


def muat_data(berkas_skrip, nama):
    """Baca data/<nama>.json milik skill tempat skrip berada."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(berkas_skrip))), "data", nama)
    with open(p, encoding="utf8") as f:
        return json.load(f)


def jalankan(fungsi):
    """Pembungkus standar: baca stdin, panggil fungsi(argumen, hari_ini, register), cetak JSON. Tidak pernah traceback."""
    try:
        masukan = json.loads(sys.stdin.buffer.read().decode("utf8") or "{}")
        hasil = fungsi(masukan.get("argumen") or {}, masukan.get("hari_ini") or date.today().isoformat(),
                       masukan.get("register"))
        keluar = {"ok": True, **hasil}
    except ValueError as e:
        keluar = {"ok": False, "galat": str(e)}
    except KeyError as e:
        keluar = {"ok": False, "galat": f"field wajib tidak ada di argumen: {e}"}
    except Exception as e:  # galat tak terduga tetap dikembalikan sebagai pesan, bukan traceback
        keluar = {"ok": False, "galat": f"kesalahan internal skrip ({type(e).__name__}): {e}"}
    sys.stdout.buffer.write(json.dumps(keluar, ensure_ascii=False).encode("utf8"))


def bersih_nama(s):
    return re.sub(r"\s+", " ", (s or "").strip())
