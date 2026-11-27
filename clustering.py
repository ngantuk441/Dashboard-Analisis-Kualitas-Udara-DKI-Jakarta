import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analisis as A
import ui


def _label(c):
    return A.POLUTAN_EXCEL.get(c, c)


def _deskripsi(z):
    naik = sorted([(k, v) for k, v in z.items() if v >= 0.5], key=lambda t: -t[1])
    turun = sorted([(k, v) for k, v in z.items() if v <= -0.5], key=lambda t: t[1])
    f = lambda lst: ", ".join(f"{_label(k)} ({'+' if v > 0 else '−'}{A.fmt(abs(v), 2)})" for k, v in lst)
    teks = []
    if naik:
        teks.append(f"di atas rata-rata: <b>{f(naik)}</b>")
    if turun:
        teks.append(f"di bawah rata-rata: {f(turun)}")
    return "; ".join(teks) if teks else "mendekati rata-rata lima stasiun pada semua polutan"


def _dendrogram(d, k_potong, judul):
    fig = go.Figure()
    langkah = {}
    for nama, x, y in d["garis"]:
        langkah.setdefault(nama, []).append((x, y))
    for nama, pts in langkah.items():
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", name=nama, showlegend=False,
                                 line=dict(color=ui.OCEAN, width=3),
                                 hovertemplate=f"{nama}<br>tinggi penggabungan = %{{y:.3f}}<extra></extra>"))
    kunci = f"potong → {k_potong} cluster"
    pt = d["potong"].get(kunci)
    if pt:
        fig.add_hline(y=pt["y"], line_dash="dash", line_color=ui.SOLAR, line_width=3,
                      annotation_text=f"potong → {k_potong} klaster", annotation_position="top right")
    xs = [x for _, x in d["urutan"]]
    fig.update_xaxes(tickmode="array", tickvals=xs, ticktext=[s for s, _ in d["urutan"]], range=[0.4, 5.6], title="Stasiun")
    fig.update_yaxes(title="Jarak penggabungan (Ward)", rangemode="tozero")
    fig.update_layout(title=judul)
    return fig, (pt["ket"] if pt else "")


def tampil(k):
    c = k.clu
    ui.header("Clustering Stasiun Pemantauan", "Pengelompokan lima stasiun berdasarkan karakter enam polutan (PCA dan Hierarchical Clustering Ward)")
    POL = c["polutan"]
    stasiun = c["stasiun"]
    var = c["varians"]
    sil2 = c["silhouette_2d"]
    sil6 = {f"k{x['k']}": x["ward6d"] for x in c["perbandingan"]["silhouette"]}
    st.markdown(
        "Alur analisis: rata-rata enam polutan per stasiun → standardisasi **Z-score** → **PCA** (enam polutan diringkas menjadi dua sumbu, PC1 dan PC2) → "
        "**Hierarchical Clustering metode Ward** → hasilnya dibandingkan dengan clustering pada enam polutan penuh (6D)."
    )
    ui.kpi([
        ("Stasiun dikelompokkan", len(stasiun), "satu titik data per stasiun"),
        ("Varians dijelaskan PC1 + PC2", f"{A.fmt(var['kumulatif'] * 100, 1)}%", f"PC1 {A.fmt(var['persen'][0] * 100, 1)}% · PC2 {A.fmt(var['persen'][1] * 100, 1)}%"),
        ("Silhouette k = 3 (PCA 2D)", A.fmt(sil2["k3"], 2), "tertinggi di antara k = 2, 3, 4", True),
        ("Silhouette k = 3 (6D)", A.fmt(sil6["k3"], 2), "di bawah 0,25: pemisahan lemah"),
    ])

    t1, t2, t3, t4, t5 = st.tabs(["Data dan standardisasi", "PCA dan persebaran", "Dendrogram", "Karakteristik klaster", "Perbandingan 2D vs 6D"])

    # ---------------------------------------------------------- 1 data
    with t1:
        rata = pd.DataFrame(c["rata_rata"]).T[POL].rename(columns=_label)
        z = pd.DataFrame(c["z_score_sampel"]).T[POL].rename(columns=_label)
        a, b = st.columns(2)
        a.markdown("**Rata-rata enam polutan per stasiun** (sub-indeks)")
        a.dataframe(rata.round(2), use_container_width=True)
        fig = px.imshow(z, text_auto=".2f", aspect="auto", color_continuous_scale=ui.SKALA_DIVERGEN, zmin=-2, zmax=2,
                        title="Z-score per polutan (positif = di atas rata-rata 5 stasiun)", labels={"x": "", "y": "", "color": "Z"})
        with b:
            ui.tampilkan(fig, 330, legenda_bawah=False)
        ui.catatan("Z-score membuat polutan dengan skala berbeda (misalnya CO dan PM2.5) setara sebelum dianalisis. "
                   "Nilai positif berarti stasiun tersebut lebih tinggi dari rata-rata kelima stasiun untuk polutan itu.", "Mengapa distandardisasi?")

    # ---------------------------------------------------------- 2 PCA
    with t2:
        kk = st.radio("Jumlah klaster (K-means pada titik PCA 2D)", [2, 3, 4], index=1, horizontal=True)
        koord = pd.DataFrame(c["koordinat"]).T.reset_index().rename(columns={"index": "stasiun"})
        koord["klaster"] = [c["skenario_kmeans"][s][f"k{kk}"] for s in koord["stasiun"]]
        koord["Klaster"] = koord["klaster"].map(lambda v: f"Klaster {v}")
        peta = {f"Klaster {i}": col for i, col in ui.WARNA_KLASTER[kk].items()}
        a, b = st.columns([1.35, 1])
        fig = px.scatter(koord, x="PC1", y="PC2", color="Klaster", text="stasiun", color_discrete_map=peta,
                         category_orders={"Klaster": sorted(peta)}, title=f"Persebaran stasiun pada ruang PCA 2D (k = {kk})",
                         labels={"PC1": f"PC1 ({A.fmt(var['persen'][0] * 100, 1)}% varians)", "PC2": f"PC2 ({A.fmt(var['persen'][1] * 100, 1)}% varians)"})
        fig.update_traces(marker=dict(size=18, line=dict(width=2, color=ui.NAVY)), textposition="top center")
        fig.add_hline(y=0, line_color=ui.GARIS)
        fig.add_vline(x=0, line_color=ui.GARIS)
        with a:
            ui.tampilkan(fig, 440)
        load = pd.DataFrame(c["loading"]).T[POL].rename(columns=_label)
        fig = px.imshow(load, text_auto=".2f", aspect="auto", color_continuous_scale=ui.SKALA_DIVERGEN, zmin=-0.7, zmax=0.7,
                        title="Loading PCA (bobot polutan)", labels={"x": "", "y": "", "color": "Loading"})
        with b:
            ui.tampilkan(fig, 220, legenda_bawah=False)
            vv = pd.DataFrame({"Komponen": ["PC1", "PC2"], "Varians": c["varians"]["nilai"], "% dijelaskan": [x * 100 for x in var["persen"]]})
            st.dataframe(vv.round(2), use_container_width=True, hide_index=True)
            st.caption(f"Kumulatif {A.fmt(var['kumulatif'] * 100, 1)}%: {A.fmt(100 - var['kumulatif'] * 100, 1)}% informasi tidak terwakili dua sumbu.")
        sk = pd.DataFrame({"k": ["k = 2", "k = 3", "k = 4"], "WCSS": [c["wcss"][x] for x in ["k2", "k3", "k4"]],
                           "Silhouette": [sil2[x] for x in ["k2", "k3", "k4"]]})
        a, b = st.columns(2)
        fig = px.bar(sk, x="k", y="Silhouette", text=sk["Silhouette"].round(2), title="Silhouette per jumlah klaster (PCA 2D)",
                     labels={"k": ""})
        fig.update_traces(marker_color=[ui.CYAN, ui.SOLAR, ui.CYAN])
        with a:
            ui.tampilkan(fig, 300, legenda_bawah=False)
        tab = koord[["stasiun", "PC1", "PC2", "klaster"]].rename(columns={"stasiun": "Stasiun", "klaster": f"Klaster (k={kk})"})
        b.markdown("**Koordinat dan keanggotaan klaster**")
        b.dataframe(tab.round(3), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------- 3 dendrogram
    with t3:
        a, b = st.columns(2)
        ruang = a.radio("Ruang data", ["PCA 2D", "6 polutan penuh (6D)"], horizontal=True)
        kp = b.radio("Potong dendrogram menjadi", [2, 3, 4], index=1, horizontal=True, format_func=lambda v: f"{v} klaster")
        d = c["dendrogram_2d"] if ruang == "PCA 2D" else c["dendrogram_6d"]
        fig, ket = _dendrogram(d, kp, f"Dendrogram Ward: {ruang}")
        ui.tampilkan(fig, 460, legenda_bawah=False)
        if ket:
            ui.catatan(ket, f"Hasil potongan {kp} klaster ({ruang})", penting=True)
        langkah = pd.DataFrame(d["langkah"])
        langkah = langkah[["langkah", "gabung", "tinggi"]].rename(columns={"langkah": "Langkah", "gabung": "Penggabungan", "tinggi": "Tinggi penggabungan"})
        st.dataframe(langkah.round(3), use_container_width=True, hide_index=True)
        st.caption("Makin rendah titik penggabungan, makin mirip dua stasiun. Tinggi pada 6D memakai simpangan baku populasi, pada 2D simpangan baku sampel "
                   "(selisih skala √(5/4); struktur pohon tidak berubah).")

    # ---------------------------------------------------------- 4 karakteristik
    with t4:
        pilih = st.radio("Hasil klaster (k = 3)", ["PCA 2D (K-means / Ward 2D)", "6 polutan (Ward 6D)"], horizontal=True)
        prof = c["profil_2d_k3"] if pilih.startswith("PCA") else c["perbandingan"]["profil_6d_k3"]
        pf = pd.DataFrame([{"Klaster": f"Klaster {x['klaster']}", **{_label(p_): x["z"][p_] for p_ in POL}} for x in prof]).set_index("Klaster")
        fig = px.imshow(pf, text_auto=".2f", aspect="auto", color_continuous_scale=ui.SKALA_DIVERGEN, zmin=-2, zmax=2,
                        title="Profil klaster: rata-rata Z-score tiap polutan", labels={"x": "", "y": "", "color": "Z"})
        ui.tampilkan(fig, 280, legenda_bawah=False)
        for x in prof:
            anggota = x["anggota"].replace(" ", ", ")
            ui.catatan(f"Anggota: <b>{anggota}</b><br>Karakter polutan {_deskripsi(x['z'])}.", f"Klaster {x['klaster']}",
                       penting=(x["klaster"] == 3))
        if pilih.startswith("PCA"):
            ui.catatan("'PM10 tinggi' pada Klaster 1 berasal dari DKI4 saja; PM10 DKI1 justru sedikit di bawah rata-rata (z = −0,10), "
                       "sedangkan PM2.5 DKI1 di atas rata-rata (z = +0,27). Karena itu Klaster 1 lebih tepat dibaca sebagai 'CO relatif tinggi'.",
                       "Catatan dari hasil Excel")
        with st.expander("Interpretasi dan catatan langsung dari file Excel"):
            for t in c["catatan_excel_2d"] + c["perbandingan"]["kesimpulan_excel"]:
                st.markdown(f"- {t}")

    # ---------------------------------------------------------- 5 perbandingan
    with t5:
        pb = c["perbandingan"]
        ag = pd.DataFrame(pb["keanggotaan"]).rename(columns={
            "stasiun": "Stasiun", "kmeans2d_k3": "K-means 2D (k=3)", "ward2d_k3": "Ward 2D (k=3)",
            "ward6d_k3": "Ward 6D (k=3)", "ward6d_k2": "Ward 6D (k=2)"})
        a, b = st.columns([1.2, 1])
        a.markdown("**Keanggotaan klaster** (nomor hanya label; yang dibandingkan adalah siapa yang sekelompok)")
        a.dataframe(ag, use_container_width=True, hide_index=True)
        b.markdown("**Apakah pasangan stasiun sekelompok? (k = 3)**")
        b.dataframe(pd.DataFrame(pb["pasangan"]).rename(columns={"pasangan": "Pasangan", "kmeans2d": "K-means 2D", "ward2d": "Ward 2D", "ward6d": "Ward 6D"}),
                    use_container_width=True, hide_index=True)
        sl = pd.DataFrame(pb["silhouette"]).melt(id_vars="k", var_name="metode", value_name="silhouette")
        sl["metode"] = sl["metode"].map({"kmeans2d": "K-means PCA 2D", "ward6d": "Ward 6D"})
        sl["k"] = sl["k"].map(lambda v: f"k = {v}")
        fig = px.bar(sl, x="k", y="silhouette", color="metode", barmode="group", text=sl["silhouette"].round(2),
                     color_discrete_map={"K-means PCA 2D": ui.OCEAN, "Ward 6D": ui.SOLAR},
                     title="Silhouette: PCA 2D vs 6 polutan", labels={"k": "", "silhouette": "Silhouette", "metode": ""})
        fig.add_hline(y=0.25, line_dash="dot", line_color=ui.NAVY, annotation_text="batas 0,25")
        a, b = st.columns([1, 1.1])
        with a:
            ui.tampilkan(fig, 360)
        th = pd.DataFrame(pb["tinggi"])[["langkah", "gabung2d", "tinggi2d", "gabung6d", "tinggi6d"]].rename(columns={
            "langkah": "Langkah", "gabung2d": "Penggabungan (2D)", "tinggi2d": "Tinggi 2D", "gabung6d": "Penggabungan (6D)", "tinggi6d": "Tinggi 6D"})
        b.markdown("**Urutan penggabungan Ward**")
        b.dataframe(th.round(3), use_container_width=True, hide_index=True)
        ui.catatan(
            "<b>Konsisten di semua metode:</b> DKI5 Kebun Jeruk terpisah dari empat stasiun lain (O₃ dan PM2.5 tertinggi, PM10 terendah).<br>"
            "<b>Tidak konsisten:</b> pada PCA 2D, k = 3 menghasilkan {DKI1, DKI4}, {DKI2, DKI3}, {DKI5}; pada 6D menghasilkan {DKI1, DKI2, DKI4}, {DKI3}, {DKI5}. "
            f"PCA 2D membuang {A.fmt(100 - var['kumulatif'] * 100, 1)}% varians, sehingga jarak antarstasiun berubah. Analisis utama sebaiknya merujuk 6D; PCA cocok untuk visualisasi.",
            "Interpretasi perbandingan", penting=True)
        ui.catatan(f"Silhouette k = 3 hanya {A.fmt(sil2['k3'], 2)} (2D) dan {A.fmt(sil6['k3'], 2)} (6D), dan jumlah stasiun hanya 5. "
                   "Hasil bersifat eksploratif/deskriptif, bukan bukti statistik adanya kelompok yang tegas.", "Keterbatasan")
