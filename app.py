import io
import requests
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

# Konfigurasi Tampilan Halaman
st.set_page_config(page_title="Monitoring Tender LPSE", layout="wide")

# ==========================================
# 1. INTEGRASI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1O4pgSrn1hCWfyFrmbB_O4fGkwyZIGJex"
GID = "1621753805"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=5) # Cache otomatis disegarkan setiap 5 detik
def load_data_from_sheets():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets. Error: {e}")
        return pd.DataFrame()

# ==========================================
# 2. FUNGSI SCRAPING PEMENANG LPSE
# ==========================================
def dapatkan_pemenang_lpse(url_lpse):
    if not url_lpse or pd.isna(url_lpse) or str(url_lpse).strip() in ["-", "", "None", "nan"]:
        return "-"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url_lpse, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            pemenang_element = soup.find('td', string='Pemenang') or soup.find('td', text='Pemenang')
            if pemenang_element:
                return pemenang_element.find_next_sibling('td').text.strip()
            return "Belum Ada Pemenang"
        return "Gagal Akses LPSE"
    except Exception as e:
        return f"Error: {str(e)}"

# Tarik data dari Google Sheets
df_tender = load_data_from_sheets()

# ==========================================
# 3. DASHBOARD UTAMA
# ==========================================
st.title("📊 Dashboard Monitoring Laporan Tender LPSE PU")
st.info("💡 Website terhubung dengan Google Sheets. Total Harga Negosiasi di atas kini menghitung khusus paket lelang yang **Menang**.")

if not df_tender.empty:
    # --------------------------------------------------
    # PEMBERSIHAN DATA
    # --------------------------------------------------
    df_tender = df_tender.fillna("-")
    df_tender = df_tender.replace(["None", "nan", "NaN", ""], "-")

    # Pembersihan khusus kolom angka/uang
    kolom_uang = ['Nilai HPS (Rp)', 'Harga Penawaran (Rp)', 'Harga Negosiasi (Rp)']
    for col in kolom_uang:
        if col in df_tender.columns:
            s_clean = df_tender[col].astype(str).str.replace(r'[^\d]', '', regex=True)
            df_tender[col] = pd.to_numeric(s_clean, errors='coerce').fillna(0)

    # Identifikasi Paket Menang
    is_menang = df_tender['Status Internal'].astype(str).str.strip().str.lower() == 'menang' if 'Status Internal' in df_tender.columns else pd.Series([False]*len(df_tender))
    
    # Hitung Total Harga Negosiasi KHUSUS Paket Menang
    total_negosiasi_menang = df_tender.loc[is_menang, 'Harga Negosiasi (Rp)'].sum() if 'Harga Negosiasi (Rp)' in df_tender.columns else 0
    
    # Metric Ringkasan
    col1, col2, col3 = st.columns(3)
    total_paket = len(df_tender)
    total_menang = is_menang.sum()

    col1.metric("Total Paket Diikuti", total_paket)
    col2.metric("Total Harga Negosiasi (Menang)", f"Rp {total_negosiasi_menang:,.0f}".replace(",", "."))
    col3.metric("Tender Menang", total_menang)

    st.markdown("---")

    # Tombol Aksi (Refresh & Download Excel)
    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("🔄 Segarkan Data dari Google Sheets"):
            st.cache_data.clear()
            st.rerun()

    with col_btn2:
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

    # Pemformatan Tampilan Teks & Uang
    df_tampil = df_tender.copy()
    
    def format_rupiah(val):
        try:
            val_int = int(val)
            if val_int == 0:
                return "Rp 0"
            return f"Rp {val_int:,}".replace(",", ".")
        except:
            return "Rp 0"

    # Tambahkan Kolom "Nilai Negosiasi Menang"
    df_tampil['Tender Menang (Rp)'] = df_tender.apply(
        lambda row: format_rupiah(row['Harga Negosiasi (Rp)']) if str(row.get('Status Internal', '')).strip().lower() == 'menang' else "-", 
        axis=1
    )

    for col in kolom_uang:
        if col in df_tampil.columns:
            df_tampil[col] = df_tampil[col].apply(format_rupiah)

    # Memastikan tidak ada sisa None di tampilan akhir
    df_tampil = df_tampil.fillna("-")
    df_tampil = df_tampil.replace(["None", "nan", "NaN", ""], "-")

    # Tampilkan Tabel Utama
    st.subheader("📋 Daftar Monitoring Lelang Aktif")
    st.dataframe(
        df_tampil,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("Data belum tersedia atau sedang memuat dari Google Sheets...")
