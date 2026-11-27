import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analisis as A
import ui

KAT = A.KATEGORI_JASP


def _tabel_silang(klas):
    baris = [s for s in klas["silang"] if s["stasiun"] != "Total"]
    jml = pd.DataFrame([{**{"Stasiun": s["stasiun"]}, **{c: int(s["jumlah"][c]) for c in KAT}, "Total": int(s["total"])}
                        for s in baris]).set_index("Stasiun")
    pct = pd.DataFrame([{**{"Stasiun": s["stasiun"]}, **{c: s["persen_baris"][c] for c in KAT}} for s in baris]).set_index("Stasiun")
    harap = pd.DataFrame([{**{"Stasiun": s["stasiun"]}, **{c: s["harapan"][c] for c in KAT}} for s in baris]).set_index("Stasiun")
    tot = next(s for s in klas["silang"] if s["stasiun"] == "Total")
    return jml, pct, harap, tot


def tampil(k):
    klas, df, da = k.klas, k.df, k.da
    ui.header("Klasifikasi Kualitas Udara", "Pengelompokan kondisi udara berdasarkan kategori ISPU (hasil analisis JASP)")
    jml, pct, harap, tot = _tabel_silang(klas)
    N = tot["total"]
    frek = pd.Series({c: tot["jumlah"][c] for c in KAT})
    dom = frek[A.KATEGORI].idxmax()

    st.markdown(
        "Klasifikasi di sini mengelompokkan setiap observasi harian (stasiun × tanggal) ke dalam kategori ISPU menurut nilai "
        "ISPU tertinggi dari enam polutan: **Baik** (0–50), **Sedang** (51–100), **Tidak Sehat** (101–200), dan "
        "**Sangat Tidak Sehat** (201–300). Hari tanpa nilai ISPU dicatat sebagai *Tidak Dapat Diklasifikasi*. "
        "Seluruh tabel pada halaman ini bersumber dari hasil JASP."
    )
    ui.kpi([
        ("Observasi diklasifikasi", A.fmt(N, 0), "total data analisis JASP"),
        ("Kategori dominan", dom.title(), f"{A.fmt(frek[dom] / N * 100, 1)}% dari seluruh observasi"),
        ("Baik", f"{A.fmt(frek['BAIK'] / N * 100, 1)}%", f"{A.fmt(frek['BAIK'], 0)} observasi"),
        ("Tidak Sehat", f"{A.fmt(frek['TIDAK SEHAT'] / N * 100, 1)}%", f"{A.fmt(frek['TIDAK SEHAT'], 0)} observasi", True),
        ("Sangat Tidak Sehat", A.fmt(frek["SANGAT TIDAK SEHAT"], 0), "kejadian di seluruh data"),
    ])

    t1, t2, t3, t4, t5 = st.tabs(["Distribusi kategori", "Perbandingan antarstasiun", "Statistik polutan (JASP)",
                                  "Eksplorasi dengan filter", "Coba klasifikasi"])

    # ---------------------------------------------------------- 1 distribusi
    with t1:
        a, b = st.columns([1.3, 1])
        d = pd.DataFrame({"kategori": KAT, "jumlah": [frek[c] for c in KAT]})
        d["persen"] = d["jumlah"] / N * 100
        fig = px.bar(d, x="jumlah", y="kategori", orientation="h", color="kategori", color_discrete_map=ui.WARNA_KAT,
                     text=[f"{A.fmt(j, 0)} ({A.fmt(p, 1)}%)" for j, p in zip(d["jumlah"], d["persen"])],
                     title="Frekuensi setiap kategori", labels={"jumlah": "Jumlah observasi", "kategori": ""},
                     category_orders={"kategori": KAT[::-1]})
        fig.update_layout(showlegend=False)
        fig.update_traces(textposition="outside", cliponaxis=False)
        with a:
            ui.tampilkan(fig, 360, legenda_bawah=False)
        tab = d.assign(jumlah=d["jumlah"].astype(int), persen=d["persen"].round(2)).rename(
            columns={"kategori": "Kategori", "jumlah": "Frekuensi", "persen": "Persentase (%)"})
        b.markdown("**Tabel frekuensi**")
        b.dataframe(tab, use_container_width=True, hide_index=True)
        b.caption(f"Total {A.fmt(N, 0)} observasi, sama dengan tabel Contingency Tables JASP.")
        ui.catatan(
            f"Kategori <b>{dom.title()}</b> mendominasi dengan {A.fmt(frek[dom] / N * 100, 1)}% observasi. "
            f"Kategori Baik ({A.fmt(frek['BAIK'] / N * 100, 1)}%) dan Tidak Sehat ({A.fmt(frek['TIDAK SEHAT'] / N * 100, 1)}%) "
            f"sama-sama minoritas, sedangkan Sangat Tidak Sehat hanya {A.fmt(frek['SANGAT TIDAK SEHAT'], 0)} kejadian "
            f"dan {A.fmt(frek['TIDAK DAPAT DIKLASIFIKASI'], 0)} hari tidak dapat diklasifikasi karena nilai ISPU kosong.",
            "Cara membaca")

    # ---------------------------------------------------------- 2 antarstasiun
    with t2:
        pl = pct.reset_index().melt(id_vars="Stasiun", var_name="kategori", value_name="persen")
        fig = px.bar(pl, y="Stasiun", x="persen", color="kategori", orientation="h", color_discrete_map=ui.WARNA_KAT,
                     category_orders={"kategori": KAT, "Stasiun": list(pct.index[::-1])},
                     title="Komposisi kategori per stasiun (% dari hari pengamatan)",
                     labels={"persen": "% observasi", "Stasiun": "", "kategori": "Kategori"})
        ui.tampilkan(fig, 380)
        a, b = st.columns(2)
        a.markdown("**Frekuensi (jumlah observasi)**")
        a.dataframe(jml, use_container_width=True)
        b.markdown("**Persentase dalam stasiun (%)**")
        b.dataframe(pct.round(1), use_container_width=True)

        chi = klas["chi2"]
        v = klas["cramers_v"]
        ui.kpi([("Chi-square (Χ²)", A.fmt(chi["nilai"], 2), f"df = {chi['df']}"),
                ("Signifikansi (p)", A.fmt_p(chi["p"]), "uji independensi stasiun × kategori"),
                ("Cramér's V", A.fmt(v, 3), "kekuatan hubungan (0 sampai 1)", True)])
        terbanyak_ts = pct["TIDAK SEHAT"].idxmax()
        tersedikit_ts = pct["TIDAK SEHAT"].idxmin()
        kecil = [c for c in KAT if (harap[c] < 5).any()]
        ui.catatan(
            f"Uji Chi-square signifikan (p {A.fmt_p(chi['p'])}), artinya komposisi kategori berbeda antarstasiun. "
            f"Namun Cramér's V = {A.fmt(v, 2)} menunjukkan hubungan stasiun-kategori yang <b>lemah</b>: perbedaannya nyata secara statistik, "
            f"tetapi besarnya kecil. <b>{terbanyak_ts}</b> punya porsi Tidak Sehat tertinggi ({A.fmt(pct.loc[terbanyak_ts, 'TIDAK SEHAT'], 1)}%) "
            f"dan <b>{tersedikit_ts}</b> terendah ({A.fmt(pct.loc[tersedikit_ts, 'TIDAK SEHAT'], 1)}%).<br>"
            f"<i>Catatan:</i> kategori {', '.join(c.title() for c in kecil)} memiliki frekuensi harapan di bawah 5 pada sebagian sel, "
            f"sehingga nilai Χ² sebaiknya dibaca hati-hati.",
            "Interpretasi", penting=True)

    # ---------------------------------------------------------- 3 statistik polutan JASP
    with t3:
        ds = pd.DataFrame(klas["deskriptif"])
        peta = {"pm_sepuluh": "PM10", "pm_duakomalima": "PM2.5", "sulfur_dioksida": "SO₂", "karbon_monoksida": "CO",
                "ozon": "O₃", "nitrogen_dioksida": "NO₂", "max": "ISPU (nilai tertinggi)"}
        ds["Parameter"] = ds["variabel"].map(peta)
        hm = ds.pivot(index="stasiun", columns="Parameter", values="mean")[list(peta.values())]
        fig = px.imshow(hm, text_auto=".1f", aspect="auto", color_continuous_scale=ui.SKALA_URUT,
                        title="Rata-rata sub-indeks per stasiun dan parameter",
                        labels={"x": "", "y": "", "color": "Rata-rata"})
        ui.tampilkan(fig, 340, legenda_bawah=False)
        pilih = st.selectbox("Lihat tabel statistik deskriptif untuk parameter", list(peta.values()), index=1)
        tb = ds[ds["Parameter"] == pilih][["stasiun", "valid", "hilang", "mean", "sd", "min", "maks"]].rename(
            columns={"stasiun": "Stasiun", "valid": "N valid", "hilang": "Data hilang", "mean": "Rata-rata",
                     "sd": "Std. deviasi", "min": "Min", "maks": "Maks"})
        st.dataframe(tb.round(2), use_container_width=True, hide_index=True)
        st.caption("Sumber: Descriptive Statistics JASP (dipisah per stasiun).")

    # ---------------------------------------------------------- 4 eksplorasi dengan filter
    with t4:
        st.caption("Bagian ini dihitung dari dataset bersih (3.480 observasi) dan mengikuti filter di sidebar, "
                   "sehingga angkanya dapat berbeda dari tabel JASP.")
        ring = df.groupby("stasiun").agg(
            rata_rata=("nilai_ispu", "mean"), median=("nilai_ispu", "median"), maks=("nilai_ispu", "max"),
            persen_tidak_sehat=("kategori", lambda s: s.isin(["TIDAK SEHAT", "SANGAT TIDAK SEHAT"]).mean() * 100),
            n=("nilai_ispu", "size")).round(1).sort_values("rata_rata")
        st.dataframe(ring.rename(columns={"rata_rata": "Rata-rata ISPU", "median": "Median", "maks": "Maksimum",
                                          "persen_tidak_sehat": "% hari Tidak Sehat", "n": "Jumlah hari"}),
                     use_container_width=True)
        a, b = st.columns(2)
        fig = px.box(df, x="stasiun", y="nilai_ispu", color="stasiun", color_discrete_map=ui.WARNA_STASIUN, points=False,
                     title="Sebaran nilai ISPU", labels={"stasiun": "", "nilai_ispu": "Nilai ISPU"})
        fig.update_layout(showlegend=False)
        with a:
            ui.tampilkan(fig, 380, legenda_bawah=False)
        kr = df.dropna(subset=["parameter_pencemar_kritis"]).groupby(["stasiun", "parameter_pencemar_kritis"]).size().reset_index(name="n")
        kr["persen"] = kr["n"] / kr.groupby("stasiun")["n"].transform("sum") * 100
        fig = px.bar(kr, x="persen", y="stasiun", color="parameter_pencemar_kritis", orientation="h",
                     color_discrete_sequence=[ui.OCEAN, ui.CYAN, ui.SOLAR, ui.NAVY, ui.SUN, ui.NETRAL],
                     title="Parameter pencemar kritis (penentu ISPU harian)",
                     labels={"persen": "% hari", "stasiun": "", "parameter_pencemar_kritis": "Parameter"})
        with b:
            ui.tampilkan(fig, 380)

    # ---------------------------------------------------------- 5 coba klasifikasi
    with t5:
        st.caption("ISPU harian adalah nilai sub-indeks polutan yang paling tinggi, lalu dikelompokkan menurut batas kategori. "
                   "Isi sub-indeks tiap parameter untuk melihat kategorinya. Ini aturan baku, bukan model prediksi.")
        med = da[A.POLUTAN].median()
        cols = st.columns(6)
        nilai = {p: cols[i].number_input(A.LABEL_POLUTAN[p], 0, 500, int(med[p]), key=f"kal_{p}") for i, p in enumerate(A.POLUTAN)}
        puncak = max(nilai, key=nilai.get)
        hasil = A.kategori_ispu(nilai[puncak])
        st.markdown(
            f"<div class='catatan penting'><b class='t'>ISPU = {nilai[puncak]}</b>Kategori: <b>{hasil.title()}</b> · "
            f"parameter kritis: <b>{A.LABEL_POLUTAN[puncak]}</b></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------- konsistensi
    with st.expander("Catatan konsistensi data JASP dan dataset bersih"):
        cek = A.cek_konsistensi_kategori(da)
        selisih = int(cek.values.sum() - np.trace(cek.values))
        st.markdown(
            f"Analisis JASP memakai {A.fmt(N, 0)} observasi, sedangkan dataset bersih berisi {A.fmt(len(da), 0)} "
            f"(selisih {A.fmt(N - len(da), 0)} = hari tanpa nilai ISPU). Kolom `kategori_hasil` di JASP dibentuk dari batas nilai ISPU, "
            f"sementara kolom `kategori` di dataset bersih adalah kategori bawaan data. Keduanya berbeda pada **{selisih}** observasi "
            f"(tabel di bawah: baris = kategori bawaan, kolom = kategori menurut batas ISPU). Dashboard memakai angka JASP pada tab "
            f"Distribusi dan Antarstasiun, serta kategori bawaan pada grafik eksploratif.")
        st.dataframe(cek, use_container_width=True)
