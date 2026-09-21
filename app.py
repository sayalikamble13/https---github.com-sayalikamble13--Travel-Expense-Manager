from datetime import date
from io import BytesIO

import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import pooling
import numpy as np
import pandas as pd
import streamlit as st


# ==============================================================================
# 1. APPLICATION & PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Travel Expense Manager",
    page_icon="✈️",
    layout="wide"
)

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Prem@1326"
DB_NAME = "travel_expense_manager"

# Admin login
ADMIN_USERNAME = "sayalik"
ADMIN_PASSWORD = "Sau@1303"

CATEGORIES = [
    "Flights",
    "Transport",
    "Accommodation",
    "Food",
    "Activities",
    "Shopping",
    "Fuel",
    "Visa",
    "Travel Insurance",
    "Medical",
    "Entertainment",
    "Communication",
    "Emergency",
    "Other",
]

PAYMENT_METHODS = [
    "Cash",
    "Card",
    "UPI",
    "Bank Transfer",
    "Wallet",
    "Other",
]


# ==============================================================================
# 2. LOGIN / ACCESS CONTROL
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "access_type" not in st.session_state:
    st.session_state.access_type = None


def login_screen():

    st.markdown(
        """
        <div class="login-box">
            <h1>✈️ Travel Expense Manager</h1>
            <p>Select your access type</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    access = st.radio(
        "Access Type",
        ["User", "Admin"],
        horizontal=True
    )

    # --------------------------------------------------------------------------
    # USER LOGIN
    # --------------------------------------------------------------------------

    if access == "User":

        st.info(
            "User access does not require a password."
        )

        if st.button(
            "👤 Continue as User",
            use_container_width=True
        ):

            st.session_state.logged_in = True
            st.session_state.access_type = "User"

            st.rerun()

    # --------------------------------------------------------------------------
    # ADMIN LOGIN
    # --------------------------------------------------------------------------

    else:

        username = st.text_input(
            "Admin Username"
        )

        password = st.text_input(
            "Admin Password",
            type="password"
        )

        if st.button(
            "🔐 Admin Login",
            use_container_width=True
        ):

            if (
                username == ADMIN_USERNAME
                and password == ADMIN_PASSWORD
            ):

                st.session_state.logged_in = True
                st.session_state.access_type = "Admin"

                st.success(
                    "✅ Admin login successful!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid admin username or password."
                )


# ==============================================================================
# LOGIN PAGE CSS
# ==============================================================================

st.markdown(
    """
    <style>

    .login-box {
        padding: 35px;
        border-radius: 25px;
        margin-bottom: 30px;
        text-align: center;

        background:
        linear-gradient(
            100deg,
            #8e24aa,
            #f57c00,
            #ffb74d
        );
    }

    .login-box h1 {
        color: white !important;
        font-weight: 900 !important;
        font-size: 38px !important;
    }

    .login-box p {
        color: white !important;
        font-weight: 900 !important;
        font-size: 18px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==============================================================================
# SHOW LOGIN PAGE
# ==============================================================================

if not st.session_state.logged_in:

    login_screen()

    st.stop()


# ==============================================================================
# 3. DATABASE OPERATIONS & CONNECTION POOLING
# ==============================================================================

@st.cache_resource
def get_connection_pool():

    return pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def db():

    return get_connection_pool().get_connection()


def setup_database():

    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(30) NOT NULL,
            email VARCHAR(30),
            phone VARCHAR(10),
            city VARCHAR(10),
            passport_number VARCHAR(8)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            person_id INT NULL,
            expense_date DATE,
            description VARCHAR(255),
            category VARCHAR(100),
            amount DECIMAL(10,2),
            payment_method VARCHAR(50),
            FOREIGN KEY (person_id)
            REFERENCES people(id)
            ON DELETE CASCADE
        )
    """)

    con.commit()

    cur.close()
    con.close()


def get_people():

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT
            id,
            full_name,
            email,
            phone,
            city,
            passport_number
        FROM people
        ORDER BY full_name
    """)

    rows = cur.fetchall()

    cur.close()
    con.close()

    df = pd.DataFrame(
        rows,
        columns=[
            "DB_ID",
            "Full Name",
            "Email",
            "Phone",
            "City",
            "Passport Number"
        ],
    )

    if not df.empty:

        df.insert(
            0,
            "S.No",
            range(1, len(df) + 1)
        )

    return df


def add_person(
    name,
    email,
    phone,
    city,
    passport
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO people
        (
            full_name,
            email,
            phone,
            city,
            passport_number
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            name,
            email,
            phone,
            city,
            passport
        )
    )

    con.commit()

    cur.close()
    con.close()


def update_person(
    person_id,
    name,
    email,
    phone,
    city,
    passport
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        UPDATE people

        SET
            full_name=%s,
            email=%s,
            phone=%s,
            city=%s,
            passport_number=%s

        WHERE id=%s
        """,
        (
            name,
            email,
            phone,
            city,
            passport,
            person_id
        )
    )

    con.commit()

    cur.close()
    con.close()


def delete_person(person_id):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        DELETE FROM people
        WHERE id=%s
        """,
        (person_id,)
    )

    con.commit()

    cur.close()
    con.close()


def get_expenses(person_id=None):

    con = db()
    cur = con.cursor()

    query = """
        SELECT
            expenses.id,
            people.full_name,
            expenses.expense_date,
            expenses.description,
            expenses.category,
            expenses.amount,
            expenses.payment_method,
            expenses.person_id

        FROM expenses

        LEFT JOIN people
        ON people.id = expenses.person_id
    """

    if person_id is not None:

        query += """
            WHERE expenses.person_id = %s
        """

        cur.execute(
            query + """
                ORDER BY expenses.expense_date DESC
            """,
            (person_id,)
        )

    else:

        cur.execute(
            query + """
                ORDER BY expenses.expense_date DESC
            """
        )

    rows = cur.fetchall()

    cur.close()
    con.close()

    data = pd.DataFrame(
        rows,
        columns=[
            "DB_ID",
            "Person",
            "Date",
            "Description",
            "Category",
            "Amount",
            "Payment Method",
            "Person ID"
        ]
    )

    if not data.empty:

        data["Amount"] = data["Amount"].astype(float)

        data.insert(
            0,
            "S.No",
            range(1, len(data) + 1)
        )

    return data


def add_expense(
    person_id,
    expense_date,
    description,
    category,
    amount,
    payment
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO expenses
        (
            person_id,
            expense_date,
            description,
            category,
            amount,
            payment_method
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            person_id,
            expense_date,
            description,
            category,
            amount,
            payment
        )
    )

    con.commit()

    cur.close()
    con.close()


def update_expense(
    expense_id,
    person_id,
    expense_date,
    description,
    category,
    amount,
    payment
):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        UPDATE expenses

        SET
            person_id=%s,
            expense_date=%s,
            description=%s,
            category=%s,
            amount=%s,
            payment_method=%s

        WHERE id=%s
        """,
        (
            person_id,
            expense_date,
            description,
            category,
            amount,
            payment,
            expense_id
        )
    )

    con.commit()

    cur.close()
    con.close()


def delete_expense(expense_id):

    con = db()
    cur = con.cursor()

    cur.execute(
        """
        DELETE FROM expenses
        WHERE id=%s
        """,
        (expense_id,)
    )

    con.commit()

    cur.close()
    con.close()


# ==============================================================================
# 4. HELPER FUNCTIONS
# ==============================================================================

def validate_person_input(
    name,
    email,
    phone,
    city,
    passport
):

    if not name.strip():

        return "Full Name cannot be empty."

    if len(name) > 30:

        return "Full Name must not exceed 30 characters."

    if email and len(email) > 30:

        return "Email must not exceed 30 characters."

    if phone and (
        not phone.isdigit()
        or len(phone) > 10
    ):

        return (
            "Phone number must contain digits only "
            "and not exceed 10 digits."
        )

    if city and len(city) > 10:

        return "City must not exceed 10 characters."

    if passport:

        p = passport.strip()

        if (
            len(p) != 8
            or not p[0].isalpha()
            or not p[1:].isdigit()
        ):

            return (
                "Passport must be 8 characters: "
                "1 Letter followed by 7 Digits "
                "(e.g., A1234567)."
            )

    return None


def money(value):

    return f"₹ {value:,.2f}"


def excel_file(data):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        data.to_excel(
            writer,
            index=False,
            sheet_name="Travel Expenses"
        )

    return output.getvalue()


def safe_index(lst, value):

    try:

        return lst.index(value)

    except ValueError:

        return 0


# ==============================================================================
# 5. DATABASE INITIALIZATION
# ==============================================================================

setup_database()


# ==============================================================================
# 6. GLOBAL CSS
# ==============================================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        linear-gradient(
            135deg,
            #f3e5f5,
            #fff3e0,
            #ffe0b2
        );
    }

    [data-testid="stSidebar"] {
        background:
        linear-gradient(
            180deg,
            #e1bee7,
            #ffe0b2,
            #ffcc80
        );
    }

    .stApp *,
    [data-testid="stSidebar"] *,
    label,
    p,
    span,
    div,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    input,
    select,
    button,
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    .stMarkdown {

        color: #000000 !important;
        font-weight: 900 !important;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="calendar"],
    div[role="dialog"],
    .stNumberInput input,
    .stTextInput input,
    .stDateInput input,
    .stSelectbox > div > div,
    div[data-testid="stForm"],
    .stTabs [data-baseweb="tab-panel"],
    .stDownloadButton,
    .stDownloadButton > button {

        background: #ffffff !important;
        border: 2px solid #ce93d8 !important;
        border-radius: 10px !important;
    }

    .stNumberInput input,
    .stTextInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div {

        color: #000000 !important;
    }

    [data-baseweb="calendar"] button {

        background: #f3e5f5 !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] div,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] > div,
    div[data-baseweb="menu"] ul,
    ul[role="listbox"],
    ul[role="listbox"] > div,
    div[data-testid="stSelectboxVirtualDropdown"],
    div[data-testid="stSelectboxVirtualDropdown"] * {

        background: #ffffff !important;
        color: #000000 !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"],
    div[data-testid="stSelectboxVirtualDropdown"] {

        border: 2px solid #ce93d8 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    li[role="option"],
    div[data-baseweb="menu"] li,
    div[data-testid="stSelectboxVirtualDropdown"] li {

        background: #ffffff !important;
        color: #000000 !important;
        font-weight: 900 !important;
    }

    li[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[data-baseweb="menu"] li:hover,
    div[data-testid="stSelectboxVirtualDropdown"] li:hover,
    div[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] {

        background:
        linear-gradient(
            90deg,
            #8e24aa,
            #f57c00
        ) !important;

        color: #ffffff !important;
    }

    li[role="option"]:hover *,
    li[role="option"][aria-selected="true"] *,
    div[data-testid="stSelectboxVirtualDropdown"] li:hover *,
    div[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] * {

        color: #ffffff !important;
    }

    div[data-baseweb="calendar"] [aria-selected="true"],
    div[data-baseweb="calendar"] button[aria-selected="true"] {

        background:
        linear-gradient(
            90deg,
            #8e24aa,
            #f57c00
        ) !important;

        color: #ffffff !important;
    }

    div[data-baseweb="calendar"] [aria-selected="true"] *,
    div[data-baseweb="calendar"] button[aria-selected="true"] * {

        color: #ffffff !important;
    }

    [data-testid="stSidebar"] .stRadio label {

        background:
        linear-gradient(
            135deg,
            #f3e5f5 0%,
            #ffe0b2 100%
        ) !important;

        border-left:
        6px solid #ab47bc !important;

        border-radius: 12px;

        padding: 10px;

        margin: 6px 0;
    }

    .hero {

        padding: 30px;

        border-radius: 25px;

        margin-bottom: 25px;

        background:
        linear-gradient(
            100deg,
            #8e24aa,
            #f57c00,
            #ffb74d
        );
    }

    .hero h1 {

        color: white !important;
        font-weight: 900 !important;
    }

    .section-title {

        color: black !important;
        font-weight: 900 !important;

        border-left:
        8px solid #f57c00;

        padding-left: 12px;
    }

    .eyebrow {

        color: #8e24aa !important;
        font-weight: 900 !important;
    }

    [data-testid="stMetric"] {

        background:
        linear-gradient(
            135deg,
            #f3e5f5 0%,
            #ffe0b2 100%
        ) !important;

        border:
        3px solid #ab47bc !important;

        border-radius: 16px;

        box-shadow:
        4px 4px 0 #f57c00;
    }

    .stButton > button,
    .stFormSubmitButton > button {

        background:
        linear-gradient(
            90deg,
            #8e24aa,
            #f57c00
        ) !important;

        color: white !important;

        font-weight: 900 !important;

        border: 0 !important;

        border-radius: 12px !important;
    }

    .profile-metric-font {

        font-size: 16px !important;
        font-weight: 900 !important;
    }

    .profile-info-font {

        font-size: 15px !important;
        font-weight: 900 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==============================================================================
# 7. HEADER
# ==============================================================================

st.markdown(
    """
    <div class="hero">
        <h1>✈️ Travel Expense Manager</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# ==============================================================================
# 8. SIDEBAR USER INFORMATION
# ==============================================================================

if st.session_state.access_type == "Admin":

    st.sidebar.success(
        "🔐 Logged in as ADMIN"
    )

else:

    st.sidebar.info(
        "👤 Logged in as USER"
    )


if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):

    st.session_state.logged_in = False
    st.session_state.access_type = None

    st.rerun()


# ==============================================================================
# 9. FETCH PEOPLE
# ==============================================================================

people = get_people()

person_options = (
    {
        f"{row['S.No']} - {row['Full Name']}":
        row["DB_ID"]

        for _, row in people.iterrows()
    }

    if not people.empty

    else {}
)


# ==============================================================================
# 10. NAVIGATION
# ==============================================================================

# ADMIN HAS ALL OPTIONS
if st.session_state.access_type == "Admin":

    navigation_options = [
        "Add Person",
        "People Directory",
        "Add Expense",
        "View Expenses",
        "Categories",
        "Reports",
        "Budget Prediction",
        "Manage Expenses",
        "Person Profile",
        "Download Excel",
    ]

# USER HAS ONLY VIEW OPTIONS
else:

    navigation_options = [
        "View Expenses",
        "Categories",
        "Reports",
        "Budget Prediction",
        "Person Profile",
        "Download Excel",
    ]


page = st.sidebar.radio(
    "Navigate",
    navigation_options
)


# ==============================================================================
# PAGE 1: ADD PERSON
# ADMIN ONLY
# ==============================================================================

if page == "Add Person":

    if st.session_state.access_type != "Admin":

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.markdown(
        '<p class="eyebrow">STEP 1</p>'
        '<h2 class="section-title">Add Person</h2>',
        unsafe_allow_html=True
    )


    with st.form(
        "person_form",
        clear_on_submit=True
    ):

        name = st.text_input(
            "Full Name (Max 30 chars)",
            max_chars=30
        )

        email = st.text_input(
            "Email (Max 30 chars)",
            max_chars=30
        )

        phone = st.text_input(
            "Phone (Max 10 digits)",
            max_chars=10
        )

        city = st.text_input(
            "City (Max 10 chars)",
            max_chars=10
        )

        passport = st.text_input(
            "Passport (1 Letter + 7 Digits, e.g., A1234567)",
            max_chars=8
        )

        save = st.form_submit_button(
            "👤 Save Person"
        )


    if save:

        error = validate_person_input(
            name,
            email,
            phone,
            city,
            passport
        )

        if error:

            st.error(error)

        else:

            add_person(
                name.strip(),
                email.strip(),
                phone.strip(),
                city.strip(),
                passport.strip().upper()
            )

            st.success(
                "✅ Person added successfully!"
            )

            st.rerun()


# ==============================================================================
# PAGE 2: PEOPLE DIRECTORY
# ADMIN ONLY
# ==============================================================================

elif page == "People Directory":

    if st.session_state.access_type != "Admin":

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.markdown(
        '<p class="eyebrow">STEP 2</p>'
        '<h2 class="section-title">People Directory</h2>',
        unsafe_allow_html=True
    )


    if not people.empty:

        display_people = people.drop(
            columns=["DB_ID"]
        )

        st.dataframe(
            display_people,
            use_container_width=True,
            hide_index=True
        )


        col1, col2 = st.columns(2)


        # EDIT PERSON

        with col1:

            st.markdown("---")

            st.subheader(
                "✏️ Edit Person"
            )

            selected_edit_person = st.selectbox(
                "Select Person to Edit",
                list(person_options.keys()),
                key="edit_p"
            )

            selected_db_id = person_options[
                selected_edit_person
            ]

            p_row = people[
                people["DB_ID"] == selected_db_id
            ].iloc[0]


            with st.form(
                "edit_person_form"
            ):

                e_name = st.text_input(
                    "Full Name (Max 30 chars)",
                    value=p_row["Full Name"],
                    max_chars=30
                )

                e_email = st.text_input(
                    "Email (Max 30 chars)",
                    value=p_row["Email"] or "",
                    max_chars=30
                )

                e_phone = st.text_input(
                    "Phone (Max 10 digits)",
                    value=p_row["Phone"] or "",
                    max_chars=10
                )

                e_city = st.text_input(
                    "City (Max 10 chars)",
                    value=p_row["City"] or "",
                    max_chars=10
                )

                e_passport = st.text_input(
                    "Passport (1 Letter + 7 Digits)",
                    value=p_row["Passport Number"] or "",
                    max_chars=8
                )

                update_p = st.form_submit_button(
                    "💾 Save Changes"
                )


            if update_p:

                error = validate_person_input(
                    e_name,
                    e_email,
                    e_phone,
                    e_city,
                    e_passport
                )

                if error:

                    st.error(error)

                else:

                    update_person(
                        selected_db_id,
                        e_name.strip(),
                        e_email.strip(),
                        e_phone.strip(),
                        e_city.strip(),
                        e_passport.strip().upper()
                    )

                    st.success(
                        "✅ Person details updated successfully!"
                    )

                    st.rerun()


        # DELETE PERSON

        with col2:

            st.markdown("---")

            st.subheader(
                "🗑️ Remove Person"
            )

            selected_remove_person = st.selectbox(
                "Select Person to Remove",
                list(person_options.keys()),
                key="del_p"
            )


            if st.button(
                "❌ Delete Selected Person"
            ):

                delete_person(
                    person_options[
                        selected_remove_person
                    ]
                )

                st.success(
                    "✅ Person and associated records deleted successfully!"
                )

                st.rerun()


    else:

        st.info(
            "No people added yet."
        )


# ==============================================================================
# PAGE 3: ADD EXPENSE
# ADMIN ONLY
# ==============================================================================

elif page == "Add Expense":

    if st.session_state.access_type != "Admin":

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.markdown(
        '<p class="eyebrow">STEP 3</p>'
        '<h2 class="section-title">Add Expense</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.warning(
            "Add a person first."
        )

    else:

        person_keys = list(
            person_options.keys()
        )


        if (
            "selected_person_expense"
            not in st.session_state
            or
            st.session_state[
                "selected_person_expense"
            ] not in person_keys
        ):

            st.session_state[
                "selected_person_expense"
            ] = person_keys[0]


        selected_p = st.selectbox(
            "Select Person",
            person_keys,
            index=person_keys.index(
                st.session_state[
                    "selected_person_expense"
                ]
            ),
            key="person_select_dropdown"
        )


        st.session_state[
            "selected_person_expense"
        ] = selected_p


        with st.form(
            "expense_form",
            clear_on_submit=True
        ):

            st.write(
                f"Adding expense for: **{selected_p}**"
            )

            expense_date = st.date_input(
                "Expense Date",
                date.today()
            )

            description = st.text_input(
                "Description"
            )

            category = st.selectbox(
                "Category",
                CATEGORIES
            )

            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=10.0
            )

            payment = st.selectbox(
                "Payment Method",
                PAYMENT_METHODS
            )

            save = st.form_submit_button(
                "💾 Save Expense"
            )


        if save:

            if (
                description.strip()
                and amount > 0
            ):

                add_expense(
                    person_options[selected_p],
                    expense_date,
                    description,
                    category,
                    amount,
                    payment
                )

                st.success(
                    "✅ Expense saved successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "Please provide a description "
                    "and an amount greater than 0."
                )


# ==============================================================================
# PAGE 4: VIEW EXPENSES
# USER + ADMIN
# ==============================================================================

elif page == "View Expenses":

    st.markdown(
        '<p class="eyebrow">EXPENSES</p>'
        '<h2 class="section-title">View Expenses</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.info(
            "No people found."
        )

    else:

        filter_options = (
            ["All People"]
            + list(person_options.keys())
        )


        selected_filter = st.selectbox(
            "🔍 Filter Expenses by Person",
            filter_options
        )


        if selected_filter == "All People":

            expenses = get_expenses()

        else:

            p_id = person_options[
                selected_filter
            ]

            expenses = get_expenses(
                p_id
            )


        if expenses.empty:

            st.info(
                "No expenses found."
            )

        else:

            c1, c2, c3 = st.columns(3)


            c1.metric(
                "Total Spending",
                money(
                    expenses["Amount"].sum()
                )
            )


            c2.metric(
                "Total Expenses",
                len(expenses)
            )


            c3.metric(
                "People Count",
                expenses["Person"].nunique()
            )


            st.dataframe(
                expenses.drop(
                    columns=[
                        "DB_ID",
                        "Person ID"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )


# ==============================================================================
# PAGE 5: CATEGORIES
# USER + ADMIN
# ==============================================================================

elif page == "Categories":

    st.markdown(
        '<p class="eyebrow">ANALYTICS</p>'
        '<h2 class="section-title">Categories</h2>',
        unsafe_allow_html=True
    )


    expenses = get_expenses()


    summary = pd.DataFrame(
        {
            "Category": CATEGORIES
        }
    )


    if not expenses.empty:

        totals = (
            expenses
            .groupby(
                "Category",
                as_index=False
            )["Amount"]
            .sum()
        )

        summary = (
            summary
            .merge(
                totals,
                on="Category",
                how="left"
            )
            .fillna(0)
        )

    else:

        summary["Amount"] = 0.0


    summary.insert(
        0,
        "S.No",
        range(1, len(summary) + 1)
    )


    summary_display = summary.copy()

    summary_display["Amount"] = (
        summary_display["Amount"]
        .apply(
            lambda x:
            f"₹ {x:,.2f}"
        )
    )


    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True
    )


    st.markdown("---")

    st.subheader(
        "📊 Category Visualization"
    )


    c1, c2 = st.columns(2)


    with c1:

        chart_type = st.selectbox(
            "Select Graph Style",
            [
                "Bar Chart",
                "Line Chart",
                "Area Chart",
                "Scatter Plot"
            ]
        )


    with c2:

        chart_color = st.color_picker(
            "Pick Graph Color",
            "#8e24aa"
        )


    fig, ax = plt.subplots(
        figsize=(10, 4)
    )


    if chart_type == "Bar Chart":

        ax.bar(
            summary["Category"],
            summary["Amount"],
            color=chart_color
        )


    elif chart_type == "Line Chart":

        ax.plot(
            summary["Category"],
            summary["Amount"],
            color=chart_color,
            marker="o",
            linewidth=2
        )


    elif chart_type == "Area Chart":

        ax.fill_between(
            range(len(summary)),
            summary["Amount"],
            color=chart_color,
            alpha=0.6
        )

        ax.plot(
            range(len(summary)),
            summary["Amount"],
            color=chart_color
        )

        ax.set_xticks(
            range(len(summary))
        )

        ax.set_xticklabels(
            summary["Category"],
            rotation=45,
            ha="right"
        )


    elif chart_type == "Scatter Plot":

        ax.scatter(
            summary["Category"],
            summary["Amount"],
            color=chart_color,
            s=100
        )


    plt.xticks(
        rotation=45,
        ha="right"
    )

    ax.set_ylabel(
        "Amount (₹)"
    )

    st.pyplot(fig)


# ==============================================================================
# PAGE 6: REPORTS
# USER + ADMIN
# ==============================================================================

elif page == "Reports":

    st.markdown(
        '<p class="eyebrow">ANALYTICS</p>'
        '<h2 class="section-title">Reports & Advanced Analytics</h2>',
        unsafe_allow_html=True
    )


    expenses = get_expenses()


    if not expenses.empty:

        col_c1, col_c2 = st.columns(2)


        with col_c1:

            report_style = st.selectbox(
                "Select Report Graph Type",
                [
                    "Horizontal Bar",
                    "Polar Rose Chart",
                    "Category Donut Chart",
                    "Payment Stacked Bar"
                ]
            )


        with col_c2:

            base_color = st.color_picker(
                "Pick Report Accent Color",
                "#8e24aa"
            )


        fig, ax = plt.subplots(
            figsize=(10, 5)
        )


        if report_style == "Horizontal Bar":

            report = (
                expenses
                .groupby("Category")["Amount"]
                .sum()
                .sort_values()
            )

            ax.barh(
                report.index,
                report.values,
                color=base_color
            )

            ax.set_xlabel(
                "Total Amount (₹)"
            )


        elif report_style == "Polar Rose Chart":

            fig.clear()

            report = (
                expenses
                .groupby("Category")["Amount"]
                .sum()
            )

            angles = np.linspace(
                0,
                2 * np.pi,
                len(report),
                endpoint=False
            )

            ax = fig.add_subplot(
                111,
                polar=True
            )

            ax.bar(
                angles,
                report.values,
                color=base_color,
                alpha=0.7,
                width=0.3
            )

            ax.set_xticks(
                angles
            )

            ax.set_xticklabels(
                report.index
            )


        elif report_style == "Category Donut Chart":

            report = (
                expenses
                .groupby("Category")["Amount"]
                .sum()
            )

            ax.pie(
                report.values,
                labels=report.index,
                autopct="%1.1f%%",
                wedgeprops=dict(
                    width=0.4
                )
            )

            ax.axis("equal")


        elif report_style == "Payment Stacked Bar":

            pivoted = (
                expenses
                .pivot_table(
                    index="Category",
                    columns="Payment Method",
                    values="Amount",
                    aggfunc="sum"
                )
                .fillna(0)
            )

            pivoted.plot(
                kind="bar",
                stacked=True,
                ax=ax
            )

            plt.xticks(
                rotation=45,
                ha="right"
            )


        st.pyplot(fig)


    else:

        st.info(
            "No expense data available."
        )


# ==============================================================================
# PAGE 7: BUDGET PREDICTION
# USER + ADMIN
# ==============================================================================

elif page == "Budget Prediction":

    st.markdown(
        '<p class="eyebrow">ANALYTICS</p>'
        '<h2 class="section-title">Budget Prediction</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.info(
            "No people available."
        )

    else:

        selected_p = st.selectbox(
            "Select Person for Budget Forecast",
            list(person_options.keys())
        )


        p_id = person_options[
            selected_p
        ]


        expenses = get_expenses(
            p_id
        )


        if not expenses.empty:

            expenses["Month"] = (
                pd.to_datetime(
                    expenses["Date"]
                )
                .dt
                .to_period("M")
                .astype(str)
            )


            monthly = (
                expenses
                .groupby(
                    "Month",
                    as_index=False
                )["Amount"]
                .sum()
            )


            st.metric(
                "Suggested Budget for Next Month",
                money(
                    monthly["Amount"].mean()
                )
            )


            fig, ax = plt.subplots(
                figsize=(10, 4)
            )


            ax.plot(
                monthly["Month"],
                monthly["Amount"],
                marker="o",
                linewidth=3
            )


            ax.set_xlabel(
                "Month"
            )

            ax.set_ylabel(
                "Total Spending (₹)"
            )

            plt.xticks(
                rotation=45
            )

            st.pyplot(fig)


        else:

            st.info(
                "Add expenses across months "
                "to generate a budget prediction."
            )


# ==============================================================================
# PAGE 8: MANAGE EXPENSES
# ADMIN ONLY
# ==============================================================================

elif page == "Manage Expenses":

    if st.session_state.access_type != "Admin":

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.markdown(
        '<p class="eyebrow">ADMIN</p>'
        '<h2 class="section-title">Manage Expenses</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.info(
            "No people found."
        )

    else:

        selected_person_manage = st.selectbox(
            "Select Person",
            list(person_options.keys())
        )


        p_id = person_options[
            selected_person_manage
        ]


        expenses = get_expenses(
            p_id
        )


        if expenses.empty:

            st.info(
                "No expenses available."
            )

        else:

            options = {
                f"{row['S.No']} - "
                f"{row['Description']} "
                f"(₹{row['Amount']})":
                row["DB_ID"]

                for _, row in expenses.iterrows()
            }


            selected_exp = st.selectbox(
                "Select Expense",
                list(options.keys())
            )


            exp_id = options[
                selected_exp
            ]


            row = expenses[
                expenses["DB_ID"] == exp_id
            ].iloc[0]


            tab1, tab2 = st.tabs(
                [
                    "✏️ Edit Expense",
                    "🗑️ Delete Expense"
                ]
            )


            with tab1:

                with st.form(
                    "edit_expense_form"
                ):

                    edit_date = st.date_input(
                        "Date",
                        pd.to_datetime(
                            row["Date"]
                        ).date()
                    )


                    description = st.text_input(
                        "Description",
                        row["Description"]
                    )


                    category = st.selectbox(
                        "Category",
                        CATEGORIES,
                        index=safe_index(
                            CATEGORIES,
                            row["Category"]
                        )
                    )


                    amount = st.number_input(
                        "Amount (₹)",
                        value=float(
                            row["Amount"]
                        ),
                        min_value=0.0
                    )


                    payment = st.selectbox(
                        "Payment Method",
                        PAYMENT_METHODS,
                        index=safe_index(
                            PAYMENT_METHODS,
                            row["Payment Method"]
                        )
                    )


                    update_btn = st.form_submit_button(
                        "💾 Save Changes"
                    )


                if update_btn:

                    update_expense(
                        exp_id,
                        p_id,
                        edit_date,
                        description,
                        category,
                        amount,
                        payment
                    )

                    st.success(
                        "✅ Expense updated successfully!"
                    )

                    st.rerun()


            with tab2:

                st.warning(
                    f"Delete expense: "
                    f"{row['Description']}?"
                )


                if st.button(
                    "🗑️ Confirm Delete"
                ):

                    delete_expense(
                        exp_id
                    )

                    st.success(
                        "✅ Expense deleted successfully!"
                    )

                    st.rerun()


# ==============================================================================
# PAGE 9: PERSON PROFILE
# USER + ADMIN
# ==============================================================================

elif page == "Person Profile":

    st.markdown(
        '<p class="eyebrow">PROFILE</p>'
        '<h2 class="section-title">Person Profile</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.info(
            "No people available."
        )

    else:

        selected = st.selectbox(
            "Select Person",
            list(person_options.keys())
        )


        person_id = person_options[
            selected
        ]


        profile = people[
            people["DB_ID"] == person_id
        ].iloc[0]


        person_expenses = get_expenses(
            person_id
        )


        st.subheader(
            f"👤 {profile['Full Name']}"
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.markdown(
                f"""
                <div class="profile-metric-font">
                    City<br>
                    <b>
                        {profile["City"] or "Not added"}
                    </b>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c2:

            st.markdown(
                f"""
                <div class="profile-metric-font">
                    Phone<br>
                    <b>
                        {profile["Phone"] or "Not added"}
                    </b>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c3:

            total_exp = (
                money(
                    person_expenses["Amount"].sum()
                )
                if not person_expenses.empty
                else "₹ 0.00"
            )


            st.markdown(
                f"""
                <div class="profile-metric-font">
                    Total Expenses<br>
                    <b>{total_exp}</b>
                </div>
                """,
                unsafe_allow_html=True
            )


        st.markdown(
            f"""
            <p class="profile-info-font">
                <b>Email:</b>
                {profile["Email"] or "Not added"}
            </p>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <p class="profile-info-font">
                <b>Passport Number:</b>
                {profile["Passport Number"] or "Not added"}
            </p>
            """,
            unsafe_allow_html=True
        )


        if person_expenses.empty:

            st.info(
                "This person has no expenses."
            )

        else:

            st.subheader(
                "📋 Expense History"
            )


            st.dataframe(
                person_expenses.drop(
                    columns=[
                        "DB_ID",
                        "Person ID"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )


            person_expenses["Month"] = (
                pd.to_datetime(
                    person_expenses["Date"]
                )
                .dt
                .to_period("M")
                .astype(str)
            )


            monthly = (
                person_expenses
                .groupby(
                    "Month",
                    as_index=False
                )["Amount"]
                .sum()
            )


            st.subheader(
                "📈 Personal Analytics"
            )


            fig1, ax1 = plt.subplots()


            ax1.plot(
                monthly["Month"],
                monthly["Amount"],
                marker="o",
                linewidth=2
            )


            ax1.set_ylabel(
                "Amount (₹)"
            )


            plt.xticks(
                rotation=45
            )


            st.pyplot(fig1)


            pie_data = (
                person_expenses
                .groupby(
                    "Category",
                    as_index=False
                )["Amount"]
                .sum()
            )


            fig2, ax2 = plt.subplots()


            ax2.pie(
                pie_data["Amount"],
                labels=pie_data["Category"],
                autopct="%1.1f%%",
                startangle=90
            )


            ax2.axis("equal")

            st.pyplot(fig2)


# ==============================================================================
# PAGE 10: DOWNLOAD EXCEL
# USER + ADMIN
# ==============================================================================

elif page == "Download Excel":

    st.markdown(
        '<p class="eyebrow">DOWNLOAD</p>'
        '<h2 class="section-title">Download Excel</h2>',
        unsafe_allow_html=True
    )


    if not person_options:

        st.info(
            "No people available."
        )

    else:

        # ALL PEOPLE + INDIVIDUAL PEOPLE

        download_options = (
            ["All People"]
            + list(person_options.keys())
        )


        selected_download_person = st.selectbox(
            "👥 Select People",
            download_options,
            key="download_person_filter"
        )


        # ----------------------------------------------------------------------
        # ALL PEOPLE
        # ----------------------------------------------------------------------

        if selected_download_person == "All People":

            download_expenses = get_expenses()

            file_name = (
                "travel_expenses_all_people.xlsx"
            )


        # ----------------------------------------------------------------------
        # INDIVIDUAL PERSON
        # ----------------------------------------------------------------------

        else:

            selected_person_id = person_options[
                selected_download_person
            ]


            download_expenses = get_expenses(
                selected_person_id
            )


            selected_name = (
                selected_download_person
                .split(" - ", 1)[-1]
            )


            safe_name = "".join(
                ch
                for ch in selected_name
                if ch.isalnum()
                or ch in (" ", "_", "-")
            ).strip().replace(
                " ",
                "_"
            )


            file_name = (
                f"travel_expenses_{safe_name}.xlsx"
            )


        # ----------------------------------------------------------------------
        # NO DATA
        # ----------------------------------------------------------------------

        if download_expenses.empty:

            st.warning(
                "⚠️ No expense records found "
                "for the selected option."
            )


        # ----------------------------------------------------------------------
        # DATA AVAILABLE
        # ----------------------------------------------------------------------

        else:

            download_data = download_expenses.drop(
                columns=[
                    "DB_ID",
                    "Person ID"
                ]
            )


            st.success(
                f"✅ {len(download_data)} "
                f"expense record(s) ready for download."
            )


            st.dataframe(
                download_data,
                use_container_width=True,
                hide_index=True
            )


            st.metric(
                "Total Spending",
                money(
                    download_data["Amount"].sum()
                )
            )


            st.download_button(
                "📥 Download Excel File",
                data=excel_file(
                    download_data
                ),
                file_name=file_name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="download_excel_button",
                use_container_width=True
            )
