"""Membersihkan data mentah (.xls) menjadi CSV ringkas untuk dashboard.

Jalankan sekali di komputer sendiri:
    python prepare_data.py

Taruh dua file mentah di folder raw/:
    raw/Data_Indeks_Standar_Pencemar_Udara__ISPU__di_Provinsi_DKI_Jakarta.xls
    raw/Data_Meteorologi.xls
(Keduanya sebenarnya tabel HTML berekstensi .xls, jadi dibaca dengan read_html.)
"""
import numpy as np
import pandas as pd

RAW_ISPU = "raw/Data_Indeks_Standar_Pencemar_Udara__ISPU__di_Provinsi_DKI_Jakarta.xls"
RAW_METEO = "raw/Data_Meteorologi.xls"

NAMA_STASIUN = {
    "DKI1": "DKI1 Bundaran HI",
    "DKI2": "DKI2 Kelapa Gading",
    "DKI3": "DKI3 Jagakarsa",
    "DKI4": "DKI4 Lubang Buaya",
    "DKI5": "DKI5 Kebon Jeruk",
}


def buat_tanggal(df):
    return pd.to_datetime(
        df["periode_data"].astype(str) + df["tanggal"].astype(str).str.zfill(2),
        format="%Y%m%d",
        errors="coerce",
    )


def main():
    # ---------- ISPU ----------
    a = pd.read_html(RAW_ISPU)[0]
    a["stasiun"] = a["stasiun"].str[:4].map(NAMA_STASIUN)  # samakan nama stasiun
    a["tanggal"] = buat_tanggal(a)
    a = a.dropna(subset=["tanggal", "stasiun"])
    a = a.sort_values("tanggal").drop_duplicates(["tanggal", "stasiun"], keep="last")
    a = a[a["kategori"] != "TIDAK ADA DATA"]
    a = a.rename(columns={"max": "ispu", "parameter_pencemar_kritis": "parameter_kritis"})
    a = a.drop(columns=["periode_data", "bulan"])
    a.to_csv("data/ispu_bersih.csv", index=False)
    print("ISPU:", a.shape)

    # ---------- Meteorologi (per 10 menit -> harian) ----------
    m = pd.read_html(RAW_METEO)[0]
    m["stasiun"] = m["stasiun_pengamatan"].str[:4].map(NAMA_STASIUN)
    m["tanggal"] = buat_tanggal(m)
    m = m.dropna(subset=["tanggal", "stasiun"])
    # buang nilai mustahil (sensor error)
    m.loc[(m.temp_air < 15) | (m.temp_air > 45), "temp_air"] = np.nan
    m.loc[(m.hum_air <= 0) | (m.hum_air > 100), "hum_air"] = np.nan
    m.loc[(m.ff < 0) | (m.ff > 30), "ff"] = np.nan
    m.loc[(m.rain < 0) | (m.rain > 100), "rain"] = np.nan
    m.loc[(m.grad < 0) | (m.grad > 1500), "grad"] = np.nan
    d = (
        m.groupby(["tanggal", "stasiun"])
        .agg(
            suhu=("temp_air", "mean"),
            kelembapan=("hum_air", "mean"),
            angin=("ff", "mean"),
            hujan=("rain", "sum"),
            radiasi=("grad", "mean"),
        )
        .reset_index()
        .round(3)
    )
    d.to_csv("data/meteo_harian.csv", index=False)
    print("Meteorologi harian:", d.shape)


if __name__ == "__main__":
    main()
