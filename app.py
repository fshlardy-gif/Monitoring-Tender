import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. FUNGSI SCRAPING (Taruh di bagian paling atas)
# ==========================================
def dapatkan_pemenang_lpse(url_lpse):
    """Fungsi untuk mengambil nama pemenang dari URL LPSE PU"""
    if not url_lpse:
        return "-"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_lpse, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Contoh selector: Sesuaikan tag/class dengan halaman LPSE PU
            pemenang_element = soup.find('td', text='Pemenang')
            if pemenang_element:
                return pemenang_element.find_next_sibling('td').text.strip()
            return "Belum Ada Pemenang"
        return "Gagal Akses LPSE"
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# 2. INISIALISASI DATA (Session State)
# ==========================================
if 'df_tender' not in st.session_state:
    st.session_state.df_tender = pd.DataFrame(columns=[
        'ID Paket', 'Nama Tender', 'Nilai HPS (Rp)', 
        'Status Internal', 'URL LPSE', 'Pemenang'
    ])

# ==========================================
# 3. SIDEBAR (Tambah Tender Baru)
# ==========================================
st.sidebar.title("Tambah Tender Baru")
id_paket = st.sidebar.text_input("ID Paket")
nama_tender = st.sidebar.text_input("Nama Tender / Paket")
nilai_hps = st.sidebar.number_input("Nilai HPS (Rp)", min_value=0)
status_internal = st.sidebar.selectbox("Status Internal", ["Kirim Penawaran", "Menang", "Kalah"])
url_lpse = st.sidebar.text_input("URL Detail Paket LPSE PU")

if st.sidebar.button("Simpan Paket"):
    new_data = {
        'ID Paket': id_paket,
        'Nama Tender': nama_tender,
        'Nilai HPS (Rp)': nilai_hps,
        'Status Internal': status_internal,
        'URL LPSE': url_lpse,
        'Pemenang': '-'  # Default awal
    }
    st.session_state.df_tender = pd.concat(
        [st.session_state.df_tender, pd.DataFrame([new_data])], 
        ignore_index=True
    )
    st.sidebar.success("Paket Berhasil Disimpan!")

# ==========================================
# 4. MAIN DASHBOARD & TOMBOL UPDATE LPSE
# ==========================================
st.title("Dashboard Monitoring Laporan Tender LPSE PU")

# Tombol diletakkan persis di atas tabel monitoring
if st.button("Update Jadwal Semua Lelang dari LPSE"):
    with st.spinner("Mengambil data pemenang dari LPSE..."):
        for index, row in st.session_state.df_tender.iterrows():
            url = row['URL LPSE']
            pemenang = dapatkan_pemenang_lpse(url)
            
            # Update data pemenang di DataFrame
            st.session_state.df_tender.at[index, 'Pemenang'] = pemenang
            
            # Jika nama perusahaan Anda cocok, otomatis ubah Status Internal
            NAMA_PERUSAHAAN_SAYA = "PT NAMA PERUSAHAAN ANDA"
            if pemenang.lower() == NAMA_PERUSAHAAN_SAYA.lower():
                st.session_state.df_tender.at[index, 'Status Internal'] = "Menang"
                
        st.success("Data Pemenang Berhasil Diperbarui!")
        st.rerun()

# Tampilkan Tabel
st.subheader("📋 Daftar Monitoring Lelang Aktif")
st.dataframe(st.session_state.df_tender, use_container_width=True)# --- FITUR HAPUS PAKET DI SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.title("🗑️ Hapus Tender")

if not st.session_state.df_tender.empty:
    # Pilihan ID Paket yang ingin dihapus
    list_id_hapus = st.session_state.df_tender['ID Paket'].tolist()
    paket_to_delete = st.sidebar.selectbox("Pilih ID Paket yang Akan Dihapus", list_id_hapus)
    
    if st.sidebar.button("Hapus Paket", type="primary"):
        # Filter dataframe untuk menghapus baris dengan ID Paket terpilih
        st.session_state.df_tender = st.session_state.df_tender[
            st.session_state.df_tender['ID Paket'] != paket_to_delete
        ].reset_index(drop=True)
        
        st.sidebar.success(f"Paket {paket_to_delete} berhasil dihapus!")
        st.rerun()
else:
    st.sidebar.info("Belum ada data paket untuk dihapus.")