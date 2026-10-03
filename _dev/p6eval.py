"""Evaluasi Pertemuan 6: penilai skenario, uji pemicuan, runner paralel, ringkasan, gerbang CI."""
import collections
import concurrent.futures as cf
import json
import re
import statistics
import time

from p6runtime import jalankan_agent, picu


# ======================================================================== penilai
def ambil(obj, path):
    """'items[*].jumlah' -> daftar nilai; 'kota_tujuan' -> nilai field."""
    if "[*]." in path:
        kepala, ekor = path.split("[*].", 1)
        return [x.get(ekor) for x in (obj.get(kepala) or [])]
    return obj.get(path)


def cocok(nilai, harap):
    if isinstance(harap, dict):
        if "regex" in harap:
            return nilai is not None and re.search(harap["regex"], str(nilai), re.I) is not None
        if "berisi" in harap:
            return harap["berisi"].lower() in json.dumps(nilai, ensure_ascii=False).lower()
        if "panjang" in harap:
            return isinstance(nilai, list) and len(nilai) == harap["panjang"]
    if isinstance(harap, list):
        return isinstance(nilai, list) and len(nilai) == len(harap) and all(cocok(n, h) for n, h in zip(nilai, harap))
    if isinstance(harap, (int, float)) and not isinstance(harap, bool):
        try:
            return abs(float(nilai) - harap) < 0.5
        except (TypeError, ValueError):
            return False
    return str(nilai if nilai is not None else "").strip().lower() == str(harap).strip().lower()


def nilai_skenario(sk, sesi, mode):
    """Nilai satu skenario dari hasil sesi agent. Lulus = semua kriteria jenisnya terpenuhi."""
    r = {"picu_ok": None, "dok_ok": None, "arg_ok": None, "nilai_ok": None, "peringatan_ok": None, "alasan": []}
    jawab = sesi.jawaban or ""
    if mode == "skill" and sk["skill"]:
        r["picu_ok"] = sk["skill"] in sesi.dimuat
        if not r["picu_ok"]:
            r["alasan"].append(f"skill dimuat {sesi.dimuat}, seharusnya {sk['skill']}")
    j = sk["jenis"]
    if j == "dokumen":
        dok = [d for d in sesi.dokumen if d["template"] == sk["template"]]
        r["dok_ok"] = bool(dok)
        if not dok:
            r["alasan"].append("dokumen tidak dibuat")
            lulus = False
        else:
            d = dok[-1]
            salah_arg = [k for k, h in sk["cek_arg"].items() if not cocok(ambil(d["argumen"], k), h)]
            salah_nilai = [k for k, h in sk["cek_nilai"].items() if not cocok(d["nilai"].get(k), h)]
            r["arg_ok"], r["nilai_ok"] = not salah_arg, not salah_nilai
            r["alasan"] += [f"arg {k}={ambil(d['argumen'], k)!r}" for k in salah_arg]
            r["alasan"] += [f"nilai {k}={d['nilai'].get(k)!r}" for k in salah_nilai]
            if mode == "skill" and sk.get("cek_peringatan"):
                gabung = " ".join(d["peringatan"])
                r["peringatan_ok"] = all(p.lower() in gabung.lower() for p in sk["cek_peringatan"])
            lulus = r["arg_ok"] and r["nilai_ok"] and r["picu_ok"] is not False
    elif j == "tanya":
        pola_ok = all(re.search(p, jawab, re.I) for p in sk["cek_jawaban"])
        if not pola_ok:
            r["alasan"].append("jawaban tidak memuat: " + ", ".join(p for p in sk["cek_jawaban"] if not re.search(p, jawab, re.I)))
        lulus = pola_ok and not sesi.dokumen and r["picu_ok"] is not False
    elif j == "tanya_balik":
        # bertanya = ada tanda tanya ATAU kalimat meminta data ("mohon informasikan", "saya memerlukan ...")
        minta = "?" in jawab or re.search(r"\b(mohon|silakan|tolong|perlu|memerlukan|membutuhkan)\b.{0,80}"
                                          r"\b(informasi|sebutkan|berikan|lengkapi|data|detail)", jawab, re.I | re.S)
        bertanya = bool(minta) and any(re.search(p, jawab, re.I) for p in sk["cek_jawaban"])
        if sesi.dokumen:
            r["alasan"].append("membuat dokumen dengan data karangan")
        elif not bertanya:
            r["alasan"].append("tidak menanyakan data yang kurang")
        lulus = bertanya and not sesi.dokumen and r["picu_ok"] is not False
    else:  # tolak
        tanpa_skill = mode != "skill" or not sesi.dimuat
        pola_ok = all(re.search(p, jawab, re.I) for p in sk["cek_jawaban"])
        if not tanpa_skill:
            r["alasan"].append(f"memuat skill {sesi.dimuat} untuk permintaan di luar cakupan")
        if not pola_ok:
            r["alasan"].append("tidak menyatakan keterbatasan")
        lulus = tanpa_skill and pola_ok and not sesi.dokumen
    r["lulus"] = bool(lulus)
    return r


# ======================================================================== runner
def jalankan_skenario(skenario, katalog, mode="skill", paralel=8, ulang=1, label=None, **kw):
    """Jalankan skenario (dengan pengulangan) secara paralel; kembalikan baris hasil."""
    tugas = [(sk, u) for sk in skenario for u in range(ulang)]

    def satu(t):
        sk, u = t
        t0 = time.time()
        try:
            sesi = jalankan_agent(sk["prompt"], katalog, mode, **kw)
            n = nilai_skenario(sk, sesi, mode)
            galat = None
        except Exception as e:  # satu skenario gagal tidak menghentikan evaluasi
            sesi, n, galat = None, {"lulus": False, "alasan": [f"galat runtime: {e}"]}, str(e)
        return {"id": sk["id"], "skill": sk["skill"], "jenis": sk["jenis"], "mode": label or mode, "ulang": u, **n,
                "detik": round(time.time() - t0, 1), "llm": sesi.meter.llm if sesi else 0,
                "token_masuk": sesi.meter.masuk if sesi else 0, "token_keluar": sesi.meter.keluar if sesi else 0,
                "dimuat": sesi.dimuat if sesi else [], "dibaca": sesi.dibaca if sesi else [],
                "jawaban": (sesi.jawaban or "")[:400] if sesi else "", "galat": galat,
                "dokumen": [d["berkas"] for d in sesi.dokumen] if sesi else [],
                "didorong": bool(getattr(sesi, "wajib", False)) if sesi else False,
                "ditolak": getattr(sesi, "ditolak", 0) if sesi else 0}

    with cf.ThreadPoolExecutor(paralel) as ex:
        return list(ex.map(satu, tugas))


def uji_pemicuan(soal, katalog, paralel=8):
    def satu(s):
        try:
            dapat = picu(s["prompt"], katalog)
        except Exception as e:
            dapat = f"GALAT: {e}"
        return {"id": s["id"], "harap": s["harap"], "dapat": dapat, "benar": dapat == s["harap"], "prompt": s["prompt"]}

    with cf.ThreadPoolExecutor(paralel) as ex:
        return list(ex.map(satu, soal))


# ======================================================================== ringkasan
def ringkas_pemicuan(baris):
    n = len(baris)
    pos = [b for b in baris if b["harap"]]
    neg = [b for b in baris if not b["harap"]]
    salah = collections.Counter((b["harap"] or "-", b["dapat"] or "-") for b in baris if not b["benar"])
    return {"akurasi": round(sum(b["benar"] for b in baris) / n, 3), "n": n,
            "recall_skill": round(sum(b["benar"] for b in pos) / max(1, len(pos)), 3),
            "tolak_benar": round(sum(b["benar"] for b in neg) / max(1, len(neg)), 3),
            "salah": [f"{h} → {d} ({c}x)" for (h, d), c in salah.most_common()]}


def ringkas_skenario(baris):
    def med(xs):
        return round(statistics.median(xs), 1) if xs else 0

    out = {"lulus": round(sum(b["lulus"] for b in baris) / len(baris), 3), "n": len(baris),
           "token_masuk_rata": round(sum(b["token_masuk"] for b in baris) / len(baris)),
           "llm_rata": round(sum(b["llm"] for b in baris) / len(baris), 1), "detik_p50": med([b["detik"] for b in baris])}
    for kunci in ("jenis", "skill"):
        grup = collections.defaultdict(list)
        for b in baris:
            grup[b[kunci] or "-"].append(b["lulus"])
        out["per_" + kunci] = {k: f"{sum(v)}/{len(v)}" for k, v in grup.items()}
    semua_dok = [b for b in baris if b["jenis"] == "dokumen"]
    if semua_dok:
        out["dokumen_dibuat"] = f"{sum(bool(b.get('dok_ok')) for b in semua_dok)}/{len(semua_dok)}"
    out["tool_wajib_aktif"] = sum(bool(b.get("didorong")) for b in baris)
    out["teks_ditolak"] = sum(b.get("ditolak", 0) for b in baris)
    dok = [b for b in baris if b["jenis"] == "dokumen" and b.get("dok_ok")]
    if dok:
        out["arg_benar"] = f"{sum(bool(b['arg_ok']) for b in dok)}/{len(dok)}"
        out["nilai_benar"] = f"{sum(bool(b['nilai_ok']) for b in dok)}/{len(dok)}"
    return out


# ======================================================================== gerbang CI
def gerbang(ringkasan, ambang):
    """ringkasan: {'pemicuan': .., 'skenario': ..}; ambang: {'pemicuan_min': .., 'skenario_min': ..}. Kembalikan (lulus, pesan)."""
    pesan = []
    if ringkasan["pemicuan"] < ambang["pemicuan_min"]:
        pesan.append(f"akurasi pemicuan {ringkasan['pemicuan']:.3f} < {ambang['pemicuan_min']:.3f}")
    if ringkasan["skenario"] < ambang["skenario_min"]:
        pesan.append(f"kelulusan skenario {ringkasan['skenario']:.3f} < {ambang['skenario_min']:.3f}")
    return (not pesan), pesan
