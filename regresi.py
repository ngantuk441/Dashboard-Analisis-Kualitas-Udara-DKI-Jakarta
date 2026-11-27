import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analisis as A
import ui

ASSET = A.DATA.parent / "assets"
NAMA = {"(Intercept)": "Konstanta (intersep)", **A.LABEL_CUACA}
URUT_TAMPIL = ["suhu_rata2", "kelembaban_rata2", "kecepatan_angin_rata2", "curah_hujan_total", "radiasi_matahari_rata2"]


def tampil(k):
    reg, da = k.reg, k.da
    rg = reg["ringkasan"]
    ui.header("Kausalitas / Regresi Linear", "Pengaruh simultan suhu, kelembapan, angin, hujan, dan radiasi terhadap nilai ISPU (hasil JASP)")
    st.markdown(
        "Regresi linear berganda menguji seberapa besar masing-masing variabel cuaca berhubungan dengan ISPU **ketika variabel lain dianggap tetap**. "
        "Variabel dependen: nilai ISPU. Variabel independen: suhu, kelembapan, kecepatan angin, curah hujan, dan radiasi matahari."
    )
    ui.kpi([
        ("R² (R-squared)", A.fmt(rg["R2"], 4), f"{A.fmt(rg['R2'] * 100, 1)}% variasi ISPU dijelaskan model", True),
        ("Adjusted R²", A.fmt(rg["R2_adj"], 4), "setelah memperhitungkan jumlah prediktor"),
        ("R (korelasi berganda)", A.fmt(rg["R"], 3), "korelasi nilai prediksi dan aktual"),
        ("Uji F model", A.fmt(rg["F"], 2), f"df = {rg['df1']}; {A.fmt(rg['df2'], 0)} · p {A.fmt_p(rg['p'])}"),
        ("Observasi (N)", A.fmt(reg["n"], 0), "data lengkap (listwise)"),
    ])

    t1, t2, t3, t4 = st.tabs(["Ringkasan model dan ANOVA", "Koefisien regresi", "Interpretasi pengaruh", "Diagnostik dan simulasi"])

    # ---------------------------------------------------------- ringkasan & anova
    with t1:
        a, b = st.columns(2)
        ms = pd.DataFrame({"Ukuran": ["R", "R²", "Adjusted R²", "RMSE (galat baku)", "AIC", "BIC"],
                           "Model 1": [rg["R"], rg["R2"], rg["R2_adj"], rg["RMSE"], rg["AIC"], rg["BIC"]]})
        a.markdown("**Model Summary**")
        a.dataframe(ms.assign(**{"Model 1": ms["Model 1"].map(lambda x: A.fmt(x, 3))}), use_container_width=True, hide_index=True)
        an = pd.DataFrame(reg["anova"])
        an = an.rename(columns={"sumber": "Sumber", "SS": "Jumlah kuadrat", "df": "df", "MS": "Rata-rata kuadrat", "F": "F", "p": "p"})
        for c in ["Jumlah kuadrat", "Rata-rata kuadrat", "F"]:
            an[c] = an[c].map(lambda x: "" if pd.isna(x) else A.fmt(x, 2))
        an["df"] = an["df"].map(lambda x: A.fmt(x, 0))
        an["p"] = an["p"].map(lambda x: "" if pd.isna(x) else A.fmt_p(x))
        b.markdown("**ANOVA**")
        b.dataframe(an, use_container_width=True, hide_index=True)
        ssr, sse = reg["anova"][0]["SS"], reg["anova"][1]["SS"]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=[""], x=[ssr / (ssr + sse) * 100], orientation="h", name="Dijelaskan model", marker_color=ui.OCEAN,
                             text=[f"{A.fmt(ssr / (ssr + sse) * 100, 1)}%"], textposition="inside"))
        fig.add_trace(go.Bar(y=[""], x=[sse / (ssr + sse) * 100], orientation="h", name="Tidak dijelaskan model", marker_color=ui.CYAN,
                             text=[f"{A.fmt(sse / (ssr + sse) * 100, 1)}%"], textposition="inside"))
        fig.update_layout(barmode="stack", title="Pembagian variasi ISPU (berdasarkan jumlah kuadrat ANOVA)")
        fig.update_xaxes(title="% dari total variasi", range=[0, 100])
        ui.tampilkan(fig, 190)
        ui.catatan(
            f"Uji F signifikan (F = {A.fmt(rg['F'], 2)}, p {A.fmt_p(rg['p'])}): sedikitnya satu variabel cuaca berhubungan nyata dengan ISPU. "
            f"Tetapi R² hanya {A.fmt(rg['R2'], 3)}, jadi sekitar {A.fmt((1 - rg['R2']) * 100, 1)}% variasi ISPU berasal dari hal di luar kelima variabel ini.",
            "Kesimpulan model", penting=True)

    # ---------------------------------------------------------- koefisien
    ko = {x["variabel"]: x for x in reg["koefisien"]}
    with t2:
        rows = []
        for v in ["(Intercept)"] + URUT_TAMPIL:
            x = ko[v]
            rows.append({"Variabel": NAMA[v], "B (tak terstandar)": x["B"], "Galat baku": x["SE"],
                         "Beta (terstandar)": x["beta"], "t": x["t"], "p-value": x["p"], "Signif.": A.tanda_p(x["p"]),
                         "CI 95% bawah": x["ci_bawah"], "CI 95% atas": x["ci_atas"], "VIF": x["VIF"]})
        tb = pd.DataFrame(rows)
        tampil_tb = tb.copy()
        for c in ["B (tak terstandar)", "Galat baku", "Beta (terstandar)", "t", "CI 95% bawah", "CI 95% atas", "VIF"]:
            tampil_tb[c] = tb[c].map(lambda x: "" if pd.isna(x) else A.fmt(x, 3))
        tampil_tb["p-value"] = tb["p-value"].map(A.fmt_p)
        st.dataframe(tampil_tb, use_container_width=True, hide_index=True)
        st.caption("Signif.: *** p < 0,001; ** p < 0,01; * p < 0,05; n.s. = tidak signifikan. VIF di bawah 5 berarti multikolinearitas masih terkendali.")
        a, b = st.columns(2)
        bt = pd.DataFrame({"v": URUT_TAMPIL, "beta": [ko[v]["beta"] for v in URUT_TAMPIL],
                           "sig": [ko[v]["p"] < 0.05 for v in URUT_TAMPIL]})
        bt["label"] = bt["v"].map(A.LABEL_PENDEK)
        bt = bt.sort_values("beta")
        fig = go.Figure(go.Bar(x=bt["beta"], y=bt["label"], orientation="h",
                               marker_color=[ui.OCEAN if s else ui.NETRAL for s in bt["sig"]],
                               text=[f"{b_:+.3f}".replace(".", ",") for b_ in bt["beta"]], textposition="outside",
                               hovertemplate="%{y}: beta = %{x:.3f}<extra></extra>"))
        fig.update_layout(title="Koefisien terstandar (Beta): kekuatan relatif pengaruh")
        fig.update_xaxes(range=[-0.45, 0.45], title="Beta (biru = signifikan, abu-abu = tidak signifikan)")
        with a:
            ui.tampilkan(fig, 360, legenda_bawah=False)
        ci = pd.DataFrame({"label": [A.LABEL_PENDEK[v] for v in URUT_TAMPIL], "p": [ko[v]["p"] for v in URUT_TAMPIL],
                           "t": [ko[v]["t"] for v in URUT_TAMPIL]})
        ci = ci.sort_values("t")
        fig = go.Figure(go.Bar(x=ci["t"], y=ci["label"], orientation="h",
                               marker_color=[ui.SOLAR if abs(t) >= 1.96 else ui.NETRAL for t in ci["t"]],
                               text=[f"t = {t:+.2f}".replace(".", ",") for t in ci["t"]], textposition="outside"))
        fig.add_vline(x=1.96, line_dash="dot", line_color=ui.NAVY)
        fig.add_vline(x=-1.96, line_dash="dot", line_color=ui.NAVY)
        fig.update_layout(title="Uji signifikansi per variabel (nilai t)")
        fig.update_xaxes(range=[-11, 12], title="Nilai t (garis putus-putus = ±1,96; kuning = signifikan pada 5%)")
        with b:
            ui.tampilkan(fig, 360, legenda_bawah=False)

    # ---------------------------------------------------------- interpretasi
    with t3:
        s = ko["suhu_rata2"]
        ui.bagian("Arti setiap variabel terhadap nilai ISPU")
        arti = {
            "suhu_rata2": "per kenaikan 1 °C",
            "kelembaban_rata2": "per kenaikan 1 poin persen",
            "kecepatan_angin_rata2": "per kenaikan 1 m/s",
            "curah_hujan_total": "per kenaikan 1 mm",
            "radiasi_matahari_rata2": "per kenaikan 1 W/m²",
        }
        for v in sorted(URUT_TAMPIL, key=lambda x: -abs(ko[x]["beta"])):
            x = ko[v]
            sig = x["p"] < 0.05
            naik = "naik" if x["B"] > 0 else "turun"
            status = (f"signifikan (p {A.fmt_p(x['p'])})" if sig else f"<b>tidak signifikan</b> (p = {A.fmt(x['p'], 3)})")
            if sig:
                isi = (f"ISPU rata-rata <b>{naik} {A.fmt(abs(x['B']), 3)}</b> {arti[v]}, dengan variabel lain tetap. "
                       f"Pengaruh {status}; Beta = {A.fmt(x['beta'], 3)}.")
            else:
                isi = (f"Koefisien {A.fmt(x['B'], 3)} {arti[v]}, tetapi {status}: belum ada bukti pengaruh setelah variabel lain diperhitungkan. "
                       f"CI 95% [{A.fmt(x['ci_bawah'], 3)}; {A.fmt(x['ci_atas'], 3)}] mencakup nol.")
            ui.catatan(isi, A.LABEL_CUACA[v], penting=(v == "suhu_rata2"))
        n_sig = sum(ko[v]["p"] < 0.05 for v in URUT_TAMPIL)
        ui.catatan(
            f"{n_sig} dari 5 variabel signifikan pada taraf 5%. Suhu memiliki pengaruh terstandar terbesar (Beta = {A.fmt(s['beta'], 3)}). "
            f"Perhatikan bahwa kelembapan dan suhu saling berkaitan erat (lihat halaman Korelasi), sehingga VIF keduanya mendekati 3 dan tanda koefisiennya perlu dibaca hati-hati. "
            f"Curah hujan berkorelasi negatif dengan ISPU secara tunggal, tetapi tidak signifikan di dalam model berganda.",
            "Kesimpulan hasil regresi", penting=True)
        angin = da["kecepatan_angin_rata2"]
        ui.catatan(
            "Regresi menunjukkan <b>asosiasi</b> setelah mengendalikan variabel lain, bukan bukti sebab-akibat mutlak. "
            "Model ini observasional, hanya memuat lima variabel cuaca, dan R² yang rendah menandakan faktor penting lain (misalnya sumber emisi) tidak ikut dimodelkan.<br>"
            f"<i>Catatan kualitas data:</i> kecepatan angin pada dataset memiliki nilai ekstrem (maksimum {A.fmt(angin.max(), 1)} m/s, simpangan baku {A.fmt(angin.std(), 1)}). "
            "Nilai seperti itu tidak wajar untuk rata-rata harian dan dapat memengaruhi koefisien angin; hasil JASP dipakai apa adanya.",
            "Batasan metode")

    # ---------------------------------------------------------- diagnostik & simulasi
    with t4:
        a, b = st.columns([1, 1])
        with a:
            st.markdown("**Q-Q plot residual (dari JASP)**")
            st.image(str(ASSET / "qq_residual_jasp.png"), use_container_width=True)
            st.caption("Titik di tengah mengikuti garis, tetapi ekor kanan melengkung ke atas: ada hari dengan ISPU jauh lebih tinggi dari perkiraan model, sehingga residual tidak sepenuhnya normal.")
        with b:
            st.markdown("**Simulasi ISPU dari koefisien JASP**")
            st.caption("Hanya menghitung ISPU = konstanta + Σ(B × nilai) dengan koefisien di atas. Karena R² rendah, hasilnya perkiraan kasar, bukan prediksi andal.")
            nilai = {}
            for v in URUT_TAMPIL:
                lo, hi = float(da[v].quantile(0.05)), float(da[v].quantile(0.95))
                nilai[v] = st.slider(A.LABEL_CUACA[v], round(lo, 1), round(hi, 1), round(float(da[v].median()), 1), key=f"sim_{v}")
            hasil = A.prediksi_dari_koefisien(reg, nilai)
            ui.catatan(f"Perkiraan ISPU: <b>{A.fmt(hasil, 1)}</b> (kategori {A.kategori_ispu(hasil).title()}). "
                       f"Galat baku model (RMSE) ±{A.fmt(rg['RMSE'], 1)}.", "Hasil simulasi", penting=True)
