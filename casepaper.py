import streamlit as st
import mysql.connector
import pandas as pd

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
    (Name, RFIDNO, Age, Gender, BloodGroup, DateofBirth, 
     ContactNo, EmailID, password, Address, DoctorAssigned)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, data)
    conn.commit()
    cursor.close()
    conn.close()

# -------------------- Patient Login --------------------
def check_patient_login(user_input, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT * FROM E_casepatient 
    WHERE (EmailID = %s OR ContactNo = %s) AND password = %s
    """
    cursor.execute(sql, (user_input, user_input, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# -------------------- Fetch All Patients --------------------
def get_all_patients():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM E_casepatient ORDER BY ID DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# -------------------- Fetch Appointments --------------------
def get_current_appointments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM E_Case ORDER BY Date_Time DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# -------------------- Delete Appointment --------------------
def delete_appointment_by_rfid(rfid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM E_Case WHERE RFID_No = %s", (rfid,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0

# -------------------- Fetch Medical History --------------------
def get_medical_history_by_rfid(rfid):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM medical__histroy WHERE RFIDNo = %s ORDER BY ID DESC",
            (rfid,)
        )
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        st.error(f"Error fetching medical history: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# -------------------- Doctor Dashboard --------------------
def doctor_dashboard():
    st.sidebar.title("📌 Doctor Panel")
    menu = st.sidebar.radio("Select Option",
                            ["Register Patient",
                             "View All Patients",
                             "Current Appointments",
                             "Logout"])

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

            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            submitted = st.form_submit_button("Register Patient")

            if submitted:
                try:
                    if password != confirm_password:
                        st.error("Passwords do not match!")
                    elif password == "":
                        st.error("Password cannot be empty!")
                    else:
                        age_int = int(age)
                        dob_str = dob.strftime('%Y-%m-%d')

                        insert_patient((
                            name, rfid, age_int, gender, blood_group,
                            dob_str, contact, email,
                            password, address, doctor
                        ))

                        st.success("Patient registered successfully!")

                except Exception as e:
                    st.error(f"Error: {e}")

    # View All Patients
    elif menu == "View All Patients":
        st.subheader("All Registered Patients")
        data = get_all_patients()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No patients found.")

    # Current Appointments
    elif menu == "Current Appointments":
        st.subheader("Current Appointments")
        data = get_current_appointments()

        if data:
            df = pd.DataFrame(data)
            for i, row in df.iterrows():
                cols = st.columns([3, 3, 2, 2])
                cols[0].write(f"RFID: {row['RFID_No']}")
                cols[1].write(f"Date & Time: {row['Date_Time']}")

                status = int(row.get("Status", 0))
                status_str = "🟢 Active" if status == 1 else "🔴 Inactive"
                cols[2].write(status_str)

                if status == 1:
                    if cols[3].button("Complete", key=i):
                        if delete_appointment_by_rfid(row['RFID_No']):
                            st.success("Appointment Completed")
                            st.rerun()
        else:
            st.info("No appointments found.")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = ""
        st.rerun()

# -------------------- Patient Dashboard --------------------
def patient_dashboard():
    st.sidebar.title("👤 Patient Panel")
    menu = st.sidebar.radio("Select Option",
                            ["My Profile",
                             "Medical History",
                             "Logout"])

    # My Profile
    if menu == "My Profile":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM E_casepatient WHERE ID=%s",
                       (st.session_state.patient_id,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()

        if data:
            st.subheader("My Profile")
            st.write(f"Name: {data['Name']}")
            st.write(f"RFID: {data['RFIDNO']}")
            st.write(f"Age: {data['Age']}")
            st.write(f"Blood Group: {data['BloodGroup']}")
            st.write(f"Doctor Assigned: {data['DoctorAssigned']}")

    # Medical History
    elif menu == "Medical History":
        st.subheader("My Medical History")

        rfid = st.session_state.patient_rfid
        history = get_medical_history_by_rfid(rfid)

        if history:
            st.dataframe(pd.DataFrame(history),
                         use_container_width=True)
        else:
            st.info("No medical history found.")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = ""
        st.session_state.patient_id = None
        st.session_state.patient_rfid = None
        st.rerun()

# -------------------- Login Page --------------------
def login_page():
    st.title("🩺 E-Case Login System")

    role = st.radio("Login As", ["Doctor", "Patient"])

    # Doctor Login
    if role == "Doctor":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "doctor" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = "Doctor"
                st.rerun()
            else:
                st.error("Invalid credentials")

    # Patient Login
    else:
        user_input = st.text_input("Email or Mobile")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = check_patient_login(user_input, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.role = "Patient"
                st.session_state.patient_id = user['ID']
                st.session_state.patient_rfid = user['RFIDNO']
                st.rerun()
            else:
                st.error("Invalid credentials")

# -------------------- Session Initialization --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = ""
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "patient_rfid" not in st.session_state:
    st.session_state.patient_rfid = None

# -------------------- Start App --------------------
if st.session_state.logged_in:
    if st.session_state.role == "Doctor":
        doctor_dashboard()
    else:
        patient_dashboard()
else:
    login_page()

