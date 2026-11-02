# SuperTani ERP

Aplikasi ERP Basic untuk operasional perusahaan pupuk menggunakan Python dan Streamlit.

## Menjalankan di komputer lokal

1. Buat virtual environment:
   `python -m venv .venv`
2. Aktifkan:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
3. Instal dependensi:
   `pip install -r requirements.txt`
4. Jalankan:
   `streamlit run app.py`

## Status versi 0.1.0

- Fondasi aplikasi dan navigasi tersedia.
- Dashboard awal tersedia.
- Master JSON masih kosong sebagai data awal.
- Data transaksi sementara menggunakan `st.session_state`.
- Belum ada database permanen.

**Penting:** `st.session_state` bukan penyimpanan permanen. Data dapat hilang saat sesi berakhir atau aplikasi restart.
