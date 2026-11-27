import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analisis as A
import ui

VAR = A.VAR_KORELASI


def tampil(k):
    df, da, filter_aktif = k.df, k.da, k.filter_aktif
    ui.header("Korelasi Cuaca dan ISPU", "Hubungan antarvariabel meteorologi dan nilai ISPU (korelasi Pearson, acuan Tableau)")
    st.markdown(
        "Korelasi mengukur seberapa kuat dan ke arah mana dua variabel bergerak bersama (−1 sampai +1). "
        "Variabel yang dianalisis: suhu, kelembapan, kecepatan angin, curah hujan, radiasi matahari, dan nilai ISPU."
    )
    c1, c2 = st.columns([1, 2])
    metode = c1.radio("Metode", ["Pearson", "Spearman"], horizontal=True,
                      help="Pearson adalah metode pada file Tableau. Spearman (berbasis peringkat) disediakan sebagai pembanding.")
    sumber = df if filter_aktif else da
    r, p, n = A.matriks_korelasi(sumber, metode.lower())
    if filter_aktif:
        c2.info("Filter sidebar aktif: koefisien dihitung ulang dari data terfilter, sehingga bisa berbeda dari file Tableau.")
    else:
        c2.success("Data lengkap (tanpa filter): koefisien Pearson setara dengan file Tableau.")
    if len(sumber) < 30:
        st.warning("Data terlalu sedikit untuk menghitung korelasi. Longgarkan filter di sidebar.")
        return

    r_isp = r["nilai_ispu"].drop("nilai_ispu")
    p_isp = p["nilai_ispu"].drop("nilai_ispu")
    n_isp = n["nilai_ispu"].drop("nilai_ispu")
    top = r_isp.abs().idxmax()
    ui.kpi([
        ("Hubungan terkuat dengan ISPU", A.LABEL_PENDEK[top], f"{A.arah(r_isp[top])}, {A.kekuatan(r_isp[top])}", True),
        ("Koefisien terkuat", f"{r_isp[top]:+.3f}".replace(".", ","), f"{metode}"),
        ("Jumlah observasi", A.fmt(len(sumber), 0), f"pasangan data ISPU–cuaca {A.fmt(n_isp.min(), 0)} – {A.fmt(n_isp.max(), 0)}"),
    ])

    # ---------------------------------------------------------- heatmap + bar
    a, b = st.columns([1.15, 1])
    nama = [A.LABEL_PENDEK[v] for v in VAR]
    fig = go.Figure(go.Heatmap(z=r.values, x=nama, y=nama, zmin=-1, zmax=1, colorscale=ui.SKALA_DIVERGEN,
                               text=np.round(r.values, 2), texttemplate="%{text}", textfont=dict(color=ui.NAVY),
                               colorbar=dict(title="r", thickness=12),
                               hovertemplate="%{y} × %{x}<br>r = %{z:.3f}<extra></extra>"))
    fig.update_layout(title=f"Heatmap korelasi {metode}")
    fig.update_yaxes(autorange="reversed")
    with a:
        ui.tampilkan(fig, 430, legenda_bawah=False)
    ur = r_isp.sort_values()
    fig = go.Figure(go.Bar(x=ur.values, y=[A.LABEL_PENDEK[v] for v in ur.index], orientation="h",
                           marker_color=[ui.SOLAR if v > 0 else ui.OCEAN for v in ur.values],
                           text=[f"{v:+.2f}".replace(".", ",") for v in ur.values], textposition="outside",
                           hovertemplate="%{y}: r = %{x:.3f}<extra></extra>"))
    fig.update_layout(title="Korelasi tiap variabel cuaca dengan ISPU")
    fig.update_xaxes(range=[-0.6, 0.6], title="Koefisien korelasi")
    with b:
        ui.tampilkan(fig, 430, legenda_bawah=False)

    # ---------------------------------------------------------- tabel koefisien
    ui.bagian("Koefisien, arah, dan kekuatan hubungan")
    tabel = pd.DataFrame({
        "Variabel": [A.LABEL_CUACA[v] for v in r_isp.index],
        "Koefisien (r)": r_isp.round(3).values,
        "Arah": [A.arah(x) for x in r_isp.values],
        "Kekuatan": [A.kekuatan(x) for x in r_isp.values],
        "p-value": [A.fmt_p(x) for x in p_isp.values],
        "Jumlah pasangan": n_isp.values,
    }).sort_values("Koefisien (r)", key=lambda s: s.abs(), ascending=False)
    st.dataframe(tabel, use_container_width=True, hide_index=True)
    st.caption("Kriteria kekuatan (Guilford): |r| < 0,2 sangat lemah; 0,2–0,39 lemah; 0,4–0,59 sedang; 0,6–0,79 kuat; ≥ 0,8 sangat kuat. "
               "Arah positif = naik bersama ISPU; negatif = berlawanan.")
    with st.expander("Matriks korelasi lengkap (semua pasangan variabel)"):
        m = r.copy()
        m.index = nama
        m.columns = nama
        st.dataframe(m.round(3), use_container_width=True)
        mn = n.copy()
        mn.index = nama
        mn.columns = nama
        st.caption("Jumlah pasangan data per sel:")
        st.dataframe(mn, use_container_width=True)

    # ---------------------------------------------------------- scatter
    ui.bagian("Scatter plot antarvariabel")
    s1, s2, s3 = st.columns([1, 1, 1])
    x = s1.selectbox("Sumbu X", VAR, index=0, format_func=lambda v: A.LABEL_VAR[v])
    y = s2.selectbox("Sumbu Y", VAR, index=5, format_func=lambda v: A.LABEL_VAR[v])
    warna = s3.checkbox("Warnai per stasiun", value=True)
    if x == y:
        st.info("Pilih dua variabel yang berbeda.")
    else:
        s = sumber.dropna(subset=[x, y])
        fig = px.scatter(s, x=x, y=y, color="stasiun" if warna else None, color_discrete_map=ui.WARNA_STASIUN,
                         opacity=0.55, hover_data={"tanggal": "|%d %b %Y"},
                         labels={x: A.LABEL_VAR[x], y: A.LABEL_VAR[y], "stasiun": "Stasiun"},
                         title=f"{A.LABEL_VAR[y]} vs {A.LABEL_VAR[x]}")
        if s[x].nunique() > 1:
            b1, b0 = np.polyfit(s[x], s[y], 1)
            xs = np.linspace(s[x].min(), s[x].max(), 50)
            fig.add_trace(go.Scatter(x=xs, y=b1 * xs + b0, mode="lines", name="Garis tren linear",
                                     line=dict(color=ui.NAVY, width=3)))
        rr = r.loc[x, y]
        fig.add_annotation(text=f"r = {rr:+.3f}".replace(".", ",") + f" ({A.kekuatan(rr)})", xref="paper", yref="paper",
                           x=0.99, y=0.99, showarrow=False, bgcolor="#FFFFFF", bordercolor=ui.GARIS, font=dict(color=ui.NAVY))
        ui.tampilkan(fig, 460)

    # ---------------------------------------------------------- interpretasi
    ui.bagian("Interpretasi")
    baris = []
    for v in r_isp.abs().sort_values(ascending=False).index:
        rv = r_isp[v]
        gerak = ("cenderung ikut naik saat ISPU naik" if rv > 0 else "cenderung turun saat ISPU naik")
        baris.append(f"<b>{A.LABEL_PENDEK[v]}</b>: r = {A.fmt(rv, 2)} ({A.arah(rv)}, {A.kekuatan(rv)}). Nilainya {gerak}.")
    ui.catatan("<br>".join(baris), f"Variabel terkuat: {A.LABEL_PENDEK[top]}", penting=True)
    if abs(r.loc["suhu_rata2", "kelembaban_rata2"]) >= 0.6:
        rsk = r.loc["suhu_rata2", "kelembaban_rata2"]
        ui.catatan(f"Suhu dan kelembapan saling berkorelasi {A.kekuatan(rsk)} (r = {A.fmt(rsk, 2)}). "
                   "Keduanya bergerak berlawanan, jadi pengaruhnya terhadap ISPU sulit dipisahkan. Hal ini dibahas lagi pada halaman Regresi.",
                   "Antarvariabel cuaca")
    ui.catatan("Korelasi hanya menunjukkan bahwa dua variabel bergerak bersama. Hasil ini <b>tidak</b> membuktikan bahwa suhu, "
               "kelembapan, angin, hujan, atau radiasi menyebabkan perubahan ISPU. Faktor lain seperti sumber emisi dapat memengaruhi keduanya.",
               "Korelasi bukan sebab-akibat", penting=True)
    with st.expander("Catatan sumber hasil korelasi"):
        st.markdown(
            "Acuan analisis adalah `Analtika Data korelasi kausalitas.twbx` (tabel `Korelasi_Pearson`: variabel_x, variabel_y, "
            "korelasi_pearson, n_pasangan). Tabel itu tersimpan di ekstrak Tableau (.hyper) terkompresi yang tidak dapat dibuka tanpa Tableau, "
            "sehingga koefisien Pearson dihitung ulang dari dataset yang sama (`Merged_Dataset_Utama`) dengan struktur pasangan yang sama. "
            "Silakan cocokkan dengan tampilan Tableau Anda.")
