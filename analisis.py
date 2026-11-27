"""Fungsi data dan analisis (tanpa Streamlit) supaya mudah dites dan dipakai ulang.

Hasil statistik utama TIDAK dihitung di sini: regresi dan klasifikasi dibaca dari file JASP,
clustering dari file Excel (semuanya sudah dikonversi oleh prepare_data.py ke folder data/).
Yang dihitung ulang hanya bagian yang bereaksi terhadap filter di sidebar (korelasi,
statistik deskriptif, tren).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).parent / "data"

KATEGORI = ["BAIK", "SEDANG", "TIDAK SEHAT", "SANGAT TIDAK SEHAT"]
KATEGORI_JASP = KATEGORI + ["TIDAK DAPAT DIKLASIFIKASI"]
AMBANG = [(50, "BAIK"), (100, "SEDANG"), (200, "TIDAK SEHAT"), (300, "SANGAT TIDAK SEHAT")]

POLUTAN = ["pm_sepuluh", "pm_duakomalima", "sulfur_dioksida", "karbon_monoksida", "ozon", "nitrogen_dioksida"]
LABEL_POLUTAN = {"pm_sepuluh": "PM10", "pm_duakomalima": "PM2.5", "sulfur_dioksida": "SO₂",
                 "karbon_monoksida": "CO", "ozon": "O₃", "nitrogen_dioksida": "NO₂"}
POLUTAN_EXCEL = {"PM10": "PM10", "PM2.5": "PM2.5", "SO2": "SO₂", "CO": "CO", "O3": "O₃", "NO2": "NO₂"}
NAMA_PARAM = {"PM25": "PM2.5", "PM10": "PM10", "SO2": "SO₂", "O3": "O₃", "NO2": "NO₂", "CO": "CO"}

CUACA = ["suhu_rata2", "kelembaban_rata2", "kecepatan_angin_rata2", "curah_hujan_total", "radiasi_matahari_rata2"]
LABEL_CUACA = {
    "suhu_rata2": "Suhu rata-rata (°C)",
    "kelembaban_rata2": "Kelembapan rata-rata (%)",
    "kecepatan_angin_rata2": "Kecepatan angin (m/s)",
    "curah_hujan_total": "Curah hujan (mm/hari)",
    "radiasi_matahari_rata2": "Radiasi matahari (W/m²)",
}
LABEL_PENDEK = {"suhu_rata2": "Suhu", "kelembaban_rata2": "Kelembapan", "kecepatan_angin_rata2": "Kec. angin",
                "curah_hujan_total": "Curah hujan", "radiasi_matahari_rata2": "Radiasi", "nilai_ispu": "ISPU"}
LABEL_VAR = {**LABEL_CUACA, "nilai_ispu": "Nilai ISPU"}
VAR_KORELASI = CUACA + ["nilai_ispu"]


# ------------------------------------------------------------------ pemuatan data
def muat_dataset():
    d = pd.read_csv(DATA / "dataset_harian.csv", parse_dates=["tanggal"])
    d["parameter_pencemar_kritis"] = d["parameter_pencemar_kritis"].map(NAMA_PARAM).fillna(d["parameter_pencemar_kritis"])
    return d


def muat_json(nama):
    with open(DATA / nama, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ klasifikasi
def kategori_ispu(nilai):
    """Kategori menurut batas ISPU: 0-50 Baik, 51-100 Sedang, 101-200 Tidak Sehat, 201-300 Sangat Tidak Sehat."""
    if nilai is None or (isinstance(nilai, float) and np.isnan(nilai)):
        return "TIDAK DAPAT DIKLASIFIKASI"
    for batas, nama in AMBANG:
        if nilai <= batas:
            return nama
    return "SANGAT TIDAK SEHAT"


def cek_konsistensi_kategori(df):
    """Kategori resmi di dataset (baris) vs kategori hasil batas ISPU (kolom, dasar 'kategori_hasil' di JASP)."""
    t = df.assign(kategori_ambang=df["nilai_ispu"].map(kategori_ispu))
    return pd.crosstab(t["kategori"], t["kategori_ambang"]).reindex(index=KATEGORI, columns=KATEGORI, fill_value=0)


# ------------------------------------------------------------------ korelasi
def kekuatan(r):
    """Kriteria Guilford: <0,2 sangat lemah; 0,2-0,4 lemah; 0,4-0,6 sedang; 0,6-0,8 kuat; >=0,8 sangat kuat."""
    a = abs(r)
    return ("sangat lemah" if a < 0.2 else "lemah" if a < 0.4 else "sedang" if a < 0.6
            else "kuat" if a < 0.8 else "sangat kuat")


def arah(r):
    return "positif" if r > 0 else "negatif" if r < 0 else "tidak ada"


def matriks_korelasi(df, metode="pearson", kolom=VAR_KORELASI):
    """Matriks koefisien, p-value, dan jumlah pasangan (pairwise, seperti tabel Korelasi_Pearson di Tableau)."""
    fn = stats.pearsonr if metode == "pearson" else stats.spearmanr
    n = len(kolom)
    r = np.eye(n)
    p = np.zeros((n, n))
    m = np.zeros((n, n), dtype=int)
    for i in range(n):
        m[i, i] = df[kolom[i]].notna().sum()
        for j in range(i + 1, n):
            s = df[[kolom[i], kolom[j]]].dropna()
            m[i, j] = m[j, i] = len(s)
            if len(s) > 2 and s[kolom[i]].nunique() > 1 and s[kolom[j]].nunique() > 1:
                rr, pp = fn(s[kolom[i]], s[kolom[j]])
            else:
                rr, pp = np.nan, np.nan
            r[i, j] = r[j, i] = rr
            p[i, j] = p[j, i] = pp
    idx = pd.Index(kolom)
    return pd.DataFrame(r, idx, idx), pd.DataFrame(p, idx, idx), pd.DataFrame(m, idx, idx)


# ------------------------------------------------------------------ regresi (memakai koefisien JASP)
def tanda_p(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."


def prediksi_dari_koefisien(hasil_reg, nilai):
    """ISPU prediksi = intersep + jumlah(B x nilai), memakai koefisien Model 1 dari JASP."""
    k = {x["variabel"]: x["B"] for x in hasil_reg["koefisien"]}
    return k["(Intercept)"] + sum(k[v] * nilai[v] for v in hasil_reg["prediktor"])


# ------------------------------------------------------------------ format angka Indonesia
def fmt(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_p(p):
    return "< 0,001" if p < 0.001 else fmt(p, 3)
