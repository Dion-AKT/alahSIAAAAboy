# =============================================================
# Aplikasi Siklus Akuntansi Dagang dengan Login + Registrasi
# Versi Stabil FULL — Anti Error KeyError 'Akun'
# =============================================================

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io

st.set_page_config(page_title="Siklus Akuntansi Dagang", layout="wide")

# === Fungsi Format Rupiah ===
def format_rp(x):
    try:
        return "Rp {:,.2f}".format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "Rp 0,00"

# === Sidebar Logo — Tidak Error kalau file hilang ===
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=160)
st.sidebar.markdown("### Sistem Akuntansi Dagang")

# === File Database User ===
DATA_FILE = "data_user.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# === Login & Register ===
def login(username, password):
    data = load_data()
    return username in data and data[username].get("password") == password

def register(username, password):
    if not username or not password:
        return False, "Username dan password wajib diisi."
    data = load_data()
    if username in data:
        return False, "Username sudah digunakan."
    data[username] = {
        "password": password,
        "jurnal": [],
        "jurnal_penyesuaian": []
    }
    save_data(data)
    return True, "Registrasi berhasil."

# =============================================================
#                          MAIN APP
# =============================================================
def main_app():
    st.title("📈 Aplikasi Siklus Akuntansi Dagang")

    data = load_data()
    user = st.session_state.user

    # load user data
    user_data = data.get(user, {
        "jurnal": [],
        "jurnal_penyesuaian": []
    })

    jurnal = pd.DataFrame(user_data["jurnal"])
    jurnal_penyesuaian = pd.DataFrame(user_data["jurnal_penyesuaian"])

    # Pastikan kolom ada walaupun kosong
    if jurnal.empty:
        jurnal = pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])
    if jurnal_penyesuaian.empty:
        jurnal_penyesuaian = pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])

    # =============================================================
    #                   INPUT JURNAL UMUM
    # =============================================================
    st.sidebar.header("📝 Input Transaksi Baru")
    tgl = st.sidebar.date_input("Tanggal", datetime.today(), key="tgl_jurnal")
    akun_debit = st.sidebar.text_input("Akun Debit", key="akun_debit")
    jml_debit = st.sidebar.number_input("Jumlah Debit", min_value=0.0, format="%.2f", key="jml_debit")
    akun_kredit = st.sidebar.text_input("Akun Kredit", key="akun_kredit")
    jml_kredit = st.sidebar.number_input("Jumlah Kredit", min_value=0.0, format="%.2f", key="jml_kredit")
    ket = st.sidebar.text_input("Keterangan", key="ket_jurnal")

    if st.sidebar.button("Tambah Transaksi", key="btn_add_trx"):
        if jml_debit != jml_kredit:
            st.sidebar.error("⚠ Debit dan Kredit harus sama.")
        elif not akun_debit or not akun_kredit:
            st.sidebar.error("⚠ Nama akun wajib diisi.")
        else:
            new = pd.DataFrame([
                {"Tanggal": str(tgl), "Akun": akun_debit, "Debit": jml_debit, "Kredit": 0.0, "Keterangan": ket},
                {"Tanggal": str(tgl), "Akun": akun_kredit, "Debit": 0.0, "Kredit": jml_kredit, "Keterangan": ket}
            ])
            jurnal = pd.concat([jurnal, new], ignore_index=True)
            data[user]["jurnal"] = jurnal.to_dict(orient="records")
            save_data(data)
            st.sidebar.success("✔ Transaksi berhasil ditambahkan")

    # =============================================================
    #               Buku Besar & Neraca Saldo
    # =============================================================
    def buku_besar(df):
        ledger = {}
        if df.empty:
            return ledger

        for akun in df["Akun"].unique():
            dfa = df[df["Akun"] == akun].copy()
            dfa.sort_values("Tanggal", inplace=True)
            dfa["Mutasi"] = dfa["Debit"].fillna(0) - dfa["Kredit"].fillna(0)
            dfa["Saldo Akhir"] = dfa["Mutasi"].cumsum()
            ledger[akun] = dfa.reset_index(drop=True)

        return ledger

    def neraca_saldo(ledger):
        if not ledger:
            return pd.DataFrame(columns=["Akun", "Debit", "Kredit"])

        rows = []
        for akun, df in ledger.items():
            akhir = df["Saldo Akhir"].iloc[-1]
            rows.append({
                "Akun": akun,
                "Debit": max(akhir, 0),
                "Kredit": max(-akhir, 0)
            })

        return pd.DataFrame(rows)

    # === Tampilan Jurnal ===
    st.subheader("📒 1. Jurnal Umum")
    st.dataframe(jurnal.style.format({"Debit": format_rp, "Kredit": format_rp}))

    st.subheader("📚 2. Buku Besar")
    ledger = buku_besar(jurnal)
    for akun, df in ledger.items():
        with st.expander(f"Akun: {akun}"):
            st.dataframe(df.style.format({
                "Debit": format_rp,
                "Kredit": format_rp,
                "Mutasi": format_rp,
                "Saldo Akhir": format_rp
            }))

    st.subheader("📊 3. Neraca Saldo Awal")
    ns_awal = neraca_saldo(ledger)
    st.dataframe(ns_awal.style.format({"Debit": format_rp, "Kredit": format_rp}))

    # =============================================================
    #                 JURNAL PENYESUAIAN
    # =============================================================
    st.subheader("🔧 4. Jurnal Penyesuaian")
    with st.expander("Input Penyesuaian"):
        tglp = st.date_input("Tanggal Penyesuaian", datetime.today(), key="tgl_adj")
        ad = st.text_input("Akun Debit", key="adj_debit")
        ak = st.text_input("Akun Kredit", key="adj_kredit")
        jml = st.number_input("Jumlah", min_value=0.0, format="%.2f", key="adj_jml")
        ketp = st.text_input("Keterangan", key="adj_ket")

        if st.button("Tambah Penyesuaian", key="btn_add_adj"):
            if ad and ak and jml > 0:
                new_adj = pd.DataFrame([
                    {"Tanggal": str(tglp), "Akun": ad, "Debit": jml, "Kredit": 0.0, "Keterangan": ketp},
                    {"Tanggal": str(tglp), "Akun": ak, "Debit": 0.0, "Kredit": jml, "Keterangan": ketp}
                ])
                jurnal_penyesuaian = pd.concat([jurnal_penyesuaian, new_adj], ignore_index=True)
                data[user]["jurnal_penyesuaian"] = jurnal_penyesuaian.to_dict(orient="records")
                save_data(data)
                st.success("✔ Penyesuaian berhasil ditambahkan")

    st.dataframe(jurnal_penyesuaian.style.format({"Debit": format_rp, "Kredit": format_rp}))

    # =============================================================
    #       Neraca Saldo Setelah Penyesuaian
    # =============================================================
    st.subheader("📈 5. Neraca Saldo Setelah Penyesuaian")

    all_jurnal = pd.concat([jurnal, jurnal_penyesuaian], ignore_index=True)
    ledger_adj = buku_besar(all_jurnal)
    ns_adj = neraca_saldo(ledger_adj)

    st.dataframe(ns_adj.style.format({"Debit": format_rp, "Kredit": format_rp}))

    # =============================================================
    #          LABA RUGI — ANTI ERROR 'AKUN'
    # =============================================================
    st.subheader("📉 6. Laporan Laba Rugi")

    if ns_adj.empty or "Akun" not in ns_adj.columns:
        pendapatan = 0
        beban = 0
    else:
        pendapatan = ns_adj[ns_adj["Akun"].str.contains("Pendapatan", case=False, na=False)]["Kredit"].sum()
        beban = ns_adj[ns_adj["Akun"].str.contains("Beban", case=False, na=False)]["Debit"].sum()

    laba = pendapatan - beban

    st.write(f"**Pendapatan:** {format_rp(pendapatan)}")
    st.write(f"**Beban:** {format_rp(beban)}")
    st.write(f"### ➕ Laba Bersih: {format_rp(laba)}")

    # =============================================================
    #          PERUBAHAN MODAL
    # =============================================================
    st.subheader("🔄 7. Perubahan Modal")
    modal_awal = st.number_input("Modal Awal", value=0.0, key="modal_awal")
    prive = st.number_input("Prive", value=0.0, key="prive")
    modal_akhir = modal_awal + laba - prive

    st.write(f"### Modal Akhir: {format_rp(modal_akhir)}")

    # =============================================================
    #                      NERACA
    # =============================================================
    st.subheader("🧾 8. Neraca")

    aktiva = ns_adj[ns_adj["Akun"].str.contains("Kas|Piutang|Persediaan", case=False, na=False)]["Debit"].sum()
    kewajiban = ns_adj[ns_adj["Akun"].str.contains("Utang", case=False, na=False)]["Kredit"].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total Aktiva:** {format_rp(aktiva)}")
    with col2:
        st.write(f"**Total Kewajiban + Modal:** {format_rp(kewajiban + modal_akhir)}")

    # =============================================================
    #                      JURNAL PENUTUP
    # =============================================================
    st.subheader("🛑 9. Jurnal Penutup")

    def jurnal_penutup():
        rows = []
        if pendapatan > 0:
            rows += [
                {"Akun": "Pendapatan", "Debit": pendapatan, "Kredit": 0, "Keterangan": "Tutup pendapatan"},
                {"Akun": "Ikhtisar Laba Rugi", "Debit": 0, "Kredit": pendapatan, "Keterangan": "Tutup pendapatan"}
            ]
        if beban > 0:
            rows += [
                {"Akun": "Ikhtisar Laba Rugi", "Debit": beban, "Kredit": 0, "Keterangan": "Tutup beban"},
                {"Akun": "Beban", "Debit": 0, "Kredit": beban, "Keterangan": "Tutup beban"}
            ]
        if laba != 0:
            rows += [
                {"Akun": "Ikhtisar Laba Rugi", "Debit": laba, "Kredit": 0, "Keterangan": "Tutup laba"},
                {"Akun": "Modal", "Debit": 0, "Kredit": laba, "Keterangan": "Tutup laba"}
            ]
        return pd.DataFrame(rows)

    jpenutup = jurnal_penutup()
    st.dataframe(jpenutup.style.format({"Debit": format_rp, "Kredit": format_rp}))

    # =============================================================
    #            NERACA SETELAH PENUTUPAN
    # =============================================================
    st.subheader("📌 10. Neraca Saldo Setelah Penutupan")
    final_jurnal = pd.concat([all_jurnal, jpenutup], ignore_index=True)
    ledger_final = buku_besar(final_jurnal)
    ns_akhir = neraca_saldo(ledger_final)

    st.dataframe(ns_akhir.style.format({"Debit": format_rp, "Kredit": format_rp}))

    # =============================================================
    #                       EXPORT
    # =============================================================
    st.subheader("📤 Download Excel")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        jurnal.to_excel(writer, "Jurnal Umum", index=False)
        jurnal_penyesuaian.to_excel(writer, "Jurnal Penyesuaian", index=False)
        ns_awal.to_excel(writer, "Neraca Awal", index=False)
        ns_adj.to_excel(writer, "Neraca Disesuaikan", index=False)
        jpenutup.to_excel(writer, "Jurnal Penutup", index=False)
        ns_akhir.to_excel(writer, "Neraca Akhir", index=False)

    output.seek(0)

    st.download_button(
        "⬇️ Download Excel",
        data=output,
        file_name="laporan_keuangan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================================================
#                    LOGIN & REGISTER UI
# =============================================================
def login_page():
    st.title("🔐 Login Sistem Akuntansi")
    user = st.text_input("Username", key="login_user")
    pw = st.text_input("Password", type="password", key="login_pw")

    if st.button("Login", key="btn_login"):
        if login(user, pw):
            st.session_state.user = user
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah.")

    if st.button("Daftar Akun Baru", key="btn_show_register"):
        st.session_state.show_register = True

def register_page():
    st.title("🆕 Registrasi")
    user = st.text_input("Username Baru", key="reg_user")
    pw = st.text_input("Password Baru", type="password", key="reg_pw")

    if st.button("Daftar", key="btn_register"):
        ok, msg = register(user, pw)
        if ok:
            st.success(msg)
            st.session_state.show_register = False
        else:
            st.error(msg)

    if st.button("Kembali", key="btn_back_login"):
        st.session_state.show_register = False

# =============================================================
#                    SYSTEM SESSION STATE
# =============================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False

if st.session_state.user:
    main_app()
else:
    if st.session_state.show_register:
        register_page()
    else:
        login_page()
