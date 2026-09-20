import io
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Konfigurasi Tampilan Halaman
st.set_page_config(page_title="Monitoring Tender LPSE", layout="wide")

# ==========================================
# 1. FUNGSI SCRAPING PEMENANG LPSE
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

# ==========================================
# 2. INISIALISASI DATASET
# ==========================================
if 'df_tender' not in st.session_state:
    st.session_state.df_tender = pd.DataFrame(columns=[
        'ID Paket', 'Nama Tender', 'Nilai HPS (Rp)', 
        'Harga Penawaran (Rp)', 'Harga Negosiasi (Rp)',
        'Tenaga Ahli', 'Tenaga Pendukung',
        'Status Internal', 'URL LPSE', 'Pemenang'
    ])

# ==========================================
# 3. SIDEBAR (TAMBAH & HAPUS TENDER)
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
        st.session_state.df_tender = pd.concat(
            [st.session_state.df_tender, pd.DataFrame([new_data])], 
            ignore_index=True
        )
        st.sidebar.success("Paket Berhasil Disimpan!")
        st.rerun()
    else:
        st.sidebar.error("ID Paket dan Nama Tender wajib diisi!")

# --- FITUR HAPUS PAKET DI SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.title("🗑️ Hapus Tender")

if not st.session_state.df_tender.empty:
    list_id_hapus = st.session_state.df_tender['ID Paket'].tolist()
    paket_to_delete = st.sidebar.selectbox("Pilih ID Paket yang Akan Dihapus", list_id_hapus)
    
    if st.sidebar.button("Hapus Paket", type="primary"):
        st.session_state.df_tender = st.session_state.df_tender[
            st.session_state.df_tender['ID Paket'] != paket_to_delete
        ].reset_index(drop=True)
        st.sidebar.success(f"Paket {paket_to_delete} berhasil dihapus!")
        st.rerun()
else:
    st.sidebar.info("Belum ada data paket untuk dihapus.")

# ==========================================
# 4. DASHBOARD UTAMA
# ==========================================
st.title("📊 Dashboard Monitoring Laporan Tender LPSE PU")

# Metric Ringkasan
col1, col2, col3 = st.columns(3)
total_paket = len(st.session_state.df_tender)
total_hps = st.session_state.df_tender['Nilai HPS (Rp)'].sum() if total_paket > 0 else 0
total_menang = len(st.session_state.df_tender[st.session_state.df_tender['Status Internal'] == 'Menang'])

col1.metric("Total Paket Diikuti", total_paket)
col2.metric("Total Nilai HPS", f"Rp {total_hps:,.0f}")
col3.metric("Tender Menang", total_menang)

st.markdown("---")

# Tombol Aksi (Update & Download Excel)
col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    if st.button("🔄 Update Jadwal Semua Lelang dari LPSE"):
        if not st.session_state.df_tender.empty:
            with st.spinner("Mengambil data pemenang dari LPSE..."):
                for index, row in st.session_state.df_tender.iterrows():
                    url = row['URL LPSE']
                    pemenang = dapatkan_pemenang_lpse(url)
                    st.session_state.df_tender.at[index, 'Pemenang'] = pemenang
                st.success("Data Pemenang Berhasil Diperbarui!")
                st.rerun()

with col_btn2:
    if not st.session_state.df_tender.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.df_tender.to_excel(writer, index=False, sheet_name='Monitoring Tender')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Laporan Excel",
            data=processed_data,
            file_name="Laporan_Monitoring_Tender_LPSE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Tampilkan Tabel Utama
st.subheader("📋 Daftar Monitoring Lelang Aktif")

if not st.session_state.df_tender.empty:
    st.dataframe(
        st.session_state.df_tender,
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
