"""Palet warna, gaya CSS, dan komponen tampilan yang dipakai semua halaman."""
import html

import streamlit as st

# ------------------------------------------------------------------ palet (sesuai gambar referensi)
OCEAN = "#015382"   # Deep Ocean Blue : sidebar, header, identitas utama
CYAN = "#71CDF4"    # Sky Cyan        : aksen, grafik
SOLAR = "#FFD202"   # Solar Yellow    : highlight informasi penting
SUN = "#FFE454"     # Soft Sunshine   : aksen tambahan
CLOUD = "#F5F8FA"   # Cloud White     : latar utama
NAVY = "#163247"    # Midnight Navy   : teks dan heading
GARIS = "#DCE6EE"   # turunan Cloud White untuk garis grid
REDAM = "#5B7285"   # turunan Midnight Navy untuk teks sekunder
NETRAL = "#B8C7D3"

WARNA_KAT = {"BAIK": CYAN, "SEDANG": OCEAN, "TIDAK SEHAT": SOLAR, "SANGAT TIDAK SEHAT": NAVY,
             "TIDAK DAPAT DIKLASIFIKASI": NETRAL}
# DKI5 memakai Solar Yellow di semua halaman karena stasiun ini paling menonjol di hampir semua analisis
WARNA_STASIUN = {"DKI1 Bundaran HI": OCEAN, "DKI2 Kelapa Gading": CYAN, "DKI3 Jagakarsa": NAVY,
                 "DKI4 Lubang Buaya": SUN, "DKI5 Kebun Jeruk": SOLAR}
WARNA_KLASTER = {2: {1: OCEAN, 2: SOLAR},
                 3: {1: OCEAN, 2: CYAN, 3: SOLAR},
                 4: {1: OCEAN, 2: CYAN, 3: NAVY, 4: SOLAR}}
SKALA_URUT = [[0, CLOUD], [0.5, CYAN], [1, OCEAN]]
SKALA_DIVERGEN = [[0, OCEAN], [0.5, CLOUD], [1, SOLAR]]

CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: "Source Sans Pro", "Segoe UI", sans-serif; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }}
h1, h2, h3, h4 {{ color: {NAVY}; letter-spacing: -0.01em; }}
h3 {{ margin-top: 1.4rem; }}
[data-testid="stSidebar"] {{ background: {OCEAN}; }}
[data-testid="stSidebar"] * {{ color: #F5F8FA; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(113,205,244,.35); }}
[data-testid="stSidebar"] .sb-judul {{ font-size: 1.05rem; font-weight: 700; line-height: 1.25; color: #fff; }}
[data-testid="stSidebar"] .sb-sub {{ font-size: .78rem; color: {CYAN}; margin-top: 2px; }}
[data-testid="stSidebar"] .sb-label {{ font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: {CYAN}; margin: 6px 0 2px; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] input {{ color: {NAVY} !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] span {{ color: {NAVY} !important; }}
[data-testid="stSidebar"] [data-baseweb="tag"] {{ background: {CYAN}; }}
[data-testid="stSidebar"] [data-baseweb="tag"] span {{ color: {NAVY} !important; }}
.hdr {{ background: {OCEAN}; border-bottom: 5px solid {SOLAR}; border-radius: 10px; padding: 26px 32px; margin-bottom: 18px; }}
.hdr .judul {{ color: #fff; font-size: 1.85rem; font-weight: 700; line-height: 1.2; margin: 0; }}
.hdr .sub {{ color: {CYAN}; font-size: 1rem; margin-top: 8px; }}
.kpi-baris {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 6px 0 14px; }}
.kpi {{ background: #fff; border: 1px solid {GARIS}; border-left: 5px solid {OCEAN}; border-radius: 8px; padding: 12px 16px; }}
.kpi.sorot {{ border-left-color: {SOLAR}; }}
.kpi .k-label {{ font-size: .78rem; color: {REDAM}; }}
.kpi .k-nilai {{ font-size: 1.65rem; font-weight: 700; color: {NAVY}; line-height: 1.25; }}
.kpi .k-ket {{ font-size: .78rem; color: {REDAM}; }}
.kartu {{ background: #fff; border: 1px solid {GARIS}; border-top: 4px solid {OCEAN}; border-radius: 8px; padding: 14px 18px; height: 100%; }}
.kartu h4 {{ margin: 0 0 6px; font-size: 1.02rem; }}
.kartu p {{ margin: 0 0 6px; font-size: .92rem; color: {NAVY}; }}
.kartu .angka {{ font-size: 1.5rem; font-weight: 700; color: {OCEAN}; }}
.catatan {{ background: #fff; border: 1px solid {GARIS}; border-left: 5px solid {CYAN}; border-radius: 6px; padding: 12px 16px; margin: 10px 0; color: {NAVY}; }}
.catatan.penting {{ border-left-color: {SOLAR}; background: #FFFDF0; }}
.catatan b.t {{ display: block; margin-bottom: 3px; }}
.bagian {{ color: {REDAM}; font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; margin: 22px 0 -6px; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color: {OCEAN}; font-weight: 600; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background-color: {SOLAR}; }}
@media (max-width: 700px) {{ .hdr {{ padding: 18px; }} .hdr .judul {{ font-size: 1.35rem; }} .kpi .k-nilai {{ font-size: 1.35rem; }} }}
</style>
"""


def pasang_tema():
    st.markdown(CSS, unsafe_allow_html=True)


def header(judul, sub):
    st.markdown(f'<div class="hdr"><div class="judul">{html.escape(judul)}</div>'
                f'<div class="sub">{html.escape(sub)}</div></div>', unsafe_allow_html=True)


def bagian(teks):
    st.markdown(f'<div class="bagian">{html.escape(teks)}</div>', unsafe_allow_html=True)


def kpi(daftar):
    """daftar: [(label, nilai, keterangan, sorot?)]"""
    kartu = ""
    for item in daftar:
        label, nilai, ket = item[:3]
        sorot = " sorot" if len(item) > 3 and item[3] else ""
        kartu += (f'<div class="kpi{sorot}"><div class="k-label">{html.escape(str(label))}</div>'
                  f'<div class="k-nilai">{html.escape(str(nilai))}</div>'
                  f'<div class="k-ket">{html.escape(str(ket))}</div></div>')
    st.markdown(f'<div class="kpi-baris">{kartu}</div>', unsafe_allow_html=True)


def kartu(judul, angka, isi):
    return (f'<div class="kartu"><h4>{html.escape(judul)}</h4><div class="angka">{html.escape(angka)}</div>'
            f'<p>{isi}</p></div>')


def catatan(isi, judul=None, penting=False):
    """isi boleh mengandung HTML sederhana (<b>, <br>)."""
    t = f'<b class="t">{html.escape(judul)}</b>' if judul else ""
    st.markdown(f'<div class="catatan{" penting" if penting else ""}">{t}{isi}</div>', unsafe_allow_html=True)


def gaya(fig, tinggi=420, legenda_bawah=True):
    fig.update_layout(
        height=tinggi, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
        font=dict(color=NAVY, size=13), margin=dict(l=10, r=10, t=55, b=10),
        title=dict(font=dict(size=15, color=NAVY), x=0.01),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=NAVY, bordercolor=GARIS),
    )
    if legenda_bawah:
        fig.update_layout(legend=dict(orientation="h", y=-0.2, title_text=""))
    fig.update_xaxes(gridcolor=GARIS, zeroline=False, linecolor=GARIS)
    fig.update_yaxes(gridcolor=GARIS, zeroline=False, linecolor=GARIS)
    return fig


def tampilkan(fig, tinggi=420, **kw):
    st.plotly_chart(gaya(fig, tinggi, **kw), use_container_width=True)


JUDUL = "DASHBOARD ANALISIS KUALITAS UDARA DKI JAKARTA"
SUBJUDUL = "Visualisasi dan Analisis Data Menggunakan Metode Klasifikasi, Korelasi, Regresi, dan Clustering."
