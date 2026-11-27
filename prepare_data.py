"""Membangun file data dashboard dari empat file hasil analisis.

Letakkan file sumber di folder sumber/ lalu jalankan:  python prepare_data.py

  sumber/Analitika_Data_Bersih_ISPU_Meteorologi_Clustering_PCA_REVISI.xlsx   (dataset + clustering)
  sumber/KLASIFIKASI.jasp                                                     (klasifikasi, JASP)
  sumber/kausalitass_jasp_jasp.zip                                            (regresi, JASP)
  sumber/Analtika_Data_korelasi_kausalitas.twbx                               (korelasi, Tableau; hanya dicek strukturnya)

Tidak ada angka yang dibuat sendiri: tabel JASP dan sheet Excel disalin apa adanya.
Satu pengecualian yang dijelaskan di dashboard: tabel korelasi Pearson di dalam ekstrak
Tableau (.hyper) terkompresi dan tidak bisa dibaca tanpa Tableau, jadi koefisien Pearson
dihitung ulang dari dataset yang sama (Merged_Dataset_Utama) dengan struktur yang sama
(variabel_x, variabel_y, korelasi_pearson, n_pasangan).
"""
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from scipy import stats

SUMBER = Path("sumber")
OUT = Path("data")
F_EXCEL = next(SUMBER.glob("Analitika_Data_Bersih_ISPU_Meteorologi_Clustering_PCA_REVISI*.xlsx"))
F_KLAS = SUMBER / "KLASIFIKASI.jasp"
F_REG = next(SUMBER.glob("kausalitas*jasp*.zip"))
OUT.mkdir(exist_ok=True)

CUACA = ["suhu_rata2", "kelembaban_rata2", "kecepatan_angin_rata2", "curah_hujan_total", "radiasi_matahari_rata2"]
VAR_KORELASI = CUACA + ["nilai_ispu"]
NAMA_STASIUN = {"DKI1": "DKI1 Bundaran HI", "DKI2": "DKI2 Kelapa Gading", "DKI3": "DKI3 Jagakarsa",
                "DKI4": "DKI4 Lubang Buaya", "DKI5": "DKI5 Kebun Jeruk"}


def simpan_json(obj, nama):
    with open(OUT / nama, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("ditulis:", OUT / nama)


def bersih(v):
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    return v


# ------------------------------------------------------------------ 1. dataset
def buat_dataset():
    d = pd.read_excel(F_EXCEL, sheet_name="Merged_Dataset_Utama")
    d["tanggal"] = pd.to_datetime(d["tanggal"]).dt.date
    d.to_csv(OUT / "dataset_harian.csv", index=False)
    print("dataset_harian.csv:", d.shape)
    return d


# ------------------------------------------------------------------ 2. korelasi (Pearson)
def buat_korelasi(d):
    baris = []
    for x in VAR_KORELASI:
        for y in VAR_KORELASI:
            s = d[[x, y]].dropna()
            r, p = stats.pearsonr(s[x], s[y]) if x != y else (1.0, 0.0)
            baris.append(dict(variabel_x=x, variabel_y=y, korelasi_pearson=r, p_value=p, n_pasangan=len(s)))
    pd.DataFrame(baris).to_csv(OUT / "korelasi_pearson.csv", index=False)
    print("korelasi_pearson.csv:", len(baris), "baris")


# ------------------------------------------------------------------ 3. regresi JASP
def buat_regresi(d):
    with zipfile.ZipFile(F_REG) as z:
        an = json.loads(z.read("analyses.json"))["analyses"][0]
        hasil = json.loads(z.read("resources/0/jaspResults.json"))
    mc = hasil["data"]["modelContainer"]["data"]
    # urutan variabel di Model 1 (JASP menyandikan nama kolom, urutan footnote = urutan modelTerms)
    urut = [c[0] for c in an["options"]["modelTerms"][1]["components"]["value"]]
    ringkas = mc["summaryTable"]["data"]
    ikol = {n: i for i, n in enumerate(mc["summaryTable"]["colNames"]["rows"])} if isinstance(mc["summaryTable"]["colNames"], dict) else None
    sm = dict(zip(mc["summaryTable"]["colNames"]["rows"], ringkas))
    an_t = dict(zip(mc["anovaTable"]["colNames"]["rows"], mc["anovaTable"]["data"]))
    co_t = dict(zip(mc["coeffTable"]["colNames"]["rows"], mc["coeffTable"]["data"]))
    de_t = dict(zip(mc["descriptivesTable"]["colNames"]["rows"], mc["descriptivesTable"]["data"]))

    # koefisien Model 1: indeks 1 = intercept M1, 2.. = prediktor sesuai `urut`
    koef = []
    for i, nama in enumerate(["(Intercept)"] + urut):
        j = i + 1
        koef.append(dict(variabel=nama, B=co_t["unstandCoeff"][j], SE=co_t["SE"][j], beta=co_t["standCoeff"][j],
                         t=co_t["t"][j], p=co_t["p"][j], ci_bawah=co_t["lower"][j], ci_atas=co_t["upper"][j],
                         tolerance=co_t["tolerance"][j], VIF=co_t["VIF"][j]))
    # verifikasi: hitung ulang OLS dari dataset dan bandingkan dengan JASP
    s = d.dropna(subset=CUACA + ["nilai_ispu"])
    X = np.column_stack([np.ones(len(s))] + [s[c] for c in urut])
    b = np.linalg.lstsq(X, s["nilai_ispu"].astype(float).values, rcond=None)[0]
    assert np.allclose(b, [k["B"] for k in koef], atol=1e-6), "koefisien JASP tidak cocok dengan dataset"
    assert len(s) == sm["df2"][1] + sm["df1"][1] + 1, "jumlah observasi tidak cocok"

    out = dict(
        dependen="nilai_ispu", prediktor=urut, n=len(s),
        ringkasan=dict(R=sm["R"][1], R2=sm["R2"][1], R2_adj=sm["adjR2"][1], RMSE=sm["RMSE"][1],
                       AIC=sm["AIC"][1], BIC=sm["BIC"][1], F=sm["Fc"][1], df1=sm["df1"][1], df2=sm["df2"][1], p=sm["p"][1]),
        anova=[dict(sumber=an_t["cases"][i], SS=an_t["SS"][i], df=an_t["df"][i],
                    MS=(an_t["MS"][i] if i < len(an_t["MS"]) else None),
                    F=(an_t["F"][0] if i == 0 else None), p=(an_t["p"][0] if i == 0 else None)) for i in range(3)],
        koefisien=koef,
        deskriptif=[dict(variabel=n, N=de_t["N"][i], mean=de_t["mean"][i], SD=de_t["SD"][i])
                    for i, n in enumerate(["nilai_ispu"] + urut)],
    )
    simpan_json(out, "hasil_regresi.json")


# ------------------------------------------------------------------ 4. klasifikasi JASP
def buat_klasifikasi():
    with zipfile.ZipFile(F_KLAS) as z:
        an = json.loads(z.read("analyses.json"))["analyses"]
    desk = []
    for r in an[0]["results"]["stats"]["data"]:
        val = lambda k: r[k]["value"] if isinstance(r[k], dict) else r[k]
        desk.append(dict(variabel=r["Variable"], stasiun=NAMA_STASIUN[r["Level"][:4]], valid=r["Valid"],
                         hilang=r["Missing"], mean=r["MeanArithmetic"], sd=r["Std. Deviation"],
                         min=val("Minimum"), maks=val("Maximum")))
    kc = an[1]["results"]["container_stasiun_kategori_hasil"]["collection"]
    ct = kc["container_stasiun_kategori_hasil_crossTabMain"]["data"]
    kat = ["BAIK", "SEDANG", "TIDAK SEHAT", "SANGAT TIDAK SEHAT", "TIDAK DAPAT DIKLASIFIKASI"]
    silang = []
    for r in ct:
        nama = r["stasiun"]
        silang.append(dict(stasiun=NAMA_STASIUN.get(nama[:4], nama), total=r["total[counts]"],
                           jumlah={k: r[f"{k}[counts]"] for k in kat},
                           harapan={k: r[f"{k}[expected]"] for k in kat},
                           persen_baris={k: r[f"{k}[row.proportions]"] * 100 for k in kat}))
    chi = kc["container_stasiun_kategori_hasil_crossTabChisq"]["data"][0]
    nom = kc["container_stasiun_kategori_hasil_crossTabNominal"]["data"][0]
    out = dict(kategori=kat, deskriptif=desk, silang=silang,
               chi2=dict(nilai=chi["value[chiSquared]"], df=chi["df[chiSquared]"], p=chi["p[chiSquared]"], N=chi["value[N]"]),
               cramers_v=nom["value[CramerV]"])
    simpan_json(out, "hasil_klasifikasi.json")


# ------------------------------------------------------------------ 5. clustering (Excel)
def baris_sheet(wb, nama):
    return [list(r) for r in wb[nama].iter_rows(values_only=True)]


def idx(rows, awalan):
    for i, r in enumerate(rows):
        if isinstance(r[0], str) and r[0].startswith(awalan):
            return i
    raise KeyError(awalan)


def blok(rows, awalan, n, kolom, lompat=2):
    i = idx(rows, awalan) + lompat
    return [[bersih(c) for c in r[:kolom]] for r in rows[i:i + n]]


def teks_setelah(rows, awalan_mulai):
    return [r[0] for r in rows[idx(rows, awalan_mulai):] if isinstance(r[0], str)]


def buat_clustering():
    wb = openpyxl.load_workbook(F_EXCEL, data_only=True)
    POL = ["PM10", "PM2.5", "SO2", "CO", "O3", "NO2"]
    P = baris_sheet(wb, "Clustering PCA")
    stas = [r[0] for r in blok(P, "1. Rata-rata", 5, 7)]
    rata = {r[0]: dict(zip(POL, r[1:7])) for r in blok(P, "1. Rata-rata", 5, 7)}
    z2d = {r[0]: dict(zip(POL, r[1:7])) for r in blok(P, "2. Standarisasi", 5, 7)}
    load = {r[0]: dict(zip(POL, r[1:7])) for r in blok(P, "3. Loading", 2, 7)}
    i4 = idx(P, "4. Koordinat")
    koord = {r[0]: dict(PC1=r[1], PC2=r[2]) for r in blok(P, "4. Koordinat", 5, 3)}
    var = P[i4 + 2 + 5]            # Varians komponen
    pers = P[i4 + 2 + 6]           # % varians dijelaskan
    kum = P[i4 + 2 + 7]            # % kumulatif
    i6 = idx(P, "6. Skenario")
    sk = blok(P, "6. Skenario", 5, 9)
    skenario = {r[0]: dict(k2=int(r[3]), k3=int(r[4]), k4=int(r[5])) for r in sk}
    wcss = P[i6 + 2 + 5][6:9]
    sil2d = P[i6 + 2 + 6][6:9]
    profil2d = [dict(klaster=int(r[0]), z=dict(zip(POL, r[1:7])), anggota=r[7]) for r in blok(P, "7. Profil", 3, 8)]
    catatan = [t for t in teks_setelah(P, "8. Interpretasi")[1:]]

    D = baris_sheet(wb, "Dendrogram")
    lang2d = [dict(langkah=r[0], gabung=r[1], n_kiri=r[2], n_kanan=r[3], tinggi=r[10], jarak=r[8], anggota=r[13])
              for r in blok(D, "1. Tahapan", 4, 15)]
    garis2d = [[r[0], r[2], r[3]] for r in blok(D, "3. Koordinat", 16, 4)]
    urut2d = [[r[0], r[1]] for r in blok(D, "2. Urutan", 5, 3)]
    potong2d = {}
    for r in blok(D, "4. Garis potong", 9, 4):
        potong2d.setdefault(r[0], dict(y=r[2], ket=None))
        if r[3]:
            potong2d[r[0]]["ket"] = r[3]

    D6 = baris_sheet(wb, "Dendrogram 6D")
    z6 = {r[0]: dict(zip(POL, r[1:7])) for r in blok(D6, "1. Z-score", 5, 7)}
    lang6 = [dict(langkah=r[0], gabung=r[1], n_kiri=r[2], n_kanan=r[3], jarak=r[4], tinggi=r[6])
             for r in blok(D6, "3. Tahapan", 4, 8)]
    garis6 = [[r[0], r[2], r[3]] for r in blok(D6, "5. Koordinat", 16, 4)]
    urut6 = [[r[0], r[1]] for r in blok(D6, "4. Urutan", 5, 3)]
    potong6 = {}
    i6p = idx(D6, "6. Garis potong")
    for r in D6[i6p + 2:i6p + 2 + 20]:
        if isinstance(r[0], str) and r[0].startswith("potong"):
            potong6.setdefault(r[0], dict(y=bersih(r[2]), ket=None))
            if len(r) > 3 and r[3]:
                potong6[r[0]]["ket"] = r[3]

    C = baris_sheet(wb, "Perbandingan 2D vs 6D")
    anggota = [dict(stasiun=r[0], kmeans2d_k3=int(r[1]), ward2d_k3=int(r[2]), ward6d_k3=int(r[3]), ward6d_k2=int(r[4]))
               for r in blok(C, "2. Keanggotaan", 5, 5)]
    pasangan = [dict(pasangan=r[0], kmeans2d=r[1], ward2d=r[2], ward6d=r[3]) for r in blok(C, "3. Apakah", 4, 4)]
    sil_c = [dict(k=int(r[0]), kmeans2d=r[1], ward6d=r[2]) for r in blok(C, "4. Silhouette", 3, 3)]
    profil6d = [dict(klaster=int(r[0]), z=dict(zip(POL, r[1:7])), anggota=r[7]) for r in blok(C, "5. Profil", 3, 8)]
    kesimpulan = teks_setelah(C, "6. Kesimpulan")[1:]
    tinggi_cmp = [dict(langkah=r[0], gabung2d=r[1], tinggi2d=r[2], gabung6d=r[3], tinggi6d=r[4], tinggi6d_setara=r[5])
                  for r in blok(C, "1. Urutan", 4, 6)]

    out = dict(polutan=POL, stasiun=stas, rata_rata=rata, z_score_sampel=z2d, loading=load, koordinat=koord,
               varians=dict(nilai=var[1:3], persen=pers[1:3], kumulatif=kum[1]),
               skenario_kmeans=skenario, wcss=dict(zip(["k2", "k3", "k4"], wcss)),
               silhouette_2d=dict(zip(["k2", "k3", "k4"], sil2d)), profil_2d_k3=profil2d, catatan_excel_2d=catatan,
               dendrogram_2d=dict(langkah=lang2d, garis=garis2d, urutan=urut2d, potong=potong2d),
               z_score_populasi_6d=z6,
               dendrogram_6d=dict(langkah=lang6, garis=garis6, urutan=urut6, potong=potong6),
               perbandingan=dict(keanggotaan=anggota, pasangan=pasangan, silhouette=sil_c, profil_6d_k3=profil6d,
                                 tinggi=tinggi_cmp, kesimpulan_excel=kesimpulan))
    simpan_json(out, "hasil_clustering.json")


if __name__ == "__main__":
    d = buat_dataset()
    buat_korelasi(d)
    buat_regresi(d)
    buat_klasifikasi()
    buat_clustering()
    print("selesai.")
