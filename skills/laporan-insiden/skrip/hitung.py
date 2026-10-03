"""Hitung field program laporan insiden sesuai SOP-INS-05 (severity dari matriks, status, durasi, penanggung jawab)."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_bersama"))
from arunika import jalankan, ke_tanggal, muat_data, nomor_baru, tanggal_id  # noqa: E402

S = muat_data(__file__, "severity.json")
_URUT = ["P1", "P2", "P3", "P4"]


def waktu(x, nama):
    try:
        return datetime.strptime(x, "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        raise ValueError(f"{nama} {x!r} tidak valid; gunakan format YYYY-MM-DD HH:MM")


def lama(menit):
    j, m = divmod(int(menit), 60)
    h, j = divmod(j, 24)
    bagian = [f"{h} hari" if h else "", f"{j} jam" if j else "", f"{m} menit" if m else ""]
    return " ".join(b for b in bagian if b) or "kurang dari 1 menit"


def hitung(a, hari_ini, register):
    mulai, deteksi = waktu(a["waktu_mulai"], "waktu_mulai"), waktu(a["waktu_terdeteksi"], "waktu_terdeteksi")
    pulih = waktu(a["waktu_pulih"], "waktu_pulih") if (a.get("waktu_pulih") or "").strip() else None
    if deteksi < mulai:
        raise ValueError("waktu_terdeteksi lebih awal dari waktu_mulai; periksa linimasa ke pengguna")
    if pulih and pulih < mulai:
        raise ValueError("waktu_pulih lebih awal dari waktu_mulai; periksa linimasa ke pengguna")
    sev = S["matriks"][a["urgensi"]][a["dampak"]]
    peringatan = []
    teks = " ".join([a["judul"], a["ringkasan"], a["dampak_uraian"]]).lower()
    if any(k in teks for k in S["kata_kebocoran"]) and _URUT.index(sev) > 1:
        peringatan.append(f"Ada indikasi insiden keamanan/kebocoran data; severity dinaikkan dari {sev} ke P2 "
                          "(SOP-INS-05 Pasal 7). Beri tahu Petugas Pelindungan Data paling lambat 1 x 24 jam.")
        sev = "P2"
    info = S["severity"][sev]
    if sev in ("P1", "P2"):
        peringatan.append(f"Insiden {sev} wajib postmortem tertulis paling lambat 5 hari kerja setelah pulih (Pasal 6 ayat 3).")
    for i, t in enumerate(a["tindak_lanjut"], 1):
        if not (t.get("pic") or "").strip() or not (t.get("tenggat") or "").strip():
            peringatan.append(f"Tindak lanjut no. {i} belum lengkap PIC/tenggatnya (Pasal 6 ayat 2).")
    selesai = pulih or datetime.combine(ke_tanggal(hari_ini), datetime.max.time()).replace(second=0, microsecond=0)
    durasi = lama((selesai - mulai).total_seconds() // 60) if pulih else "masih berlangsung"
    nomor = nomor_baru("INS/TI", register, hari_ini)
    program = {"nomor": nomor, "tanggal": tanggal_id(hari_ini), "severity": sev,
               "severity_label": f"{sev} · {info['nama']} — target pemulihan {info['target']}", "sev_warna": info["warna"],
               "status": "Pulih" if pulih else "Berlangsung", "durasi": durasi,
               "jabatan_penanggung_jawab": info["penanggung_jawab"],
               "waktu_mulai": tanggal_id(mulai, jam=True), "waktu_terdeteksi": tanggal_id(deteksi, jam=True),
               "waktu_pulih": tanggal_id(pulih, jam=True) if pulih else "Belum pulih",
               "linimasa": [{"waktu": (l["waktu"][11:] + " WIB") if l["waktu"][:10] == a["waktu_mulai"][:10]
                             else tanggal_id(l["waktu"], jam=True), "kejadian": l["kejadian"]} for l in a["linimasa"]],
               "tindak_lanjut": [{"no": i, "tugas": t["tugas"], "pic": (t.get("pic") or "").strip() or "–",
                                  "tenggat": tanggal_id(t["tenggat"]) if (t.get("tenggat") or "").strip() else "–"}
                                 for i, t in enumerate(a["tindak_lanjut"], 1)],
               "peringatan": peringatan}
    ringkasan = (f"Laporan {nomor}: severity {sev} ({info['nama']}, target pemulihan {info['target']}), "
                 f"status {program['status'].lower()}, durasi {durasi}, penanggung jawab {info['penanggung_jawab']}.")
    return {"program": program, "ringkasan": ringkasan, "peringatan": peringatan}


if __name__ == "__main__":
    jalankan(hitung)
