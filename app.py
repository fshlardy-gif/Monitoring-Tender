import io
import sqlite3
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Konfigurasi Tampilan Halaman
st.set_page_config(page_title="Monitoring Tender LPSE", layout="wide")

# ==========================================
# 1. KONEKSI & INISIALISASI DATABASE SQLITE
# ==========================================
DB_FILE = "tender_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tender (
            id_paket TEXT PRIMARY KEY,
            nama_tender TEXT,
            nilai_hps REAL,
            harga_penawaran REAL,
            harga_negosiasi REAL,
            tenaga_ahli TEXT,
            tenaga_pendukung TEXT,
            status_internal TEXT,
            url_lpse TEXT,
            pemenang TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM tender", conn)
    conn.close()
    # Format ulang nama kolom agar sesuai tampilan
    df.rename(columns={
        'id_paket': 'ID Paket',
        'nama_tender': 'Nama Tender',
        'nilai_hps': 'Nilai HPS (Rp)',
        'harga_penawaran': 'Harga Penawaran (Rp)',
        'harga_negosiasi': 'Harga Negosiasi (Rp)',
        'tenaga_ahli': 'Tenaga Ahli',
        'tenaga_pendukung': 'Tenaga Pendukung',
        'status_internal': 'Status Internal',
        'url_lpse': 'URL LPSE',
        'pemenang': 'Pemenang'
    }, inplace=True)
    return df

def save_data(data_dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO tender 
        (id_paket, nama_tender, nilai_hps, harga_penawaran, harga_negosiasi, tenaga_ahli, tenaga_pendukung, status_internal, url_lpse, pemenang)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_dict['ID Paket'], data_dict['Nama Tender'], data_dict['Nilai HPS (Rp)'],
        data_dict['Harga Penawaran (Rp)'], data_dict['Harga Negosiasi (Rp)'],
        data_dict['Tenaga Ahli'], data_dict['Tenaga Pendukung'],
        data_dict['Status Internal'], data_dict['URL LPSE'], data_dict['Pemenang']
    ))
    conn.commit()
    conn.close()

def delete_data(id_paket):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tender WHERE id_paket = ?", (id_paket,))
    conn.commit()
    conn.close()

def update_pemenang_db(id_paket, pemenang):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tender SET pemenang = ? WHERE id_paket = ?", (pemenang, id_paket))
    conn.commit()
    conn.close()

# Jalankan inisialisasi tabel database
init_db()

# ==========================================
# 2. FUNGSI SCRAPING PEMENANG LPSE
# ==========================================
def dapatkan_pemenang_lpse(url_lpse):
    if not url_lpse:
        return "-"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_lpse, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            pemenang_element = soup.find('td', text='Pemenang')
            if pemenang_element:
                return pemenang_element.find_next_sibling('td').text.strip()
            return "Belum Ada Pemenang"
        return "Gagal Akses LPSE"
    except Exception as e:
        return f"Error: {str(e)}"

# Read Data dari SQLite
df_tender = load_data()

# ==========================================
# 3. SIDEBAR (TAMBAH & HAPUS PAKET)
# ==========================================
st.sidebar.title("➕ Tambah Tender Baru")
id_paket = st.sidebar.text_input("ID Paket")
nama_tender = st.sidebar.text_input("Nama Tender / Paket")
nilai_hps = st.sidebar.number_input("Nilai HPS (Rp)", min_value=0, step=1000000)
harga_penawaran = st.sidebar.number_input("Harga Penawaran (Rp)", min_value=0, step=1000000)
harga_negosiasi = st.sidebar.number_input("Harga Hasil Negosiasi (Rp)", min_value=0, step=1000000)

st.sidebar.subheader("👥 Kebutuhan Personil")
tenaga_ahli = st.sidebar.text_area("Tenaga Ahli", placeholder="Contoh: 1 Team Leader, 2 Ahli K3")
tenaga_pendukung = st.sidebar.text_area("Tenaga Pendukung", placeholder="Contoh: 1 Cad/Cam Operator, 1 Admin")

status_internal = st.sidebar.selectbox("Status Internal", ["Kirim Penawaran", "Menang", "Kalah"])
url_lpse = st.sidebar.text_input("URL Detail Paket LPSE PU")

if st.sidebar.button("Simpan Paket"):
    if id_paket and nama_tender:
        new_data = {
            'ID Paket': id_paket,
            'Nama Tender': nama_tender,
            'Nilai HPS (Rp)': nilai_hps,
            'Harga Penawaran (Rp)': harga_penawaran,
            'Harga Negosiasi (Rp)': harga_negosiasi,
            'Tenaga Ahli': tenaga_ahli if tenaga_ahli else "-",
            'Tenaga Pendukung': tenaga_pendukung if tenaga_pendukung else "-",
            'Status Internal': status_internal,
            'URL LPSE': url_lpse,
            'Pemenang': '-'
        }
        save_data(new_data)
        st.sidebar.success("Paket Berhasil Disimpan Permanen!")
        st.rerun()
    else:
        st.sidebar.error("ID Paket dan Nama Tender wajib diisi!")

# --- FITUR HAPUS PAKET DI SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.title("🗑️ Hapus Tender")

if not df_tender.empty:
    list_id_hapus = df_tender['ID Paket'].tolist()
    paket_to_delete = st.sidebar.selectbox("Pilih ID Paket yang Akan Dihapus", list_id_hapus)
    
    if st.sidebar.button("Hapus Paket", type="primary"):
        delete_data(paket_to_delete)
        st.sidebar.success(f"Paket {paket_to_delete} berhasil dihapus!")
        st.rerun()
else:
    st.sidebar.info("Belum ada data paket untuk dihapus.")

# ==========================================
# 4. DASHBOARD UTAMA
# ==========================================
st.title("📊 Dashboard Monitoring Laporan Tender LPSE PU")

# Metric Ringkasan (Total HPS diganti menjadi Total Harga Negosiasi)
col1, col2, col3 = st.columns(3)
total_paket = len(df_tender)
total_negosiasi = df_tender['Harga Negosiasi (Rp)'].sum() if total_paket > 0 else 0
total_menang = len(df_tender[df_tender['Status Internal'] == 'Menang']) if total_paket > 0 else 0

col1.metric("Total Paket Diikuti", total_paket)
col2.metric("Total Harga Negosiasi", f"Rp {total_negosiasi:,.0f}")
col3.metric("Tender Menang", total_menang)

st.markdown("---")

# Tombol Aksi (Update & Download Excel)
col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    if st.button("🔄 Update Jadwal Semua Lelang dari LPSE"):
        if not df_tender.empty:
            with st.spinner("Mengambil data pemenang dari LPSE..."):
                for index, row in df_tender.iterrows():
                    url = row['URL LPSE']
                    pemenang = dapatkan_pemenang_lpse(url)
                    update_pemenang_db(row['ID Paket'], pemenang)
                st.success("Data Pemenang Berhasil Diperbarui!")
                st.rerun()

with col_btn2:
    if not df_tender.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_tender.to_excel(writer, index=False, sheet_name='Monitoring Tender')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Laporan Excel",
            data=processed_data,
            file_name="Laporan_Monitoring_Tender_LPSE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Tampilkan Tabel Utama
st.subheader("📋 Daftar Monitoring Lelang Aktif")

if not df_tender.empty:
    st.dataframe(
        df_tender,
        column_config={
            "ID Paket": st.column_config.TextColumn("ID Paket"),
            "Nama Tender": st.column_config.TextColumn("Nama Tender / Paket", width="large"),
            "Nilai HPS (Rp)": st.column_config.NumberColumn("Nilai HPS", format="Rp %d"),
            "Harga Penawaran (Rp)": st.column_config.NumberColumn("Harga Penawaran", format="Rp %d"),
            "Harga Negosiasi (Rp)": st.column_config.NumberColumn("Harga Negosiasi", format="Rp %d"),
            "Tenaga Ahli": st.column_config.TextColumn("Tenaga Ahli"),
            "Tenaga Pendukung": st.column_config.TextColumn("Tenaga Pendukung"),
            "Status Internal": st.column_config.SelectboxColumn("Status Internal", options=["Kirim Penawaran", "Menang", "Kalah"]),
            "URL LPSE": st.column_config.LinkColumn("URL Detail LPSE"),
            "Pemenang": st.column_config.TextColumn("Pemenang LPSE")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Belum ada data paket lelang yang dimasukkan.")
