# Dashboard Analisis Kualitas Udara DKI Jakarta

Visualisasi dan Analisis Data Menggunakan Metode Klasifikasi, Korelasi, Regresi, dan Clustering.

Aplikasi Streamlit ini adalah revisi dari dashboard ISPU sebelumnya (struktur `app.py` + `analisis.py` + `data/` dipertahankan).
Isinya kini mengikuti empat file hasil analisis penelitian.

## Halaman
| Halaman | Sumber hasil | Isi utama |
|---|---|---|
| Beranda | dataset bersih (Excel) | KPI, ringkasan 4 metode, informasi dataset, tren, pola musiman, perbandingan stasiun |
| Klasifikasi | `KLASIFIKASI.jasp` | frekuensi kategori, tabel silang stasiun × kategori, Chi-square, Cramér's V, statistik polutan, kalkulator kategori ISPU |
| Korelasi | `Analtika Data korelasi kausalitas.twbx` | heatmap, koefisien Pearson (pembanding Spearman), scatter plot, arah dan kekuatan |
| Kausalitas / Regresi | `kausalitass jasp.jasp.zip` | ringkasan model, R², Adjusted R², ANOVA, koefisien, signifikansi, Q-Q plot, simulasi |
| Clustering | `..._Clustering_PCA_REVISI.xlsx` | Z-score, PCA, dendrogram Ward 2D dan 6D, profil klaster, perbandingan 2D vs 6D |
| Kesimpulan | gabungan | kesimpulan per metode, hubungan antartemuan, bahan evaluasi, keterbatasan |

## Struktur folder
```
app.py                 router, sidebar, filter
analisis.py            fungsi data (muat data, korelasi, format angka)
ui.py                  palet warna, CSS, komponen tampilan
prepare_data.py        membangun data/ dari empat file sumber
halaman/               satu modul per halaman
data/                  dataset_harian.csv, hasil_klasifikasi.json, hasil_regresi.json,
                       hasil_clustering.json, korelasi_pearson.csv
assets/                qq_residual_jasp.png (diambil dari JASP)
sumber/                tempat file sumber (opsional, hanya untuk prepare_data.py)
legacy/                skrip pembersihan data mentah versi lama (prepare_data_mentah.py)
.streamlit/config.toml tema warna
```

## Menjalankan di komputer sendiri
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deployment ke Streamlit Community Cloud
1. Unggah seluruh isi folder ini ke repositori GitHub (folder `data/` dan `assets/` wajib ikut).
2. Buka https://share.streamlit.io, pilih **New app**, pilih repositori dan cabang.
3. Isi **Main file path** dengan `app.py`, lalu **Deploy**. Dependensi dibaca otomatis dari `requirements.txt`.

## Membuat ulang data dari file sumber (opsional)
Taruh empat file di `sumber/`, lalu jalankan `python prepare_data.py`:
`Analitika_Data_Bersih_ISPU_Meteorologi_Clustering_PCA_REVISI.xlsx`, `KLASIFIKASI.jasp`, `kausalitass_jasp_jasp.zip`, `Analtika_Data_korelasi_kausalitas.twbx`.
Skrip memverifikasi bahwa koefisien regresi JASP identik dengan hitungan ulang dari dataset.

## Catatan akurasi
- Regresi, klasifikasi, dan clustering disalin dari file JASP dan Excel tanpa perubahan angka.
- Tabel `Korelasi_Pearson` di file Tableau tersimpan di ekstrak `.hyper` terkompresi yang tidak bisa dibaca di luar Tableau. Koefisien Pearson karena itu
  dihitung ulang dari dataset yang sama; cocokkan dengan tampilan Tableau Anda.
- JASP klasifikasi memakai 3.501 observasi (termasuk 21 hari tanpa ISPU), dataset bersih 3.480. Selisih dijelaskan di halaman Klasifikasi.
- Fitur lama yang tidak lagi dipakai: Random Forest dan K-means Stasiun-Bulan, karena angkanya tidak berasal dari keempat file sumber.

## Sumber data
Data ISPU dan Data Meteorologi Provinsi DKI Jakarta (Satu Data Jakarta).
