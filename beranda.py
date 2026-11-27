import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analisis as A
import ui

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tgl(t):
    return f"{t.day} {BULAN[t.month - 1]} {t.year}"


def tampil(k):
    df, da = k.df, k.da
    ui.header(ui.JUDUL, ui.SUBJUDUL)
    st.markdown(
        "Dashboard ini merangkum analisis kualitas udara di lima stasiun pemantauan DKI Jakarta dan hubungannya "
        "dengan kondisi meteorologi. Empat metode dipakai bersama: **klasifikasi** untuk memetakan kategori ISPU, "
        "**korelasi** untuk melihat keterkaitan cuaca dengan ISPU, **regresi** untuk menguji pengaruh simultan variabel "
        "cuaca, dan **clustering** untuk mengelompokkan stasiun berdasarkan karakter polutannya."
    )
    tidak_sehat = df["kategori"].isin(["TIDAK SEHAT", "SANGAT TIDAK SEHAT"]).mean() * 100
    ui.kpi([
        ("Observasi harian", A.fmt(len(df), 0), "baris stasiun-tanggal"),
        ("Stasiun pemantauan", df["stasiun"].nunique(), "dari 5 stasiun DKI Jakarta"),
        ("Periode pengamatan", f"{tgl(df['tanggal'].min())} – {tgl(df['tanggal'].max())}", "sesuai filter sidebar"),
        ("Rata-rata ISPU", A.fmt(df["nilai_ispu"].mean(), 1), "nilai harian tertinggi dari 6 polutan"),
        ("Hari Tidak Sehat", f"{A.fmt(tidak_sehat, 1)}%", "kategori Tidak Sehat atau lebih buruk", True),
    ])

    # ---------------------------------------------------------- ringkasan empat metode
    ui.bagian("Ringkasan empat metode analisis")
    klas, reg, clu = k.klas, k.reg, k.clu
    total = next(s for s in klas["silang"] if s["stasiun"] == "Total")
    n_klas = total["total"]
    dom = max(A.KATEGORI, key=lambda c: total["jumlah"][c])
    pearson, _, _ = A.matriks_korelasi(da)
    r_isp = pearson["nilai_ispu"].drop("nilai_ispu")
    v_top = r_isp.abs().idxmax()
    rg = reg["ringkasan"]
    s3 = clu["silhouette_2d"]["k3"]
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(ui.kartu("1. Klasifikasi", f"{A.fmt(total['jumlah'][dom] / n_klas * 100, 1)}% {dom.title()}",
                         f"Dari {A.fmt(n_klas, 0)} observasi JASP, kategori {dom.title()} paling dominan; "
                         f"Tidak Sehat {A.fmt(total['jumlah']['TIDAK SEHAT'] / n_klas * 100, 1)}%."), unsafe_allow_html=True)
    c2.markdown(ui.kartu("2. Korelasi", f"r = {A.fmt(r_isp[v_top], 2)}",
                         f"{A.LABEL_CUACA[v_top].split(' (')[0]} punya korelasi terkuat dengan ISPU "
                         f"({A.arah(r_isp[v_top])}, {A.kekuatan(r_isp[v_top])})."), unsafe_allow_html=True)
    c3.markdown(ui.kartu("3. Regresi", f"R² = {A.fmt(rg['R2'], 3)}",
                         f"Model signifikan (F = {A.fmt(rg['F'], 1)}, p {A.fmt_p(rg['p'])}) tetapi hanya menjelaskan "
                         f"{A.fmt(rg['R2'] * 100, 1)}% variasi ISPU."), unsafe_allow_html=True)
    c4.markdown(ui.kartu("4. Clustering", "3 klaster",
                         f"DKI5 Kebun Jeruk selalu terpisah dari stasiun lain. Silhouette k = 3 (PCA 2D) hanya "
                         f"{A.fmt(s3, 2)}: pemisahan lemah."), unsafe_allow_html=True)

    # ---------------------------------------------------------- informasi dataset + komposisi
    ui.bagian("Informasi dataset")
    a, b = st.columns([1.25, 1])
    info = pd.DataFrame({
        "Keterangan": ["Periode pengamatan", "Jumlah observasi (dataset bersih)", "Stasiun pemantauan",
                       "Parameter pencemar", "Variabel meteorologi", "Observasi dipakai regresi",
                       "Observasi dipakai klasifikasi (JASP)"],
        "Isi": [f"{tgl(da['tanggal'].min())} – {tgl(da['tanggal'].max())}",
                f"{A.fmt(len(da), 0)} baris harian",
                "DKI1 Bundaran HI, DKI2 Kelapa Gading, DKI3 Jagakarsa, DKI4 Lubang Buaya, DKI5 Kebun Jeruk",
                "PM10, PM2.5, SO₂, CO, O₃, NO₂ (ISPU = nilai tertinggi dari keenamnya)",
                "Suhu, kelembapan, kecepatan angin, curah hujan, radiasi matahari",
                f"{A.fmt(reg['n'], 0)} (data lengkap, listwise)",
                f"{A.fmt(n_klas, 0)} (termasuk {A.fmt(total['jumlah']['TIDAK DAPAT DIKLASIFIKASI'], 0)} hari tanpa nilai ISPU)"],
    })
    a.dataframe(info, use_container_width=True, hide_index=True)
    kat = df["kategori"].value_counts().reindex(A.KATEGORI).dropna().reset_index()
    kat.columns = ["kategori", "hari"]
    fig = px.pie(kat, names="kategori", values="hari", hole=0.55, color="kategori", color_discrete_map=ui.WARNA_KAT,
                 title="Komposisi kategori kualitas udara")
    fig.update_traces(textinfo="percent", sort=False, marker=dict(line=dict(color="#fff", width=2)))
    with b:
        ui.tampilkan(fig, 330)

    # ---------------------------------------------------------- visual gambaran umum
    ui.bagian("Gambaran umum kualitas udara")
    t1, t2, t3 = st.tabs(["Tren waktu", "Pola musiman", "Perbandingan stasiun"])
    with t1:
        c1, c2 = st.columns([3, 1])
        agregasi = c1.radio("Agregasi waktu", ["Harian", "Mingguan", "Bulanan"], index=2, horizontal=True)
        gab = c2.checkbox("Rata-ratakan semua stasiun")
        freq = {"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}[agregasi]
        idx = df.set_index("tanggal")
        if gab:
            tren = idx["nilai_ispu"].resample(freq).mean().reset_index()
            tren["stasiun"] = "Rata-rata stasiun terpilih"
            peta = {"Rata-rata stasiun terpilih": ui.OCEAN}
        else:
            tren = idx.groupby("stasiun")["nilai_ispu"].resample(freq).mean().reset_index()
            peta = ui.WARNA_STASIUN
        fig = px.line(tren, x="tanggal", y="nilai_ispu", color="stasiun", color_discrete_map=peta,
                      title=f"Nilai ISPU ({agregasi.lower()})", labels={"tanggal": "Tanggal", "nilai_ispu": "Nilai ISPU", "stasiun": "Stasiun"})
        fig.add_hline(y=50, line_dash="dot", line_color=ui.REDAM, annotation_text="Batas Baik (50)")
        fig.add_hline(y=100, line_dash="dot", line_color=ui.NAVY, annotation_text="Batas Sedang (100)")
        ui.tampilkan(fig, 420)
    with t2:
        d = df.copy()
        d["bln"] = d["tanggal"].dt.month
        d["tahun"] = d["tanggal"].dt.year.astype(str)
        musim = d.groupby(["tahun", "bln"])["nilai_ispu"].mean().reset_index()
        fig = px.line(musim, x="bln", y="nilai_ispu", color="tahun", markers=True,
                      color_discrete_sequence=[ui.CYAN, ui.OCEAN, ui.SOLAR],
                      title="Rata-rata ISPU per bulan", labels={"bln": "Bulan", "nilai_ispu": "Nilai ISPU", "tahun": "Tahun"})
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=BULAN)
        ui.tampilkan(fig, 380)
        rata = d.groupby("bln")["nilai_ispu"].mean()
        st.caption(f"Rata-rata semua tahun terpilih: tertinggi pada **{BULAN[rata.idxmax() - 1]}** "
                   f"({A.fmt(rata.max(), 1)}), terendah pada **{BULAN[rata.idxmin() - 1]}** ({A.fmt(rata.min(), 1)}).")
    with t3:
        ring = df.groupby("stasiun")["nilai_ispu"].mean().sort_values().reset_index()
        fig = px.bar(ring, x="nilai_ispu", y="stasiun", orientation="h", color="stasiun",
                     color_discrete_map=ui.WARNA_STASIUN, text=ring["nilai_ispu"].round(1),
                     title="Rata-rata ISPU per stasiun", labels={"nilai_ispu": "Rata-rata ISPU", "stasiun": ""})
        fig.update_layout(showlegend=False)
        ui.tampilkan(fig, 320, legenda_bawah=False)

    # ---------------------------------------------------------- insight
    ui.bagian("Insight utama")
    ui.catatan(
        f"• Kualitas udara didominasi kategori <b>{dom.title()}</b>; hari <b>Tidak Sehat</b> relatif jarang namun nyata "
        f"({A.fmt(total['jumlah']['TIDAK SEHAT'] / n_klas * 100, 1)}%).<br>"
        f"• Suhu menjadi variabel cuaca yang paling berkaitan dengan ISPU, tetapi kekuatannya hanya "
        f"<b>{A.kekuatan(r_isp[v_top])}</b> dan model regresi hanya menjelaskan {A.fmt(rg['R2'] * 100, 1)}% variasi.<br>"
        f"• Secara karakter polutan, <b>DKI5 Kebun Jeruk</b> paling berbeda dari stasiun lain pada semua metode clustering.<br>"
        f"• Dengan hanya 5 stasiun, hasil clustering bersifat eksploratif. Baca halaman <b>Kesimpulan</b> untuk keterkaitan antarmetode.",
        "Yang perlu diketahui dari hasil penelitian")
    with st.expander("Catatan data dan sumber hasil"):
        st.markdown(
            "- **Skala ISPU**: Baik 0–50, Sedang 51–100, Tidak Sehat 101–200, Sangat Tidak Sehat 201–300. "
            "ISPU harian adalah nilai tertinggi dari sub-indeks enam polutan.\n"
            "- **Klasifikasi**: hasil JASP (`KLASIFIKASI.jasp`). **Korelasi**: acuan Tableau (`.twbx`), lihat catatan di halaman Korelasi. "
            "**Regresi**: JASP (`kausalitass jasp`). **Clustering**: Excel `..._Clustering_PCA_REVISI.xlsx`.\n"
            "- Filter stasiun dan periode di sidebar memengaruhi grafik eksploratif (tren, korelasi, perbandingan stasiun). "
            "Tabel hasil JASP dan Excel selalu memakai seluruh data karena merupakan hasil analisis tetap."
        )
