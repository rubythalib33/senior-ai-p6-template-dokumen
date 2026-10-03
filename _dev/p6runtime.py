"""Runtime skill Pertemuan 6: katalog SKILL.md, pengungkapan bertahap tiga tingkat, tool dokumen, loop agent, trace.

Tingkat 1  metadata (nama + deskripsi semua skill)      -> selalu ada di prompt sistem
Tingkat 2  badan SKILL.md                                -> masuk konteks saat model memanggil muat_skill
Tingkat 3  berkas rujukan / skrip                        -> rujukan dibaca lewat baca_rujukan; skrip DIJALANKAN, kodenya
                                                            tidak pernah masuk konteks
Tool dokumen milik skill (allowed-tools) baru aktif setelah skill dimuat.

Tiga mode untuk eksperimen:
  skill  : pengungkapan bertahap (desain yang diajarkan)
  semua  : semua SKILL.md + seluruh rujukan dimasukkan ke prompt sistem, semua tool aktif sejak awal
  tanpa  : tidak ada pengetahuan SOP; tool dokumen aktif dan model mengisi sendiri nilai administratif
"""
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

import requests

LLM_URL = "http://127.0.0.1:8000/v1/chat/completions"
LLM_MODEL = "qwen"
REPO = os.environ.get("P6_REPO", "template_dokumen")
HARI_INI = "2026-10-05"
sys.path.insert(0, REPO)
from render import NAMA_TEMPLATE, render, rupiah, skema, tanggal_id, terbilang_rupiah, validasi  # noqa: E402


# ======================================================================== katalog skill
class Skill:
    def __init__(self, nama, deskripsi, alat, folder, badan, rujukan, skrip, meta):
        self.nama, self.deskripsi, self.alat, self.folder = nama, deskripsi, alat, folder
        self.badan, self.rujukan, self.skrip, self.meta = badan, rujukan, skrip, meta

    def __repr__(self):
        return f"Skill({self.nama}, alat={self.alat}, rujukan={len(self.rujukan)}, skrip={len(self.skrip)})"


def baca_skill(folder):
    teks = open(os.path.join(folder, "SKILL.md"), encoding="utf8").read().replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", teks, re.S)
    if not m:
        raise ValueError(f"{folder}/SKILL.md tidak diawali frontmatter YAML (--- ... ---)")
    meta = {}
    for baris in m.group(1).splitlines():
        if ":" in baris:
            k, v = baris.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    daftar = lambda sub: sorted(f"{sub}/{f}" for f in os.listdir(os.path.join(folder, sub))) \
        if os.path.isdir(os.path.join(folder, sub)) else []
    return Skill(meta.get("name", ""), meta.get("description", ""), meta.get("allowed-tools", "").replace(",", " ").split(),
                 folder, m.group(2).strip(), daftar("rujukan"), daftar("skrip"), meta)


def muat_katalog(folder=None, ganti=None, deskripsi=None):
    """Baca semua skill di `folder`. ganti = {nama: folder_varian}; deskripsi = {nama: deskripsi pengganti}."""
    folder = folder or os.path.join(REPO, "skills")
    katalog = {}
    for d in sorted(os.listdir(folder)):
        p = os.path.join(folder, d)
        if d.startswith(("_", ".")) or not os.path.exists(os.path.join(p, "SKILL.md")):
            continue
        s = baca_skill((ganti or {}).get(d, p))
        if deskripsi and s.nama in deskripsi:
            s.deskripsi = deskripsi[s.nama]
        katalog[s.nama] = s
    return katalog


def periksa_skill(s):
    """Aturan struktur skill (spesifikasi Agent Skills + aturan seri). Kembalikan daftar masalah."""
    masalah = []
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s.nama) or len(s.nama) > 64:
        masalah.append("name harus huruf kecil/angka/tanda hubung, maks 64 karakter")
    if s.nama != os.path.basename(os.path.normpath(s.folder)):
        masalah.append(f"name '{s.nama}' harus sama dengan nama folder")
    if not 1 <= len(s.deskripsi) <= 1024:
        masalah.append(f"description harus 1–1024 karakter (sekarang {len(s.deskripsi)})")
    if not re.search(r"\b(ketika|saat|bila|jika|untuk)\b", s.deskripsi, re.I):
        masalah.append("description sebaiknya menyebut KAPAN skill dipakai (ketika/saat/bila ...)")
    if not re.search(r"\bbukan\b", s.deskripsi, re.I):
        masalah.append("description sebaiknya menyebut batas: kapan skill TIDAK dipakai ('Bukan untuk ...')")
    if s.badan.count("\n") + 1 > 500:
        masalah.append("badan SKILL.md lebih dari 500 baris; pindahkan detail ke rujukan/")
    for r in re.findall(r"`(rujukan/[^`]+)`", s.badan):
        if r not in s.rujukan:
            masalah.append(f"badan menyebut {r} tetapi berkasnya tidak ada")
    for r in s.rujukan:
        if r.count("/") > 1:
            masalah.append(f"{r}: rujukan hanya boleh satu tingkat di bawah folder skill")
    for a in s.alat:
        if a.removeprefix("isi_") not in NAMA_TEMPLATE:
            masalah.append(f"allowed-tools '{a}' tidak dikenal")
    return masalah


_cache_token = {}


def hitung_token(teks):
    """Jumlah token menurut tokenizer model yang sedang dilayani vLLM (endpoint /tokenize)."""
    if teks not in _cache_token:
        r = requests.post(LLM_URL.replace("/v1/chat/completions", "/tokenize"),
                          json={"model": LLM_MODEL, "prompt": teks}, timeout=60)
        _cache_token[teks] = r.json()["count"]
    return _cache_token[teks]


# ======================================================================== panggilan LLM
class Meter:
    def __init__(self):
        self.llm, self.masuk, self.keluar, self.detik = 0, 0, 0, 0.0

    def tambah(self, usage, detik):
        self.llm += 1
        self.masuk += usage.get("prompt_tokens", 0)
        self.keluar += usage.get("completion_tokens", 0)
        self.detik += detik


def chat(pesan, tools=None, tool_choice="auto", maks=1500, suhu=0.0, meter=None):
    body = {"model": LLM_MODEL, "messages": pesan, "max_tokens": maks, "temperature": suhu,
            "chat_template_kwargs": {"enable_thinking": False}}
    if suhu > 0:
        body.update(top_p=0.8, top_k=20)
    if tools:
        body.update(tools=tools, tool_choice=tool_choice)
    for coba in range(3):
        try:
            t0 = time.time()
            r = requests.post(LLM_URL, json=body, timeout=600)
            r.raise_for_status()
            break
        except requests.RequestException:
            if coba == 2:
                raise
            time.sleep(5)
    d = r.json()
    if meter is not None:
        meter.tambah(d.get("usage", {}), time.time() - t0)
    return d["choices"][0]["message"]


# ======================================================================== prompt sistem
KEPALA = ("Anda adalah asisten back-office PT Arunika Data Nusantara (perusahaan fiktif untuk pelatihan). "
          "Hari ini {hari}. Jawab dalam Bahasa Indonesia yang sopan dan ringkas.")
ATURAN_SKILL = """Anda memiliki skill berikut (nama: kapan dipakai):
{daftar}

Cara kerja:
1. Bila permintaan pengguna termasuk wilayah salah satu skill, panggil muat_skill dengan nama skill itu SEBELUM menjawab atau membuat dokumen. Muat hanya skill yang relevan.
2. Ikuti instruksi skill yang dimuat. Baca berkas rujukan dengan baca_rujukan bila instruksi menyuruh atau Anda butuh aturan rinci.
3. Bila tidak ada skill yang cocok, jangan memuat skill; jawab langsung dengan singkat atau katakan permintaan itu di luar kemampuan asisten ini.
4. Jangan mengarang data pengguna (nama, harga, tanggal). Tanyakan bila kurang.
5. Anda tidak bisa mengirim email, menjadwalkan rapat, menyetujui dokumen, atau mengakses sistem lain."""
ATURAN_SEMUA = """Berikut seluruh prosedur dan SOP yang berlaku. Gunakan tool dokumen yang sesuai bila pengguna meminta dokumen; nilai yang dihitung sistem tidak perlu Anda isi. Jangan mengarang data pengguna; tanyakan bila kurang. Anda tidak bisa mengirim email, menjadwalkan rapat, menyetujui dokumen, atau mengakses sistem lain.

{isi}"""
ATURAN_TANPA = """Bila pengguna meminta dokumen, gunakan tool dokumen yang sesuai dan isi semua field, termasuk nomor dan nilai administratif, sebaik mungkin. Jangan mengarang data pengguna; tanyakan bila kurang. Anda tidak bisa mengirim email, menjadwalkan rapat, menyetujui dokumen, atau mengakses sistem lain."""


def prompt_sistem(katalog, mode="skill", hari_ini=HARI_INI):
    kepala = KEPALA.format(hari=tanggal_id(hari_ini, hari=True))
    if mode == "skill":
        daftar = "\n".join(f"- {s.nama}: {s.deskripsi}" for s in katalog.values())
        return kepala + "\n\n" + ATURAN_SKILL.format(daftar=daftar)
    if mode == "semua":
        bagian = []
        for s in katalog.values():
            bagian.append(f"## Skill {s.nama}\n{s.badan}")
            for r in s.rujukan:
                bagian.append(f"### {s.nama}/{r}\n" + open(os.path.join(s.folder, r), encoding="utf8").read())
        return kepala + "\n\n" + ATURAN_SEMUA.format(isi="\n\n".join(bagian))
    return kepala + "\n\n" + ATURAN_TANPA


# ======================================================================== definisi tool
def tool_muat(katalog):
    return {"type": "function", "function": {
        "name": "muat_skill",
        "description": "Memuat instruksi lengkap satu skill. Panggil sebelum mengerjakan tugas yang termasuk wilayah skill itu.",
        "parameters": {"type": "object", "properties": {"nama": {"type": "string", "enum": list(katalog)}},
                       "required": ["nama"]}}}


def tool_baca(katalog):
    return {"type": "function", "function": {
        "name": "baca_rujukan",
        "description": "Membaca satu berkas rujukan milik skill yang sudah dimuat, mis. rujukan/sop-pengadaan.md.",
        "parameters": {"type": "object", "properties": {
            "skill": {"type": "string", "enum": list(katalog)},
            "berkas": {"type": "string", "description": "Path berkas di dalam folder skill, mis. rujukan/sop-pengadaan.md"}},
            "required": ["skill", "berkas"]}}}


# Field tambahan yang harus diisi MODEL bila tidak ada skrip SOP (mode 'tanpa' dan varian naratif/pseudokode).
SKEMA_TAMBAHAN = {
    "memo_pengadaan": ({"nomor": {"type": "string", "description": "Nomor memo sesuai aturan penomoran."},
                        "metode_pengadaan": {"type": "string", "enum": ["Pembelian langsung", "Pengadaan langsung",
                                                                        "Pemilihan langsung", "Tender", "Seleksi"]},
                        "min_penawaran": {"type": "integer", "minimum": 1, "maximum": 5},
                        "persetujuan": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"},
                                        "description": "Jabatan penyetuju berurutan."},
                        "ppn_persen": {"type": "integer", "minimum": 0, "maximum": 20}},
                       ["nomor", "metode_pengadaan", "min_penawaran", "persetujuan", "ppn_persen"]),
    "sppd": ({"nomor": {"type": "string"}, "pemberi_tugas": {"type": "string", "description": "Jabatan pemberi tugas."},
              "uang_harian_per_hari": {"type": "integer", "minimum": 0}, "penginapan_per_malam": {"type": "integer", "minimum": 0},
              "transport_lokal_per_hari": {"type": "integer", "minimum": 0}, "tiket_pp": {"type": "integer", "minimum": 0}},
             ["nomor", "pemberi_tugas", "uang_harian_per_hari", "penginapan_per_malam", "transport_lokal_per_hari", "tiket_pp"]),
    "nota_dinas": ({"nomor": {"type": "string"}}, ["nomor"]),
    "notulen_rapat": ({"nomor": {"type": "string"}}, ["nomor"]),
    "laporan_insiden": ({"nomor": {"type": "string"}, "severity": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                         "jabatan_penanggung_jawab": {"type": "string"}, "target_pemulihan": {"type": "string"}},
                        ["nomor", "severity", "jabatan_penanggung_jawab", "target_pemulihan"]),
    "surat_penawaran": ({"nomor": {"type": "string"}, "ppn_persen": {"type": "integer", "minimum": 0, "maximum": 20}},
                        ["nomor", "ppn_persen"]),
}


def skema_tool(template, tambahan=False):
    t = copy.deepcopy(skema(template)["tool"])
    if tambahan:
        props, wajib = SKEMA_TAMBAHAN[template]
        p = t["function"]["parameters"]
        p["properties"].update(copy.deepcopy(props))
        p["required"] = p["required"] + wajib
        t["function"]["description"] = (t["function"]["description"].split(" Nomor dokumen")[0]
                                        + " Anda juga harus mengisi nomor dokumen dan nilai administratif sesuai aturan perusahaan.")
    return t


# ======================================================================== field program
def _angka(s):
    return int(str(s).replace(".", "").replace(",", "") or 0)


def jalankan_skrip(skill, argumen, hari_ini, register):
    """Jalankan skrip/hitung.py milik skill sebagai proses terpisah (tingkat 3: kode tidak masuk konteks)."""
    p = os.path.join(skill.folder, "skrip", "hitung.py")
    masuk = json.dumps({"argumen": argumen, "hari_ini": hari_ini, "register": register}, ensure_ascii=False).encode("utf8")
    try:
        r = subprocess.run([sys.executable, p], input=masuk, capture_output=True, timeout=60)
        return json.loads(r.stdout.decode("utf8"))
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"ok": False, "galat": f"skrip {skill.nama} gagal dijalankan ({type(e).__name__})"}


def program_dari_model(template, a, hari_ini):
    """Mode tanpa skrip: nilai administratif dari model; program hanya merapikan aritmetika dan format."""
    from datetime import datetime
    pr = {"nomor": a.get("nomor") or "-", "tanggal": tanggal_id(hari_ini), "peringatan": []}

    def harga(items, ppn_persen):
        out, sub = [], 0
        for i, it in enumerate(items, 1):
            j = it["jumlah"] * it["harga_satuan"]
            sub += j
            out.append(dict(it, no=i, harga_satuan=rupiah(it["harga_satuan"]), jumlah_harga=rupiah(j)))
        ppn = round(sub * ppn_persen / 100)
        return out, {"subtotal": rupiah(sub), "ppn_persen": ppn_persen, "ppn": rupiah(ppn), "total": rupiah(sub + ppn),
                     "total_terbilang": terbilang_rupiah(sub + ppn)}

    if template in ("memo_pengadaan", "surat_penawaran"):
        items, angka = harga(a["items"], a.get("ppn_persen", 0))
        pr.update(angka, items=items)
    if template == "memo_pengadaan":
        pr.update(kepada="-", metode_pengadaan=a.get("metode_pengadaan", "-"), min_penawaran=a.get("min_penawaran", 0),
                  dasar_metode="-", lampiran=[], kebutuhan_tanggal=tanggal_id(a["kebutuhan_tanggal"]),
                  persetujuan=[{"tingkat": str(i), "jabatan": j} for i, j in enumerate(a.get("persetujuan", []), 1)])
    elif template == "sppd":
        pergi = datetime.strptime(a["tanggal_berangkat"], "%Y-%m-%d")
        pulang = datetime.strptime(a["tanggal_kembali"], "%Y-%m-%d")
        hari = max((pulang - pergi).days + 1, 1)
        rows = [("Uang harian", hari, "hari", a.get("uang_harian_per_hari", 0)),
                ("Penginapan", hari - 1, "malam", a.get("penginapan_per_malam", 0)),
                ("Tiket pergi-pulang", 1, "paket", a.get("tiket_pp", 0)),
                ("Transportasi lokal", hari, "hari", a.get("transport_lokal_per_hari", 0))]
        biaya, total = [], 0
        for i, (k, v, s, t) in enumerate(rows, 1):
            total += v * t
            biaya.append({"no": i, "komponen": k, "volume": v, "satuan": s, "tarif": rupiah(t), "jumlah": rupiah(v * t)})
        pr.update(pemberi_tugas=a.get("pemberi_tugas", "-"), nama_pemberi_tugas="-", kota_asal="Jakarta", lama_hari=hari,
                  lama_malam=hari - 1, biaya=biaya, total=rupiah(total), total_terbilang=terbilang_rupiah(total),
                  ketentuan=[], tanggal_berangkat=tanggal_id(pergi, hari=True), tanggal_kembali=tanggal_id(pulang, hari=True))
    elif template == "nota_dinas":
        pr.update(tembusan_teks=", ".join(a.get("tembusan", [])) or "-")
    elif template == "notulen_rapat":
        pr.update(tanggal_rapat=tanggal_id(a["tanggal_rapat"], hari=True),
                  pembahasan=[dict(p, no=i) for i, p in enumerate(a["pembahasan"], 1)],
                  tindak_lanjut=[{"no": i, "tugas": t["tugas"], "pic": t["pic"] or "–", "tenggat": t["tenggat"] or "–",
                                  "catatan": ""} for i, t in enumerate(a["tindak_lanjut"], 1)])
    elif template == "laporan_insiden":
        sev = a.get("severity", "P4")
        pr.update(severity=sev, severity_label=f"{sev} — target pemulihan {a.get('target_pemulihan', '-')}",
                  sev_warna={"P1": "B91C1C", "P2": "D97706", "P3": "CA8A04"}.get(sev, "2563EB"),
                  status="Pulih" if a.get("waktu_pulih") else "Berlangsung", durasi="-",
                  jabatan_penanggung_jawab=a.get("jabatan_penanggung_jawab", "-"),
                  waktu_mulai=a["waktu_mulai"], waktu_terdeteksi=a["waktu_terdeteksi"], waktu_pulih=a.get("waktu_pulih") or "-",
                  linimasa=a["linimasa"], tindak_lanjut=[dict(t, no=i) for i, t in enumerate(a["tindak_lanjut"], 1)])
    elif template == "surat_penawaran":
        pr.update(lampiran="-", ketentuan=[f"Penawaran berlaku {a['masa_berlaku_hari']} hari.",
                                           f"Syarat pembayaran: {a['syarat_pembayaran']}."])
    return pr


def nilai_dinilai(template, program, argumen):
    """Nilai administratif yang dinilai golden set, dari skrip SOP (mode skill) atau dari model (mode tanpa skrip)."""
    n = {"nomor": program.get("nomor")}
    if template == "memo_pengadaan":
        n.update(metode=program.get("metode_pengadaan"), min_penawaran=program.get("min_penawaran"),
                 persetujuan=[p["jabatan"] for p in program.get("persetujuan", [])], ppn_persen=program.get("ppn_persen"))
    elif template == "sppd":
        baris = {b["komponen"].split(" ")[0]: _angka(b["tarif"]) for b in program.get("biaya", [])}
        n.update(pemberi_tugas=program.get("pemberi_tugas"), uang_harian=baris.get("Uang", 0),
                 penginapan=baris.get("Penginapan", 0), total=_angka(program.get("total", 0)))
    elif template == "laporan_insiden":
        n.update(severity=program.get("severity"), penanggung_jawab=program.get("jabatan_penanggung_jawab"))
    elif template == "surat_penawaran":
        n.update(penandatangan=program.get("jabatan_penandatangan") or argumen.get("jabatan_penandatangan"),
                 total=_angka(program.get("total", 0)))
    return n


# ======================================================================== sesi & loop agent
class Sesi:
    def __init__(self, katalog, mode="skill", hari_ini=HARI_INI, keluar="hasil_dokumen", suhu=0.0, maks_giliran=8):
        self.katalog, self.mode, self.hari_ini, self.keluar = katalog, mode, hari_ini, keluar
        self.suhu, self.maks_giliran = suhu, maks_giliran
        self.dimuat, self.dibaca, self.dokumen, self.trace = [], [], [], []
        self.meter, self.jawaban, self.giliran, self.t0 = Meter(), "", 0, time.time()
        self.register = os.path.join(tempfile.gettempdir(), f"register_{uuid.uuid4().hex[:8]}.json")

    def _catat(self, jenis, **isi):
        self.trace.append(dict(t=round(time.time() - self.t0, 1), jenis=jenis, **isi))

    def pemilik_tool(self, nama_tool):
        for s in self.katalog.values():
            if nama_tool in s.alat:
                return s
        return None

    def tools(self):
        if self.mode == "skill":
            ts = [tool_muat(self.katalog), tool_baca(self.katalog)]
            for n in self.dimuat:
                s = self.katalog[n]
                for a in s.alat:
                    ts.append(skema_tool(a.removeprefix("isi_"), tambahan=not s.skrip))
            return ts
        return [skema_tool(t, tambahan=(self.mode == "tanpa")) for t in NAMA_TEMPLATE]

    def eksekusi(self, nama, a):
        if nama == "muat_skill":
            s = self.katalog.get(a.get("nama"))
            if not s:
                return {"galat": f"skill '{a.get('nama')}' tidak ada; pilihan: {list(self.katalog)}"}
            if s.nama not in self.dimuat:
                self.dimuat.append(s.nama)
            return {"skill": s.nama, "instruksi": s.badan, "berkas_rujukan": s.rujukan,
                    "tool_aktif": s.alat or ["(tidak ada — skill ini hanya untuk menjawab)"]}
        if nama == "baca_rujukan":
            s = self.katalog.get(a.get("skill"))
            if not s:
                return {"galat": f"skill '{a.get('skill')}' tidak ada"}
            if self.mode == "skill" and s.nama not in self.dimuat:
                return {"galat": f"muat skill '{s.nama}' dulu dengan muat_skill"}
            berkas = a.get("berkas", "")
            cocok = [r for r in s.rujukan if r == berkas or r.endswith("/" + berkas.split("/")[-1])]
            if not cocok:
                return {"galat": f"berkas '{berkas}' tidak ada; pilihan: {s.rujukan}"}
            self.dibaca.append(f"{s.nama}/{cocok[0]}")
            return {"berkas": cocok[0], "isi": open(os.path.join(s.folder, cocok[0]), encoding="utf8").read()}
        if nama.startswith("isi_") and nama.removeprefix("isi_") in NAMA_TEMPLATE:
            return self._dokumen(nama.removeprefix("isi_"), a)
        return {"galat": f"tool '{nama}' tidak tersedia"}

    def _dokumen(self, template, a):
        pakai_skrip = self.mode != "tanpa"
        s = self.pemilik_tool("isi_" + template)
        if self.mode == "skill":
            if not s or s.nama not in self.dimuat:
                return {"status": "ditolak", "galat": ["muat skill pemilik tool ini dulu"]}
            pakai_skrip = bool(s.skrip)
        # validasi skema (field LLM + field tambahan bila tanpa skrip)
        import jsonschema
        params = skema_tool(template, tambahan=not pakai_skrip)["function"]["parameters"]
        galat = [f"{'.'.join(map(str, e.absolute_path)) or '(akar)'}: {e.message}"
                 for e in jsonschema.Draft202012Validator(params).iter_errors(a)]
        if galat:
            return {"status": "ditolak", "galat": galat[:8], "petunjuk": "perbaiki argumen lalu panggil tool ini lagi"}
        if pakai_skrip:
            h = jalankan_skrip(s, a, self.hari_ini, self.register)
            if not h.get("ok"):
                return {"status": "ditolak", "galat": [h.get("galat", "skrip gagal")],
                        "petunjuk": "perbaiki argumen atau tanyakan ke pengguna"}
            program, ringkasan, peringatan = h["program"], h["ringkasan"], h.get("peringatan", [])
        else:
            program, ringkasan, peringatan = program_dari_model(template, a, self.hari_ini), "Dokumen dibuat.", []
        os.makedirs(self.keluar, exist_ok=True)
        berkas = os.path.join(self.keluar, re.sub(r"[^A-Za-z0-9]+", "_", str(program.get("nomor", template))) + ".docx")
        try:
            render(template, {**a, **program}, berkas)
        except Exception as e:  # galat render dikembalikan ke model, bukan menghentikan agent
            return {"status": "ditolak", "galat": [f"render gagal: {e}"]}
        self.dokumen.append({"template": template, "berkas": berkas, "argumen": a, "program": program,
                             "nilai": nilai_dinilai(template, program, a), "peringatan": peringatan})
        return {"status": "dibuat", "berkas": os.path.basename(berkas), "ringkasan": ringkasan, "peringatan": peringatan}


def jalankan_agent(permintaan, katalog, mode="skill", riwayat=None, **kw):
    """Satu permintaan pengguna -> loop LLM + tool sampai model menjawab tanpa tool (atau anggaran giliran habis)."""
    sesi = Sesi(katalog, mode, **kw)
    pesan = [{"role": "system", "content": prompt_sistem(katalog, mode, sesi.hari_ini)}] + list(riwayat or []) \
        + [{"role": "user", "content": permintaan}]
    for g in range(sesi.maks_giliran):
        sesi.giliran = g + 1
        msg = chat(pesan, tools=sesi.tools(), suhu=sesi.suhu, meter=sesi.meter)
        panggilan = msg.get("tool_calls") or []
        sesi._catat("llm", giliran=g + 1, tool=[c["function"]["name"] for c in panggilan],
                    token_masuk=sesi.meter.masuk, token_keluar=sesi.meter.keluar)
        if not panggilan:
            sesi.jawaban = (msg.get("content") or "").strip()
            pesan.append({"role": "assistant", "content": sesi.jawaban})
            break
        pesan.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": panggilan})
        for c in panggilan:
            nama = c["function"]["name"]
            try:
                a = json.loads(c["function"].get("arguments") or "{}")
                hasil = sesi.eksekusi(nama, a) if isinstance(a, dict) else {"galat": "argumen harus objek JSON"}
            except json.JSONDecodeError as e:
                a, hasil = {}, {"galat": f"argumen bukan JSON valid: {e}"}
            sesi._catat("tool", nama=nama, argumen=a, hasil={k: v for k, v in hasil.items() if k != "isi" and k != "instruksi"})
            pesan.append({"role": "tool", "tool_call_id": c.get("id", nama), "content": json.dumps(hasil, ensure_ascii=False)})
    else:
        sesi.jawaban = "(anggaran giliran habis)"
    sesi.pesan = pesan
    return sesi


def cetak_trace(sesi):
    """Tampilkan jejak satu sesi: kapan skill dimuat, rujukan dibaca, tool dipanggil, dan hasilnya."""
    for t in sesi.trace:
        if t["jenis"] == "llm":
            arah = ", ".join(t["tool"]) if t["tool"] else "jawaban akhir"
            print(f"{t['t']:6.1f}s  LLM   giliran {t['giliran']} -> {arah}   (token masuk kumulatif {t['token_masuk']:,})")
        else:
            a = {k: (v if len(str(v)) < 60 else str(v)[:57] + "...") for k, v in t["argumen"].items()}
            h = t["hasil"]
            ringkas = h.get("ringkasan") or h.get("galat") or h.get("berkas") or h.get("skill") or ""
            print(f"{t['t']:6.1f}s  TOOL  {t['nama']}({', '.join(f'{k}={v}' for k, v in a.items())})")
            print(f"{'':14}-> {str(ringkas)[:300]}")
            for p in h.get("peringatan", []):
                print(f"{'':14}   ! {p[:200]}")
    print(f"\nJawaban: {sesi.jawaban}")
    print(f"Skill dimuat: {sesi.dimuat} · rujukan dibaca: {sesi.dibaca} · dokumen: {[d['berkas'] for d in sesi.dokumen]}")
    print(f"LLM {sesi.meter.llm}x · token masuk {sesi.meter.masuk:,} · keluar {sesi.meter.keluar:,} · {sesi.meter.detik:.1f} s")


def pratinjau(berkas_docx, halaman=1, dpi=70):
    """Render halaman dokumen .docx ke PNG (LibreOffice -> PDF -> PyMuPDF) untuk ditampilkan di notebook."""
    import shutil
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice belum terpasang (sel 0.3 memasangnya di latar)")
    folder = os.path.dirname(os.path.abspath(berkas_docx))
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", folder, berkas_docx],
                   check=True, capture_output=True, timeout=180)
    import pymupdf
    doc = pymupdf.open(os.path.splitext(os.path.abspath(berkas_docx))[0] + ".pdf")
    png = os.path.splitext(os.path.abspath(berkas_docx))[0] + f"-{halaman}.png"
    doc[halaman - 1].get_pixmap(dpi=dpi).save(png)
    return png


def picu(permintaan, katalog, hari_ini=HARI_INI):
    """Uji pemicuan: skill apa yang dimuat model PERTAMA KALI untuk permintaan ini (None = tidak memuat skill)."""
    msg = chat([{"role": "system", "content": prompt_sistem(katalog, "skill", hari_ini)},
                {"role": "user", "content": permintaan}], tools=[tool_muat(katalog), tool_baca(katalog)], maks=300)
    for c in msg.get("tool_calls") or []:
        try:
            a = json.loads(c["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            continue
        if c["function"]["name"] == "muat_skill":
            return a.get("nama")
        if c["function"]["name"] == "baca_rujukan":
            return a.get("skill")
    return None
