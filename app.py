"""Dashboard Analisis Kualitas Udara DKI Jakarta.

Jalankan:  streamlit run app.py
"""
from types import SimpleNamespace

import streamlit as st

import analisis as A
import beranda
import clustering
import kesimpulan
import klasifikasi
import korelasi
import regresi

st.set_page_config(page_title="Dashboard Analisis Kualitas Udara DKI Jakarta", page_icon="🌫️", layout="wide")
ui.pasang_tema()


@st.cache_data
def muat():
    return (A.muat_dataset(), A.muat_json("hasil_klasifikasi.json"), A.muat_json("hasil_regresi.json"),
            A.muat_json("hasil_clustering.json"))


da, klas, reg, clu = muat()

HALAMAN = {
    "Beranda": beranda,
    "Klasifikasi": klasifikasi,
    "Korelasi": korelasi,
    "Kausalitas / Regresi": regresi,
    "Clustering": clustering,
    "Kesimpulan": kesimpulan,
}

# ------------------------------------------------------------------ sidebar
sb = st.sidebar
sb.markdown('<div class="sb-judul">Analisis Kualitas Udara DKI Jakarta</div>'
            '<div class="sb-sub">Klasifikasi · Korelasi · Regresi · Clustering</div>', unsafe_allow_html=True)
sb.markdown("---")
sb.markdown('<div class="sb-label">Navigasi</div>', unsafe_allow_html=True)
halaman = sb.radio("Halaman", list(HALAMAN), label_visibility="collapsed")

sb.markdown("---")
sb.markdown('<div class="sb-label">Filter data eksploratif</div>', unsafe_allow_html=True)
semua = sorted(da["stasiun"].unique())
pilih = sb.multiselect("Stasiun", semua, default=semua)
tmin, tmax = da["tanggal"].min().date(), da["tanggal"].max().date()
rentang = sb.date_input("Periode", value=(tmin, tmax), min_value=tmin, max_value=tmax)
t0, t1 = rentang if isinstance(rentang, (tuple, list)) and len(rentang) == 2 else (tmin, tmax)
sb.caption("Filter berlaku untuk grafik dan tabel yang dihitung dari dataset (tren, korelasi, eksplorasi). "
           "Tabel hasil JASP dan Excel tetap memakai seluruh data.")
sb.markdown("---")
sb.caption("Sumber: Data ISPU dan Data Meteorologi Provinsi DKI Jakarta (Satu Data Jakarta), diolah dengan JASP, Tableau, dan Excel.")

mask = da["stasiun"].isin(pilih) & (da["tanggal"].dt.date >= t0) & (da["tanggal"].dt.date <= t1)
df = da[mask].copy()
if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah stasiun atau periode di sidebar.")
    st.stop()

k = SimpleNamespace(df=df, da=da, klas=klas, reg=reg, clu=clu, filter_aktif=len(df) != len(da))
HALAMAN[halaman].tampil(k)
