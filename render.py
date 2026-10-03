"""Render template dokumen back-office (Senior AI Engineering Series, Pertemuan 6).

LLM hanya mengisi field lewat function calling; layout dikunci di template .docx; program merender.

    from render import tools, validasi, render, rupiah, terbilang_rupiah, tanggal_id

    tools(["memo_pengadaan"])                         # definisi tool untuk API chat (format OpenAI/vLLM)
    galat = validasi("memo_pengadaan", argumen_llm)   # [] bila argumen lolos skema
    render("memo_pengadaan", konteks, "memo.docx")    # konteks = argumen LLM + field program

Kebutuhan: pip install docxtpl jsonschema   (PDF opsional: LibreOffice `soffice`)
"""
import json
import os
import shutil
import subprocess
from datetime import date, datetime

from docxtpl import DocxTemplate, Listing

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMA_TEMPLATE = ["memo_pengadaan", "sppd", "nota_dinas", "notulen_rapat", "laporan_insiden", "surat_penawaran"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


# ------------------------------------------------------------------ skema & validasi
def skema(nama):
    with open(os.path.join(ROOT, "skema", nama + ".json"), encoding="utf8") as f:
        return json.load(f)


def tools(nama_list=None):
    """Daftar definisi tool siap dipakai di parameter `tools` API chat."""
    return [skema(n)["tool"] for n in (nama_list or NAMA_TEMPLATE)]


def validasi(nama, argumen):
    """Validasi argumen dari LLM terhadap skema; kembalikan daftar pesan galat yang bisa dibaca model."""
    import jsonschema
    if isinstance(argumen, str):
        try:
            argumen = json.loads(argumen)
        except json.JSONDecodeError as e:
            return [f"argumen bukan JSON yang valid: {e}"]
    params = skema(nama)["tool"]["function"]["parameters"]
    v = jsonschema.Draft202012Validator(params)
    galat = []
    for e in sorted(v.iter_errors(argumen), key=lambda e: list(e.absolute_path)):
        lokasi = ".".join(str(p) for p in e.absolute_path) or "(akar)"
        galat.append(f"{lokasi}: {e.message}")
    return galat


# ------------------------------------------------------------------ format Indonesia
def rupiah(n):
    """18500000 -> '18.500.000'"""
    return f"{int(round(n)):,}".replace(",", ".")


_SATUAN = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]


def terbilang(n):
    """Bilangan bulat ke kata (Bahasa Indonesia). 1500 -> 'seribu lima ratus'."""
    n = int(n)
    if n < 0:
        return "minus " + terbilang(-n)
    if n < 12:
        return _SATUAN[n] or "nol"
    if n < 20:
        return terbilang(n - 10) + " belas"
    if n < 100:
        return (terbilang(n // 10) + " puluh " + (terbilang(n % 10) if n % 10 else "")).strip()
    if n < 200:
        return ("seratus " + (terbilang(n - 100) if n > 100 else "")).strip()
    if n < 1000:
        return (terbilang(n // 100) + " ratus " + (terbilang(n % 100) if n % 100 else "")).strip()
    if n < 2000:
        return ("seribu " + (terbilang(n - 1000) if n > 1000 else "")).strip()
    for nilai, kata in ((10 ** 12, "triliun"), (10 ** 9, "miliar"), (10 ** 6, "juta"), (10 ** 3, "ribu")):
        if n >= nilai:
            sisa = n % nilai
            return (terbilang(n // nilai) + " " + kata + " " + (terbilang(sisa) if sisa else "")).strip()
    return str(n)


def terbilang_rupiah(n):
    """222000000 -> 'Dua ratus dua puluh dua juta rupiah'"""
    t = terbilang(n) + " rupiah"
    return t[0].upper() + t[1:]


def _ke_tanggal(x):
    if isinstance(x, datetime):
        return x
    if isinstance(x, date):
        return datetime(x.year, x.month, x.day)
    x = str(x).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(x, fmt)
        except ValueError:
            pass
    raise ValueError(f"tanggal tidak dikenali: {x!r} (pakai YYYY-MM-DD atau YYYY-MM-DD HH:MM)")


def tanggal_id(x, hari=False, jam=False):
    """'2026-10-03' -> '3 Oktober 2026'; hari=True -> 'Sabtu, 3 Oktober 2026'; jam=True menambah '14:05 WIB'."""
    d = _ke_tanggal(x)
    s = f"{d.day} {BULAN[d.month - 1]} {d.year}"
    if hari:
        s = f"{HARI[d.weekday()]}, {s}"
    if jam:
        s += f" {d:%H:%M} WIB"
    return s


# ------------------------------------------------------------------ render
def field_template(nama):
    """Himpunan variabel tingkat atas yang dibutuhkan template."""
    return DocxTemplate(os.path.join(ROOT, "templates", nama + ".docx")).get_undeclared_template_variables()


def _siapkan(x):
    if x is None:
        return "–"
    if isinstance(x, str):
        return Listing(x) if "\n" in x else x
    if isinstance(x, dict):
        return {k: _siapkan(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_siapkan(v) for v in x]
    return x


def render(nama, konteks, keluar, pdf=False):
    """Isi template `nama` dengan `konteks` (dict lengkap) dan simpan ke `keluar` (.docx).

    Gagal dengan pesan jelas bila ada field template yang belum diisi. pdf=True juga membuat PDF
    lewat LibreOffice (soffice) bila tersedia; nilai kembali = path PDF (atau .docx).
    """
    kurang = sorted(field_template(nama) - set(konteks))
    if kurang:
        raise ValueError(f"field belum diisi untuk template {nama}: {kurang}")
    tpl = DocxTemplate(os.path.join(ROOT, "templates", nama + ".docx"))
    tpl.render(_siapkan(konteks), autoescape=True)
    os.makedirs(os.path.dirname(os.path.abspath(keluar)), exist_ok=True)
    tpl.save(keluar)
    if not pdf:
        return keluar
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice tidak ditemukan; di Colab: apt-get install -y libreoffice-writer-nogui")
    folder = os.path.dirname(os.path.abspath(keluar))
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", folder, keluar],
                   check=True, capture_output=True, timeout=180)
    return os.path.splitext(os.path.abspath(keluar))[0] + ".pdf"
