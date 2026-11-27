import pandas as pd
import streamlit as st

import analisis as A
import ui


def tampil(k):
    klas, reg, clu, da = k.klas, k.reg, k.clu, k.da
    ui.header("Kesimpulan", "Keterkaitan hasil klasifikasi, korelasi, regresi, dan clustering")

    # ---------------------------------------------------------- angka dari sumber
    tot = next(s for s in klas["silang"] if s["stasiun"] == "Total")
    N = tot["total"]
    pct = pd.DataFrame([{"stasiun": s["stasiun"], **s["persen_baris"]} for s in klas["silang"] if s["stasiun"] != "Total"]).set_index("stasiun")
    ts_max, ts_min = pct["TIDAK SEHAT"].idxmax(), pct["TIDAK SEHAT"].idxmin()
    dom = max(A.KATEGORI, key=lambda c: tot["jumlah"][c])
    ds = pd.DataFrame(klas["deskriptif"])
    ispu_st = ds[ds["variabel"] == "max"].set_index("stasiun")["mean"]
    r, p, _ = A.matriks_korelasi(da)
    r_isp = r["nilai_ispu"].drop("nilai_ispu")
    top = r_isp.abs().idxmax()
    rg = reg["ringkasan"]
    ko = {x["variabel"]: x for x in reg["koefisien"]}
    sil2, sil6 = clu["silhouette_2d"]["k3"], next(x["ward6d"] for x in clu["perbandingan"]["silhouette"] if x["k"] == 3)
    ts = da[da["kategori"].isin(["TIDAK SEHAT", "SANGAT TIDAK SEHAT"])]
    kritis = ts["parameter_pencemar_kritis"].value_counts(normalize=True) * 100
    kritis_d5 = ts[ts["stasiun"] == "DKI5 Kebun Jeruk"]["parameter_pencemar_kritis"].value_counts(normalize=True) * 100

    # ---------------------------------------------------------- empat kesimpulan
    ui.bagian("Kesimpulan per metode")
    c1, c2 = st.columns(2)
    c1.markdown(ui.kartu(
        "Klasifikasi", f"{A.fmt(tot['jumlah'][dom] / N * 100, 1)}% {dom.title()}",
        f"Kualitas udara didominasi kategori {dom.title()}. Hari Tidak Sehat sebesar {A.fmt(tot['jumlah']['TIDAK SEHAT'] / N * 100, 1)}%, "
        f"paling banyak di {ts_max} ({A.fmt(pct.loc[ts_max, 'TIDAK SEHAT'], 1)}%) dan paling sedikit di {ts_min} ({A.fmt(pct.loc[ts_min, 'TIDAK SEHAT'], 1)}%). "
        f"Perbedaan antarstasiun signifikan (p {A.fmt_p(klas['chi2']['p'])}) tetapi lemah (Cramér's V = {A.fmt(klas['cramers_v'], 2)})."), unsafe_allow_html=True)
    c2.markdown(ui.kartu(
        "Korelasi", f"{A.LABEL_PENDEK[top]}: r = {A.fmt(r_isp[top], 2)}",
        f"Suhu paling berkaitan dengan ISPU ({A.arah(r_isp[top])}, {A.kekuatan(r_isp[top])}), disusul kelembapan "
        f"(r = {A.fmt(r_isp['kelembaban_rata2'], 2)}). Radiasi hampir tidak berkorelasi (r = {A.fmt(r_isp['radiasi_matahari_rata2'], 2)}). "
        f"Hubungan terkuat berstatus {A.kekuatan(r_isp[top])} dan korelasi bukan bukti sebab-akibat."), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    n_sig = sum(ko[v]["p"] < 0.05 for v in reg["prediktor"])
    c3.markdown(ui.kartu(
        "Regresi", f"R² = {A.fmt(rg['R2'], 3)}",
        f"Model signifikan (F = {A.fmt(rg['F'], 1)}, p {A.fmt_p(rg['p'])}); {n_sig} dari 5 variabel signifikan. "
        f"Suhu berpengaruh paling besar (B = {A.fmt(ko['suhu_rata2']['B'], 2)} ISPU per °C), sedangkan curah hujan tidak signifikan "
        f"(p = {A.fmt(ko['curah_hujan_total']['p'], 2)}). Cuaca hanya menjelaskan {A.fmt(rg['R2'] * 100, 1)}% variasi ISPU."), unsafe_allow_html=True)
    c4.markdown(ui.kartu(
        "Clustering", "DKI5 terpisah",
        f"Lima stasiun terbagi tiga klaster. DKI5 Kebun Jeruk selalu terpisah (O₃ dan PM2.5 tertinggi, PM10 terendah). Susunan klaster lain berbeda antara PCA 2D dan 6D, "
        f"dan silhouette lemah ({A.fmt(sil2, 2)} pada 2D, {A.fmt(sil6, 2)} pada 6D), sehingga hasil bersifat eksploratif."), unsafe_allow_html=True)

    # ---------------------------------------------------------- hubungan antar temuan
    ui.bagian("Hubungan antartemuan")
    ui.catatan(
        f"<b>DKI5 Kebun Jeruk konsisten menonjol pada dua metode.</b> Pada klasifikasi, DKI5 memiliki rata-rata ISPU tertinggi "
        f"({A.fmt(ispu_st['DKI5 Kebun Jeruk'], 1)}; terendah {ispu_st.idxmin()} {A.fmt(ispu_st.min(), 1)}) dan porsi Tidak Sehat tertinggi. "
        f"Pada clustering, DKI5 membentuk klaster sendiri dengan O₃ dan PM2.5 tertinggi. Dua hasil yang berbeda metode ini menunjuk stasiun yang sama.",
        "1. Klasifikasi dan clustering saling menguatkan", penting=True)
    ui.catatan(
        f"Karena ISPU adalah nilai sub-indeks tertinggi, kategori Tidak Sehat ditentukan oleh polutan tertentu. Pada hari Tidak Sehat, parameter kritis terbanyak adalah "
        f"<b>{kritis.index[0]}</b> ({A.fmt(kritis.iloc[0], 1)}% hari); di DKI5 yaitu <b>{kritis_d5.index[0]}</b> ({A.fmt(kritis_d5.iloc[0], 1)}%). "
        f"Ini selaras dengan profil klaster DKI5 yang PM2.5-nya tinggi.",
        "2. Polutan penentu di balik kategori")
    ui.catatan(
        f"Suhu adalah variabel yang konsisten pada korelasi (r = {A.fmt(r_isp['suhu_rata2'], 2)}) dan regresi (Beta = {A.fmt(ko['suhu_rata2']['beta'], 2)}, p {A.fmt_p(ko['suhu_rata2']['p'])}). "
        f"Namun curah hujan berkorelasi negatif secara tunggal (r = {A.fmt(r_isp['curah_hujan_total'], 2)}) tetapi tidak signifikan dalam model (p = {A.fmt(ko['curah_hujan_total']['p'], 2)}), "
        f"dan suhu–kelembapan saling berkorelasi kuat (r = {A.fmt(r.loc['suhu_rata2', 'kelembaban_rata2'], 2)}). "
        f"Jadi korelasi tunggal tidak otomatis bertahan setelah variabel lain diperhitungkan.",
        "3. Korelasi dan regresi: apa yang bertahan")
    ui.catatan(
        f"Variasi ISPU yang dijelaskan cuaca kecil (R² = {A.fmt(rg['R2'], 3)}) dan hubungan stasiun–kategori juga lemah (V = {A.fmt(klas['cramers_v'], 2)}). "
        f"Artinya, baik kondisi cuaca maupun lokasi stasiun masing-masing hanya menerangkan sebagian kecil perbedaan kualitas udara harian. "
        f"Sumber emisi dan faktor lain yang tidak ada di dataset kemungkinan berperan, tetapi hal ini perlu diuji dengan data tambahan.",
        "4. Cuaca dan lokasi bukan penjelas utama", penting=True)

    # ---------------------------------------------------------- insight & evaluasi
    ui.bagian("Insight utama kualitas udara DKI Jakarta")
    st.markdown(
        f"- Udara Jakarta pada 2024–2025 sebagian besar berada pada kategori **{dom.title()}**; hari Tidak Sehat bukan mayoritas namun tidak bisa diabaikan "
        f"({A.fmt(tot['jumlah']['TIDAK SEHAT'] / N * 100, 1)}%).\n"
        f"- Perbedaan antarstasiun ada tetapi kecil; yang paling berbeda secara karakter polutan adalah **DKI5 Kebun Jeruk**.\n"
        f"- Hari yang lebih panas cenderung berjalan bersama ISPU yang lebih tinggi, tetapi suhu bukan penentu tunggal.")
    ui.bagian("Temuan penting untuk bahan evaluasi")
    st.markdown(
        f"1. **Prioritaskan DKI5 Kebun Jeruk** untuk telaah sumber O₃ dan PM2.5, karena stasiun ini menonjol pada klasifikasi dan clustering.\n"
        f"2. **PM2.5 perlu pemantauan utama** karena paling sering menjadi parameter kritis pada hari Tidak Sehat ({kritis.index[0]} {A.fmt(kritis.iloc[0], 1)}%).\n"
        f"3. **Perhatikan profil khas tiap stasiun** pada analisis 6D: DKI3 Jagakarsa menonjol pada NO₂ dan SO₂, sedangkan DKI1, DKI2, DKI4 relatif mirip.\n"
        f"4. **Hari bersuhu tinggi** layak diberi perhatian lebih sebagai penanda risiko (asosiasi, bukan penyebab).\n"
        f"5. **Perbaiki kualitas data**: banyak data PM10 hilang di DKI2 Kelapa Gading ({A.fmt(ds[(ds['variabel'] == 'pm_sepuluh') & (ds['stasiun'] == 'DKI2 Kelapa Gading')]['hilang'].iloc[0], 0)} hari), "
        f"nilai ekstrem kecepatan angin, dan perbedaan kategori bawaan dengan batas ISPU pada beberapa hari.")

    ui.bagian("Keterbatasan penelitian")
    ui.catatan(
        "• Korelasi dan regresi menunjukkan asosiasi, bukan sebab-akibat.<br>"
        f"• Regresi hanya menjelaskan {A.fmt(rg['R2'] * 100, 1)}% variasi ISPU dan memakai data harian dengan potensi autokorelasi waktu yang tidak diuji pada hasil JASP.<br>"
        "• Clustering hanya melibatkan 5 stasiun, silhouette lemah, dan hasil 2D berbeda dari 6D.<br>"
        "• Analisis klasifikasi bersifat deskriptif (frekuensi dan uji independensi), bukan model prediksi.")
