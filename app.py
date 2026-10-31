"""Dashboard sistem rekomendasi buku Book-Crossing (Streamlit, desain neobrutalist).

Hanya memuat artefak hasil notebook di folder artifacts/, tidak melatih ulang model.
Jalankan: streamlit run app.py
"""
import json
from html import escape
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

A = Path(__file__).parent / 'artifacts'
SUKA = 7                                   # rating >= 7 dianggap "disukai" (sama dengan notebook)
INK, CANVAS, CHIP = '#000000', '#FFFDF7', '#F4EFE6'
CANARY, CYAN, CORAL, MINT, VIOLET = '#FFE600', '#00F0FF', '#FF5A36', '#05FFA1', '#B185FF'

st.set_page_config(page_title='Book-Crossing RecSys', page_icon='📚', layout='wide')

# ------------------------------------------------------------------ gaya (DESIGN.md)
st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap');
.stApp {{ background: {CANVAS}; }}
html, body, p, li, label, .stMarkdown {{ font-family: 'Space Grotesk', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; font-weight: 800 !important; letter-spacing: -0.02em; color: {INK}; }}
[data-testid="stSidebar"] {{ background: {CHIP}; border-right: 4px solid {INK}; }}
.stButton > button, [data-baseweb="select"] > div, [data-testid="stNumberInput"] input {{
  border: 3px solid {INK} !important; border-radius: 4px !important; box-shadow: 3px 3px 0 {INK}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 3px solid {INK}; }}
.stTabs [data-baseweb="tab"] {{ background: {CHIP}; border: 3px solid {INK}; border-bottom: none; padding: 6px 16px;
  font-weight: 700; border-radius: 4px 4px 0 0; }}
.stTabs [aria-selected="true"] {{ background: {CANARY} !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
.mono {{ font-family: 'JetBrains Mono', monospace; }}
.hero {{ background: {CANARY}; border: 4px solid {INK}; box-shadow: 6px 6px 0 {INK}; padding: 18px 22px; margin-bottom: 22px; }}
.hero h1 {{ margin: 0; font-size: 40px; line-height: 1.1; }}
.hero p {{ margin: 6px 0 0; font-weight: 500; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 18px; margin: 8px 0 22px; }}
.kpi {{ background: #fff; border: 4px solid {INK}; box-shadow: 4px 4px 0 {INK}; border-radius: 4px; }}
.kpi .lbl {{ font: 700 12px 'JetBrains Mono', monospace; letter-spacing: .04em; text-transform: uppercase;
  padding: 6px 10px; border-bottom: 3px solid {INK}; }}
.kpi .val {{ font: 800 32px 'JetBrains Mono', monospace; padding: 10px 10px 2px; }}
.kpi .sub {{ font-size: 12px; padding: 0 10px 10px; color: #2D2D2D; }}
.box {{ background: #fff; border: 3px solid {INK}; box-shadow: 4px 4px 0 {INK}; padding: 14px 16px; margin-bottom: 18px; }}
.sparse {{ background: repeating-linear-gradient(45deg, {CORAL} 0 14px, #ff7b5c 14px 28px); border: 4px solid {INK};
  box-shadow: 6px 6px 0 {INK}; padding: 16px 18px; margin-bottom: 22px; }}
.sparse .big {{ font: 800 40px 'JetBrains Mono', monospace; background: #fff; border: 3px solid {INK}; display: inline-block; padding: 2px 12px; }}
.sparse .calc {{ font: 700 13px 'JetBrains Mono', monospace; background: {CHIP}; border: 2px solid {INK}; display: inline-block;
  padding: 4px 8px; margin-top: 10px; }}
.badge {{ display: inline-block; border: 3px solid {INK}; border-radius: 999px; padding: 2px 10px; margin: 0 6px 6px 0;
  font: 700 12px 'JetBrains Mono', monospace; box-shadow: 2px 2px 0 {INK}; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 22px; margin-top: 18px; }}
.card {{ background: #fff; border: 4px solid {INK}; box-shadow: 6px 6px 0 {INK}; padding: 16px 14px 12px; position: relative; }}
.card .no {{ font: 800 12px 'JetBrains Mono', monospace; }}
.card .t {{ font-weight: 700; font-size: 16px; line-height: 1.25; margin: 4px 0 6px; }}
.card .a {{ font-size: 14px; color: #2D2D2D; }}
.card .pill {{ position: absolute; top: -14px; right: 10px; border: 3px solid {INK}; border-radius: 999px; padding: 1px 10px;
  font: 700 11px 'JetBrains Mono', monospace; box-shadow: 2px 2px 0 {INK}; }}
.card .why {{ font-size: 12px; background: {CHIP}; border: 2px solid {INK}; padding: 4px 8px; margin-top: 10px; }}
table.ev {{ border-collapse: collapse; border: 4px solid {INK}; width: 100%; background: #fff; margin-bottom: 18px; }}
table.ev th {{ background: #121212; color: #fff; font: 700 12px 'JetBrains Mono', monospace; text-transform: uppercase;
  border: 2px solid #fff; padding: 8px; text-align: right; }}
table.ev td {{ border: 2px solid {INK}; padding: 8px; font: 500 14px 'JetBrains Mono', monospace; text-align: right; }}
table.ev th:first-child, table.ev td:first-child {{ text-align: left; font-family: 'Space Grotesk', sans-serif; }}
table.ev tr:nth-child(even) td {{ background: {CANVAS}; }}
table.ev td.win {{ background: {MINT} !important; font-weight: 800; }}
</style>''', unsafe_allow_html=True)


# ------------------------------------------------------------------ data & model
@st.cache_data
def muat_data():
    books = pd.read_csv(A / 'books.csv', dtype={'isbn': str}).set_index('isbn')
    ratings = pd.read_csv(A / 'ratings.csv', dtype={'uid': str, 'isbn': str})
    evaluasi = pd.read_csv(A / 'evaluasi.csv', index_col=0)
    info = json.loads((A / 'ringkasan.json').read_text())
    return books, ratings, evaluasi, info


@st.cache_resource
def muat_similarity():
    z = np.load(A / 'item_sim.npz')
    return z['S'], pd.Index(z['isbn'])


books, ratings, evaluasi, info = muat_data()
S, katalog = muat_similarity()
pos = pd.Series(np.arange(len(katalog)), index=katalog)        # isbn -> nomor baris di S


def rekomendasi_dari_buku(daftar_isbn, n=10):
    """Item-Based CF: skor = jumlah similarity dengan buku-buku yang disukai."""
    idx = pos[pos.index.isin(daftar_isbn)].to_numpy()
    if len(idx) == 0:
        return pd.DataFrame(columns=['isbn', 'skor', 'alasan'])
    skor = S[:, idx].sum(axis=1)
    skor[idx] = -np.inf                                       # buku yang sudah dibaca tidak direkomendasikan
    top = np.argsort(-skor)[:n]
    alasan = katalog[idx[S[np.ix_(top, idx)].argmax(axis=1)]]  # buku yang paling berkontribusi
    return pd.DataFrame({'isbn': katalog[top], 'skor': skor[top], 'alasan': alasan})


def weighted_rating(df, q=0.9):
    g = df.groupby('isbn')['rating'].agg(v='size', R='mean')
    C, m = df['rating'].mean(), g['v'].quantile(q)
    g['WR'] = g['v'] / (g['v'] + m) * g['R'] + m / (g['v'] + m) * C
    return g.sort_values('WR', ascending=False)


# ------------------------------------------------------------------ komponen tampilan
def html(s):
    st.markdown(s, unsafe_allow_html=True)


def judul(isbn):
    return books.at[isbn, 'title'] if isbn in books.index else isbn


def kpi(label, nilai, sub='', warna=CANARY):
    return (f'<div class="kpi"><div class="lbl" style="background:{warna}">{label}</div>'
            f'<div class="val">{nilai}</div><div class="sub">{sub}</div></div>')


def kartu_buku(isbn, pill, warna_pill=MINT, alasan='', no=None):
    b = books.loc[isbn]
    tahun = '' if pd.isna(b['year']) else f' · {int(b["year"])}'
    why = f'<div class="why">karena kamu menyukai <b>{escape(judul(alasan))}</b></div>' if alasan else ''
    nomor = f'<div class="no">#{no:02d}</div>' if no else ''
    return (f'<div class="card"><span class="pill" style="background:{warna_pill}">{pill}</span>{nomor}'
            f'<div class="t">{escape(str(b["title"]))}</div><div class="a">{escape(str(b["author"]))}{tahun}</div>{why}</div>')


def grid(kartu):
    html('<div class="grid">' + ''.join(kartu) + '</div>')


def angka(x, d=0):
    """Format angka gaya Indonesia: 1.234.567 dan 7,63."""
    s = f'{x:,.{d}f}'
    return s.replace(',', '_').replace('.', ',').replace('_', '.')


def gaya(chart, tinggi=320):
    return (chart.properties(height=tinggi, background='#FFFFFF')
            .configure_view(stroke=INK, strokeWidth=3)
            .configure_axis(labelFont='Space Grotesk', titleFont='JetBrains Mono', titleFontWeight='bold',
                            domainColor=INK, domainWidth=3, tickColor=INK, gridColor='#E5E2E1', labelLimit=260)
            .configure_axisX(labelAngle=0, labelOverlap=True)       # label yang bertumpuk disembunyikan
            .configure_title(font='Space Grotesk', fontSize=16, fontWeight='bold', anchor='start')
            .configure_legend(labelFont='Space Grotesk', titleFont='JetBrains Mono', orient='top'))


def batang(data, x, y, warna, judul_grafik, horizontal=False, tinggi=320, x_judul=None, y_judul=None):
    d = pd.DataFrame(list(data.items()), columns=[x, y])
    mark = alt.Chart(d, title=judul_grafik).mark_bar(color=warna, stroke=INK, strokeWidth=2)
    if horizontal:
        enc = mark.encode(y=alt.Y(f'{x}:N', sort='-x', title=y_judul), x=alt.X(f'{y}:Q', title=x_judul),
                          tooltip=[x, alt.Tooltip(f'{y}:Q', format=',')])
    else:
        enc = mark.encode(x=alt.X(f'{x}:O', title=x_judul, sort=None), y=alt.Y(f'{y}:Q', title=y_judul),
                          tooltip=[x, alt.Tooltip(f'{y}:Q', format=',')])
    st.altair_chart(gaya(enc, tinggi), width='stretch', theme=None)


# ------------------------------------------------------------------ halaman
def halaman_ringkasan():
    html('<div class="hero"><h1>BOOK-CROSSING // RECSYS</h1>'
         '<p>Sistem rekomendasi buku dengan Item-Based Collaborative Filtering dan pendekatan <i>switching hybrid</i>.</p></div>')
    html('<div class="kpis">'
         + kpi('Buku unik', angka(info['buku']), 'setelah edisi ganda digabung', CANARY)
         + kpi('Pengguna', angka(info['user']), f'{angka(info["user_eksplisit"])} memberi rating', CYAN)
         + kpi('Rating eksplisit', angka(info['rating_eksplisit']),
               f'{angka(info["rating_implisit"] / info["rating_total"] * 100, 1)}% rating implisit (0) tidak dipakai', VIOLET)
         + kpi('Rata-rata rating', angka(info['rata_rata_rating'], 2), 'skala 1–10', MINT)
         + '</div>')

    sel = info['user_eksplisit'] * info['buku_eksplisit']
    html(f'<div class="sparse"><span class="big">{angka(info["sparsitas"] * 100, 4)}% SPARSE</span><br>'
         f'<span class="calc">{angka(info["user_eksplisit"])} pengguna × {angka(info["buku_eksplisit"])} buku → '
         f'{angka(sel)} sel, hanya {angka(info["rating_eksplisit"])} yang terisi</span></div>')

    st.subheader('Cara kerja: switching hybrid')
    c1, c2, c3 = st.columns(3)
    for kol, warna, badge, siapa, isi in [
        (c1, CYAN, 'ITEM-CF', 'Pengguna lama',
         'Punya riwayat rating. Sistem mencari buku yang mirip dengan buku yang ia sukai (rating ≥ 7).'),
        (c2, CANARY, 'WEIGHTED RATING', 'Pengguna baru',
         'Belum punya riwayat. Sistem menampilkan buku dengan weighted rating tertinggi, bisa per kelompok umur dan negara.'),
        (c3, MINT, 'SWITCH → ITEM-CF', 'Pengguna baru + favorit',
         'Memilih beberapa buku favorit. Sistem langsung beralih ke Item-CF dari buku-buku itu.'),
    ]:
        with kol:
            html(f'<div class="box"><span class="badge" style="background:{warna}">{badge}</span>'
                 f'<h3 style="margin:4px 0">{siapa}</h3><p style="margin:0">{isi}</p></div>')

    st.subheader('Model terbaik')
    m, ev = info['model'], evaluasi
    html('<div class="kpis">'
         + kpi('Data model', angka(m['rating']), f'{angka(m["user"])} pengguna × {angka(m["buku"])} buku', CHIP)
         + kpi('RMSE test · Item-CF', angka(ev.at['Item-Based CF', 'RMSE test'], 3),
               f'baseline {angka(ev.at["Baseline (rata-rata user)", "RMSE test"], 3)}', MINT)
         + kpi('Precision@10 · Item-CF', angka(ev.at['Item-Based CF', 'Precision@10'], 4),
               f'{angka(ev.at["Item-Based CF", "Precision@10"] / ev.at["Popularity (WR)", "Precision@10"], 1)}× popularity', CANARY)
         + kpi('Recall@10 · Item-CF', angka(ev.at['Item-Based CF', 'Recall@10'], 3),
               '1 dari 10 buku favorit masuk Top-10', VIOLET)
         + '</div>')


def halaman_eksplorasi():
    st.title('Eksplorasi Data')
    eda = info['eda']

    dist = eda['distribusi_rating']
    d = pd.DataFrame({'rating': list(dist), 'jumlah': list(dist.values())})
    d['jenis'] = np.where(d['rating'] == '0', 'Implisit (0)', 'Eksplisit (1–10)')
    chart = alt.Chart(d, title='Distribusi rating 0–10').mark_bar(stroke=INK, strokeWidth=2).encode(
        x=alt.X('rating:O', sort=None, title='RATING'), y=alt.Y('jumlah:Q', title='JUMLAH'),
        color=alt.Color('jenis:N', scale=alt.Scale(range=[CYAN, CORAL]), title=None),
        tooltip=['rating', alt.Tooltip('jumlah:Q', format=',')])
    st.altair_chart(gaya(chart), width='stretch', theme=None)
    html('<div class="box"><b>Insight.</b> 62,7% interaksi bernilai 0 (implisit) dan tidak dipakai model. '
         'Rating eksplisit menumpuk di 7–10 (nilai terbanyak: 8), jadi buku dianggap <b>disukai</b> jika rating ≥ 7.</div>')

    c1, c2 = st.columns(2)
    with c1:
        batang(eda['top_buku'], 'buku', 'rating', CANARY, 'Top 10 buku paling banyak dirating', horizontal=True,
               x_judul='JUMLAH RATING')
    with c2:
        batang(eda['top_penulis'], 'penulis', 'rating', VIOLET, 'Top 10 penulis paling banyak dirating', horizontal=True,
               x_judul='JUMLAH RATING')
    html('<div class="box"><b>Insight.</b> Banyak dirating belum tentu disukai: <i>Wild Animus</i> di posisi 2 '
         'punya rata-rata rating hanya ±4,4. Karena itu rekomendasi pengguna baru memakai <b>weighted rating</b>, bukan jumlah rating.</div>')

    c1, c2 = st.columns(2)
    with c1:
        batang(eda['kelompok_umur'], 'kelompok', 'pengguna', MINT, 'Kelompok umur pengguna', x_judul='UMUR', y_judul='PENGGUNA')
    with c2:
        batang(eda['top_negara'], 'negara', 'pengguna', CYAN, 'Top 10 negara pengguna', horizontal=True, x_judul='PENGGUNA')
    html('<div class="box"><b>Insight.</b> Median umur 32 tahun, tetapi 40% pengguna tidak mengisi umur yang valid. '
         'Separuh pengguna berasal dari USA, sehingga rekomendasi per negara paling stabil untuk negara besar.</div>')

    tahun = {k: v for k, v in eda['tahun_terbit'].items() if int(k) >= 1950}
    batang(tahun, 'tahun', 'buku', CANARY, 'Jumlah buku per tahun terbit (1950–2005)', x_judul='TAHUN', y_judul='BUKU', tinggi=260)

    lt = {('50+' if k == '50' else k): v for k, v in eda['rating_per_buku'].items()}
    batang(lt, 'jumlah rating', 'buku', CORAL, 'Long-tail: berapa rating yang dimiliki tiap buku?',
           x_judul='JUMLAH RATING PER BUKU', y_judul='BUKU', tinggi=260)
    html('<div class="box"><b>Insight.</b> 65,6% buku hanya punya <b>1 rating</b>. Collaborative Filtering butuh irisan '
         'pengguna, jadi model hanya memakai pengguna ≥ 10 rating dan buku ≥ 20 rating.</div>')


def halaman_rekomendasi():
    st.title('Rekomendasi')
    n = st.slider('Jumlah rekomendasi', 5, 20, 9)
    tab_lama, tab_baru, tab_mirip = st.tabs(['👤 Pengguna lama', '✨ Pengguna baru', '🔗 Buku mirip'])

    with tab_lama:
        jml = ratings['uid'].value_counts()
        pilihan = jml[jml >= 10].index.tolist()
        uid = st.selectbox('Pilih ID pengguna', pilihan, format_func=lambda u: f'User {u} · {jml[u]} rating')
        r = ratings[ratings['uid'] == uid].sort_values('rating', ascending=False)
        disukai = r.loc[r['rating'] >= SUKA, 'isbn']
        html('<span class="badge" style="background:#00F0FF">METODE: ITEM-BASED CF</span>'
             f'<span class="badge" style="background:#fff">{len(r)} RATING · {len(disukai)} DISUKAI</span>')
        with st.expander('Buku yang sudah dirating pengguna ini'):
            st.dataframe(pd.DataFrame({'judul': [judul(i) for i in r['isbn']], 'rating': r['rating'].values}),
                         hide_index=True)
        rek = rekomendasi_dari_buku((disukai if len(disukai) else r['isbn']).tolist(), n)
        grid([kartu_buku(b, f'SKOR {s:.3f}', MINT, a, i + 1) for i, (b, s, a) in enumerate(rek.itertuples(index=False))])

    with tab_baru:
        c1, c2 = st.columns(2)
        umur = c1.selectbox('Kelompok umur', ['Semua', '<18', '18-24', '25-34', '35-49', '50+'])
        negara_top = ratings['country'].value_counts().head(15).index.tolist()
        negara = c2.selectbox('Negara', ['Semua'] + negara_top)
        populer = ratings['isbn'].value_counts().index.tolist()                 # urutkan pilihan dari yang paling populer
        favorit = st.multiselect('Buku favorit (opsional). Pilih 1–3 buku yang pernah kamu sukai', populer,
                                 format_func=lambda i: f'{judul(i)} · {books.at[i, "author"]}', max_selections=3)
        if favorit:
            html('<span class="badge" style="background:#05FFA1">SWITCH → ITEM-BASED CF</span>')
            rek = rekomendasi_dari_buku(favorit, n)
            grid([kartu_buku(b, f'SKOR {s:.3f}', MINT, a, i + 1) for i, (b, s, a) in enumerate(rek.itertuples(index=False))])
        else:
            d = ratings
            if umur != 'Semua':
                d = d[d['age_group'] == umur]
            if negara != 'Semua':
                d = d[d['country'] == negara]
            html(f'<span class="badge" style="background:#FFE600">METODE: WEIGHTED RATING</span>'
                 f'<span class="badge" style="background:#fff">{angka(len(d))} RATING DI SEGMEN INI</span>')
            if d.empty:
                st.info('Belum ada rating dari segmen ini. Coba pilih "Semua".')
            else:
                wr = weighted_rating(d).head(n)
                grid([kartu_buku(b, f'WR {row.WR:.2f} · {int(row.v)} RATING', CANARY, no=i + 1)
                      for i, (b, row) in enumerate(wr.iterrows())])
            html('<div class="box" style="margin-top:22px"><b>Weighted rating</b> '
                 '<span class="mono">WR = v/(v+m)·R + m/(v+m)·C</span> menarik buku dengan sedikit rating ke arah '
                 'rata-rata global C, sehingga buku dengan 1 rating bernilai 10 tidak otomatis menang.</div>')

    with tab_mirip:
        isbn = st.selectbox('Pilih buku', ratings['isbn'].value_counts().index.tolist(),
                            format_func=lambda i: f'{judul(i)} · {books.at[i, "author"]}')
        s = S[pos[isbn]]
        top = np.argsort(-s)[:n]
        html('<span class="badge" style="background:#00F0FF">COSINE SIMILARITY + SHRINKAGE</span>')
        grid([kartu_buku(katalog[j], f'SIM {s[j]:.3f}', CYAN, no=i + 1) for i, j in enumerate(top)])


def halaman_evaluasi():
    st.title('Evaluasi Model')
    html('<div class="box">Data model dibagi <b>80% train / 20% test per pengguna</b>. Semua model dilatih dari train, '
         'lalu diuji di test. <b>RMSE/MAE</b> mengukur ketepatan menebak rating (lebih kecil lebih baik). '
         '<b>Precision@10/Recall@10</b> mengukur berapa buku yang benar-benar disukai (rating ≥ 8) masuk ke 10 rekomendasi '
         'teratas (lebih besar lebih baik).</div>')

    ev = evaluasi
    terbaik = {k: (ev[k].min() if 'MSE' in k or 'MAE' in k else ev[k].max()) for k in ev.columns if 'test' in k or '@' in k}
    kepala = ''.join(f'<th>{k}</th>' for k in ['Model'] + list(ev.columns))
    baris = ''
    for nama, row in ev.iterrows():
        sel = ''.join(
            f'<td class="{"win" if terbaik.get(k) == v else ""}">{"–" if pd.isna(v) else f"{v:.4f}"}</td>'
            for k, v in row.items())
        baris += f'<tr><td>{escape(nama)}</td>{sel}</tr>'
    html(f'<table class="ev"><tr>{kepala}</tr>{baris}</table>')
    st.caption('Sel hijau = terbaik di data test. Baseline tidak punya Precision/Recall karena tidak membuat daftar rekomendasi.')

    def banding(kolom, judul_grafik, warna):
        """Batang horizontal berkelompok: satu baris per model, satu batang per metrik."""
        d = ev[kolom].dropna().reset_index().melt('model', var_name='metrik', value_name='nilai')
        chart = alt.Chart(d, title=judul_grafik).mark_bar(stroke=INK, strokeWidth=2).encode(
            y=alt.Y('model:N', sort=list(ev.index), title=None), yOffset='metrik:N',
            x=alt.X('nilai:Q', title='NILAI'),
            color=alt.Color('metrik:N', scale=alt.Scale(range=warna), title=None),
            tooltip=['model', 'metrik', alt.Tooltip('nilai:Q', format='.4f')])
        st.altair_chart(gaya(chart, 300), width='stretch', theme=None)

    c1, c2 = st.columns(2)
    with c1:
        banding(['RMSE test', 'MAE test'], 'Error prediksi rating (lebih kecil = lebih baik)', [CYAN, CANARY])
    with c2:
        banding(['Precision@10', 'Recall@10'], 'Kualitas Top-10 (lebih besar = lebih baik)', [MINT, VIOLET])

    c1, c2 = st.columns(2)
    c1.markdown('##### Kesimpulan\n'
                '- **Item-Based CF** terbaik di semua metrik test.\n'
                '- Precision@10 Item-CF ±3,5× Popularity dan ±1,7× User-CF.\n'
                '- Selisih RMSE dengan baseline kecil: rating lebih ditentukan kebiasaan menilai pengguna.\n'
                '- Error train CF jauh lebih kecil dari test → ada overfitting ringan.')
    c2.markdown('##### Parameter\n'
                '| Parameter | Nilai |\n|---|---|\n'
                '| Filter data | pengguna ≥ 10, buku ≥ 20 rating |\n'
                '| Shrinkage λ | 10 |\n| Regularisasi β | 1 |\n'
                '| Disukai / relevan | rating ≥ 7 / ≥ 8 |\n| Top-K | 10 |')


HALAMAN = {'🏠 Ringkasan': halaman_ringkasan, '📊 Eksplorasi Data': halaman_eksplorasi,
           '🎯 Rekomendasi': halaman_rekomendasi, '📈 Evaluasi Model': halaman_evaluasi}
with st.sidebar:
    html('<h2 style="margin-bottom:0">📚 RECSYS</h2><p class="mono" style="font-size:12px">BOOK-CROSSING · SDM</p>')
    pilih = st.radio('Halaman', list(HALAMAN), label_visibility='collapsed')
    html('<p style="font-size:12px;margin-top:24px">Model: Item-Based CF + Weighted Rating<br>'
         'Data: Book-Crossing (1,1 jt interaksi)</p>')
HALAMAN[pilih]()
