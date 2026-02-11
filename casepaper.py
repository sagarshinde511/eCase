import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime

# -------------------- DB Connection --------------------
def get_connection():
    return mysql.connector.connect(
        host="82.180.143.66",
        user="u263681140_students",
        password="testStudents@123",
        database="u263681140_students"
    )

# -------------------- Insert Patient --------------------
def insert_patient(data):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
    INSERT INTO E_casepatient 
    (Name, RFIDNO, Age, Gender, BloodGroup, DateofBirth, ContactNo, EmailID, Address, DoctorAssigned)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, data)
    conn.commit()
    cursor.close()
    conn.close()

# -------------------- Fetch All Patients --------------------
def get_all_patients():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM E_casepatient ORDER BY ID DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# -------------------- Fetch Medical History --------------------
def get_medical_history_by_rfid(rfidno="41E2014B"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM medical__histroy WHERE RFIDNo = %s ORDER BY ID DESC",
            (rfidno,)
        )
        rows = cursor.fetchall()
        return rows if rows else []
    except Exception as e:
        st.error(f"❌ Error fetching medical history: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# -------------------- Fetch Appointments --------------------
def get_current_appointments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM E_Case ORDER BY Date_Time DESC")
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        st.error(f"❌ Failed to fetch appointments: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# -------------------- Delete Appointment By RFID --------------------
def delete_appointment_by_rfid(rfid):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM E_Case WHERE RFID_No = %s", (rfid,))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        return affected_rows > 0
    except Exception as e:
        st.error(f"❌ Error deleting appointment: {e}")
        return False

# -------------------- Dashboard --------------------
def dashboard():
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.radio("Select Option", ["Register Patient", "View All Patients", "View Medical History", "Current Appointments", "Logout"])

    # Register Patient
    if menu == "Register Patient":
        with st.form("patient_form"):
            st.subheader("Register New Patient")
            name = st.text_input("Full Name")
            rfid = st.text_input("RFID No")
            age = st.text_input("Age")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            blood_group = st.text_input("Blood Group")
            dob = st.date_input("Date of Birth")
            contact = st.text_input("Contact Number")
            email = st.text_input("Email ID")
            address = st.text_area("Address")
            doctor = st.text_input("Doctor Assigned")

            submitted = st.form_submit_button("Register Patient")
            if submitted:
                try:
                    age_int = int(age)
                    dob_str = dob.strftime('%Y-%m-%d')
                    insert_patient((name, rfid, age_int, gender, blood_group, dob_str,
                                    contact, email, address, doctor))
                    st.success("✅ Patient registered successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # View All Patients
    elif menu == "View All Patients":
        st.subheader("📋 All Registered Patients")
        try:
            data = get_all_patients()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No patients registered yet.")
        except Exception as e:
            st.error(f"❌ Error fetching patients: {e}")

    # View Medical History
    elif menu == "View Medical History":
        st.subheader("📖 Medical History Records")
        try:
            appointments = get_current_appointments()
            rfid_list = [row['RFID_No'] for row in appointments if row.get('RFID_No')]
            if rfid_list:
                selected_rfid = st.selectbox("Select RFID to view history", rfid_list)
                if selected_rfid:
                    data = get_medical_history_by_rfid(selected_rfid)
                    if data:
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning(f"No history found for RFID {selected_rfid}")
            else:
                st.info("No RFID numbers found in current appointments.")
        except Exception as e:
            st.error(f"❌ Error fetching history: {e}")

    # Current Appointments
    elif menu == "Current Appointments":
        st.subheader("📅 Current Appointments")
        try:
            appointments = get_current_appointments()
            if appointments:
                df = pd.DataFrame(appointments)

                # Check necessary columns
                if {'RFID_No', 'Date_Time', 'Status'}.issubset(df.columns):
                    for i, row in df.iterrows():
                        cols = st.columns([3, 3, 2, 2])
                        cols[0].write(f"**RFID:** {row['RFID_No']}")
                        cols[1].write(f"**Date & Time:** {row['Date_Time']}")

                        # Safely parse status
                        status_raw = row.get('Status', 0)
                        try:
                            status_value = int(status_raw)
                        except:
                            status_value = 0

                        if status_value == 1:
                            status_str = "🟢 Active"
                        else:
                            status_str = "🔴 Inactive"

                        cols[2].write(f"**Status:** {status_str}")

                        # Show update button only if status == 1
                        if status_value == 1:
                            if cols[3].button("Update", key=f"update_btn_{i}_{row['RFID_No']}"):
                                success = delete_appointment_by_rfid(row['RFID_No'])
                                if success:
                                    st.success(f"✅ Appointment with RFID {row['RFID_No']} deleted.")
                                    st.rerun()  # ✅ FIXED
                                else:
                                    st.error(f"❌ Failed to delete appointment with RFID {row['RFID_No']}.")
                        else:
                            cols[3].write("")  # blank if status != 1
                else:
                    st.warning("Expected columns not found in appointments data.")
                    st.dataframe(df)
            else:
                st.info("No current appointments found.")
        except Exception as e:
            st.error(f"❌ Error fetching appointments: {e}")

    # Logout
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out successfully.")
        st.rerun()  # ✅ FIXED

# -------------------- Login Page --------------------
def login_page():
    st.title("🩺 Doctor Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "doctor" and password == "0987":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful")
            st.rerun()  # ✅ FIXED
        else:
            st.error("❌ Invalid credentials")

# -------------------- Session --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# -------------------- Start --------------------
if st.session_state.logged_in:
    dashboard()
else:
    login_page()
