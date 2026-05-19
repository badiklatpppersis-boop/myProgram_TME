import streamlit as st

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Analisis Kadar Larutan",
    page_icon="🧪",
    layout="centered"
)

st.title("🧪 Analisis Kadar Larutan")
st.write("Aplikasi web untuk menghitung kadar garam larutan dan target penyerapan.")

# List Data Konfigurasi
list_satuan = ["Metrik", "Imperial"]
list_kadar = ["Persen", "PPT", "PPM"]
list_bitdepth = ["8", "10", "12", "14", "16"]

# --- INPUT SECTION ---
st.subheader("⚙️ Konfigurasi & Input Data")

col1, col2 = st.columns(2)

with col1:
    val_satuan = st.selectbox("Pilih Satuan:", list_satuan, index=0)
with col2:
    val_kadar = st.selectbox("Pilih Kadar:", list_kadar, index=0)

# Menentukan label satuan berdasarkan pilihan pengguna
satuan_massa = "Gram" if val_satuan == "Metrik" else "Ons"

# Input Form untuk Massa dan Sensor
entry_air = st.number_input(f"Massa Air ({satuan_massa}):", min_value=0.0, step=0.1, format="%.2f")
entry_garam = st.number_input(f"Massa Garam ({satuan_massa}):", min_value=0.0, step=0.1, format="%.2f")
entry_telur = st.number_input(f"Massa Telur per Biji ({satuan_massa}):", min_value=0.0, step=0.1, format="%.2f")
entry_prstelur = st.number_input("Persentase Massa Garam/Telur (%):", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
entry_jmltelur = st.number_input("Jumlah Telur (Butir):", min_value=0.0, step=1.0, format="%.0f")

# Konfigurasi Bitdepth & TDS
entry_bdt = st.selectbox("Bitdepth ADC:", list_bitdepth, index=1) # Default 10-bit

# Menentukan teks panduan berdasarkan bitdepth yang dipilih
if entry_bdt == "8": max_adc, teksbdt = 255, "TDS Analog (0-255):"
elif entry_bdt == "10": max_adc, teksbdt = 1023, "TDS Analog (0-1023):"
elif entry_bdt == "12": max_adc, teksbdt = 4095, "TDS Analog (0-4095):"
elif entry_bdt == "14": max_adc, teksbdt = 16383, "TDS Analog (0-16383):"
elif entry_bdt == "16": max_adc, teksbdt = 65535, "TDS Analog (0-65535):"
else: max_adc, teksbdt = 1023, "TDS Analog:"

entry_tds = st.number_input(teksbdt, min_value=0.0, max_value=float(max_adc), step=1.0, format="%.0f")

# --- PROSES PERHITUNGAN ---
st.markdown("---")

if st.button("🚀 Hitung Analisis", use_container_width=True):
    try:
        bdt = max_adc
        val_tds = float(entry_tds)
        val_air = float(entry_air)
        val_garaminit = float(entry_garam)
        val_telur = float(entry_telur)
        val_prstelur = float(entry_prstelur)
        val_jmltelur = float(entry_jmltelur)
        
        # Rumus utama Anda
        val_k = val_prstelur * 0.01
        val_garamleft = val_garaminit - (((val_k * val_telur) / (1 - val_k)) * val_jmltelur)
        
        # Validasi Pembagian dengan Nol & Validitas TDS
        if bdt == 0 or (val_tds / bdt) >= 1:
            st.error("Error: Nilai TDS tidak valid atau melebihi batas bitdepth!")
        elif val_garaminit + val_air == 0 or val_garamleft + val_air == 0:
            st.error("Error: Total massa awal/target adalah 0 (Pembagian dengan nol)!")
        else:
            val_garamskrg = ((val_tds / bdt) * val_air) / (1 - (val_tds / bdt))
            val_garamtsp = val_garaminit - val_garamskrg
            
            if val_garamskrg + val_air == 0:
                st.error("Error: Total massa sekarang adalah 0!")
                st.stop()
                
            ratio_awal = val_garaminit / (val_garaminit + val_air)
            ratio_akhir = val_garamleft / (val_garamleft + val_air)
            ratio_skrg = val_garamskrg / (val_garamskrg + val_air)
            
            total_massa_telur = val_telur * val_jmltelur
            if val_garamtsp + total_massa_telur == 0:
                ratio_prstelurskg = 0
            else:
                ratio_prstelurskg = val_garamtsp / (val_garamtsp + total_massa_telur)
            
            # Pengali skala kadar
            if val_kadar == "Persen":
                mult, unit = 10**2, "%"
            elif val_kadar == "PPT":
                mult, unit = 10**3, " PPT"
            elif val_kadar == "PPM":
                mult, unit = 10**6, " PPM"

            # --- OUTPUT SECTION ---
            st.subheader("📊 Hasil Analisis Kadar")
            
            # Menampilkan hasil dalam bentuk kartu (metrics) yang rapi
            c1, c2 = st.columns(2)
            with c1:
                st.metric(label="Kadar Garam Larutan Awal", value=f"{ratio_awal * mult:.2f}{unit}")
                st.metric(label="Kadar Garam Larutan Sekarang", value=f"{ratio_skrg * mult:.2f}{unit}")
            with c2:
                st.metric(label="Kadar Garam Larutan Target", value=f"{ratio_akhir * mult:.2f}{unit}")
                st.metric(label="Kadar Garam Telur", value=f"{ratio_prstelurskg * mult:.2f}{unit}")
                
    except ValueError:
        st.error("Pastikan semua input diisi dengan angka yang valid!")
