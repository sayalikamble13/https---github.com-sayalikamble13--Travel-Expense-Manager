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
# 2. DATABASE OPERATIONS & CONNECTION POOLING
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
            "Passport Number",
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
            passport,
        ),
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
            person_id,
        ),
    )

    con.commit()

    cur.close()
    con.close()


def delete_person(person_id):

    con = db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM people WHERE id=%s",
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
            ORDER BY expenses.expense_date DESC
        """

        cur.execute(
            query,
            (person_id,)
        )

    else:

        query += """
            ORDER BY expenses.expense_date DESC
        """

        cur.execute(query)

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
            "Person ID",
        ],
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
            payment,
        ),
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
            expense_id,
        ),
    )

    con.commit()

    cur.close()
    con.close()


def delete_expense(expense_id):

    con = db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM expenses WHERE id=%s",
        (expense_id,)
    )

    con.commit()

    cur.close()
    con.close()


# ==============================================================================
# 3. HELPER FUNCTIONS & VALIDATION
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
# INITIALIZE DATABASE
# ==============================================================================

setup_database()


# ==============================================================================
# 4. GLOBAL CSS STYLING
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


    /* WHITE INPUT BOXES */

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

        border:
        2px solid #ce93d8 !important;

        border-radius: 10px !important;
    }


    /* BLACK INPUT TEXT */

    .stNumberInput input,
    .stTextInput input,
    .stDateInput input,
    .stSelectbox
    div[data-baseweb="select"] > div {

        color: #000000 !important;
    }


    /* CALENDAR */

    [data-baseweb="calendar"] button {

        background: #f3e5f5 !important;

        border-radius: 6px !important;
    }


    /* DROPDOWN */

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

        border:
        2px solid #ce93d8 !important;

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
    div[data-testid="stSelectboxVirtualDropdown"]
    li[aria-selected="true"] {

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
    div[data-testid="stSelectboxVirtualDropdown"]
    li:hover *,
    div[data-testid="stSelectboxVirtualDropdown"]
    li[aria-selected="true"] * {

        color: #ffffff !important;
    }


    /* SELECTED DATE */

    div[data-baseweb="calendar"]
    [aria-selected="true"],
    div[data-baseweb="calendar"]
    button[aria-selected="true"] {

        background:
        linear-gradient(
            90deg,
            #8e24aa,
            #f57c00
        ) !important;

        color: #ffffff !important;
    }


    div[data-baseweb="calendar"]
    [aria-selected="true"] *,
    div[data-baseweb="calendar"]
    button[aria-selected="true"] * {

        color: #ffffff !important;
    }


    /* SIDEBAR RADIO */

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


    /* ==========================================================
       HEADER
       ONLY TRAVEL EXPENSE MANAGER IS SHOWN
       ========================================================== */

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

        font-size: 38px;

        margin: 0;
    }


    /* SECTION TITLE */

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


    /* METRICS */

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


    /* BUTTONS */

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


    /* PROFILE */

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
    unsafe_allow_html=True,
)


# ==============================================================================
# HEADER
# ==============================================================================

st.markdown(
    """
    <div class="hero">
        <h1>✈️ Travel Expense Manager</h1>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# FETCH CURRENT PEOPLE STATE
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
# NAVIGATION SIDEBAR
# ==============================================================================

page = st.sidebar.radio(
    "Navigate",
    [
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
    ],
)


# ==============================================================================
# PAGE 1: ADD PERSON
# ==============================================================================

if page == "Add Person":

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
# ==============================================================================

elif page == "People Directory":

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
                    "✅ Person and associated record deleted successfully!"
                )

                st.rerun()

    else:

        st.info(
            "No people added yet."
        )


# ==============================================================================
# PAGE 3: ADD EXPENSE
# ==============================================================================

elif page == "Add Expense":

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
            "Select Person (Remains Selected for Next Entries)",
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
                    f"✅ Expense saved for {selected_p}!"
                )

                st.rerun()

            else:

                st.error(
                    "Please provide a description "
                    "and an amount greater than 0."
                )

        p_id = person_options[selected_p]

        p_expenses = get_expenses(
            p_id
        )

        if not p_expenses.empty:

            st.markdown("---")

            st.subheader(
                f"📊 Live Spending Insights ({selected_p})"
            )

            g_col1, g_col2 = st.columns(2)

            with g_col1:

                st.write(
                    "**Payment Method Breakdown (Donut Chart)**"
                )

                pay_data = (
                    p_expenses
                    .groupby(
                        "Payment Method",
                        as_index=False
                    )["Amount"]
                    .sum()
                )

                fig_pay, ax_pay = plt.subplots()

                ax_pay.pie(
                    pay_data["Amount"],
                    labels=pay_data[
                        "Payment Method"
                    ],
                    autopct="%1.1f%%",
                    startangle=90,
                    wedgeprops=dict(
                        width=0.4,
                        edgecolor="w"
                    )
                )

                ax_pay.axis("equal")

                st.pyplot(fig_pay)

            with g_col2:

                st.write(
                    "**Daily Expense Distribution (Scatter Plot)**"
                )

                fig_scat, ax_scat = plt.subplots()

                ax_scat.scatter(
                    p_expenses["Date"],
                    p_expenses["Amount"],
                    color="#f57c00",
                    s=p_expenses[
                        "Amount"
                    ] / 2 + 30,
                    alpha=0.7
                )

                plt.xticks(
                    rotation=45
                )

                ax_scat.set_ylabel(
                    "Amount (₹)"
                )

                ax_scat.set_xlabel(
                    "Date"
                )

                st.pyplot(fig_scat)


# ==============================================================================
# PAGE 4: VIEW EXPENSES
# ==============================================================================

elif page == "View Expenses":

    st.markdown(
        '<p class="eyebrow">STEP 4</p>'
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
                "No expenses found for the selected selection."
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
# ==============================================================================

elif page == "Categories":

    st.markdown(
        '<p class="eyebrow">STEP 5</p>'
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
        summary_display[
            "Amount"
        ].apply(
            lambda x:
            f"₹ {x:,.2f}"
        )
    )

    st.dataframe(
        summary_display.style.set_properties(
            **{
                "text-align": "center"
            }
        ),
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
            summary["Category"]
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
# ==============================================================================

elif page == "Reports":

    st.markdown(
        '<p class="eyebrow">STEP 6</p>'
        '<h2 class="section-title">'
        'Reports & Advanced Analytics'
        '</h2>',
        unsafe_allow_html=True
    )

    expenses = get_expenses()

    if not expenses.empty:

        col_c1, col_c2 = st.columns(2)

        with col_c1:

            report_style = st.selectbox(
                "Select Unique Report Graph Type",
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

        st.markdown("---")

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        if report_style == "Horizontal Bar":

            report = (
                expenses
                .groupby("Category")[
                    "Amount"
                ]
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
                .groupby("Category")[
                    "Amount"
                ]
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
                .groupby("Category")[
                    "Amount"
                ]
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
            "No expense data available for reports."
        )


# ==============================================================================
# PAGE 7: BUDGET PREDICTION
# ==============================================================================

elif page == "Budget Prediction":

    st.markdown(
        '<p class="eyebrow">STEP 7</p>'
        '<h2 class="section-title">'
        'Budget Prediction'
        '</h2>',
        unsafe_allow_html=True
    )

    if not person_options:

        st.info(
            "Add a person and expenses first."
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
                .dt.to_period("M")
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

            c1, c2 = st.columns(2)

            with c1:

                p_chart_type = st.selectbox(
                    "Prediction Graph Style",
                    [
                        "Spline Curve",
                        "Stacked Fill Area",
                        "Step Plot",
                        "3D-Style Column"
                    ]
                )

            with c2:

                p_chart_color = st.color_picker(
                    "Chart Primary Accent Color",
                    "#f57c00"
                )

            fig, ax = plt.subplots(
                figsize=(10, 4)
            )

            if p_chart_type == "Spline Curve":

                ax.plot(
                    monthly["Month"],
                    monthly["Amount"],
                    color=p_chart_color,
                    marker="o",
                    linestyle="-",
                    linewidth=3
                )

                ax.grid(
                    True,
                    linestyle="--",
                    alpha=0.5
                )

            elif p_chart_type == "Stacked Fill Area":

                ax.fill_between(
                    range(len(monthly)),
                    monthly["Amount"],
                    color=p_chart_color,
                    alpha=0.4
                )

                ax.plot(
                    range(len(monthly)),
                    monthly["Amount"],
                    color=p_chart_color,
                    linewidth=2
                )

                ax.set_xticks(
                    range(len(monthly))
                )

                ax.set_xticklabels(
                    monthly["Month"]
                )

            elif p_chart_type == "Step Plot":

                ax.step(
                    monthly["Month"],
                    monthly["Amount"],
                    color=p_chart_color,
                    where="mid",
                    linewidth=3
                )

            elif p_chart_type == "3D-Style Column":

                ax.bar(
                    monthly["Month"],
                    monthly["Amount"],
                    color=p_chart_color,
                    edgecolor="black",
                    linewidth=1.5
                )

            ax.set_xlabel(
                "Month"
            )

            ax.set_ylabel(
                "Total Spending (₹)"
            )

            st.pyplot(fig)

        else:

            st.info(
                "Add expenses across months "
                "to generate a budget prediction "
                "for this person."
            )


# ==============================================================================
# PAGE 8: MANAGE EXPENSES
# ==============================================================================

elif page == "Manage Expenses":

    st.markdown(
        '<p class="eyebrow">STEP 8</p>'
        '<h2 class="section-title">'
        'Manage Expenses (Edit / Delete)'
        '</h2>',
        unsafe_allow_html=True
    )

    if not person_options:

        st.info(
            "No people found."
        )

    else:

        selected_person_manage = st.selectbox(
            "Select Person to Manage Expenses",
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
                "No expenses available for this person."
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
                "Select Specific Expense",
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
                    "edit_expense_unified_form"
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

                    cat_idx = safe_index(
                        CATEGORIES,
                        row["Category"]
                    )

                    category = st.selectbox(
                        "Category",
                        CATEGORIES,
                        index=cat_idx
                    )

                    amount = st.number_input(
                        "Amount (₹)",
                        value=float(
                            row["Amount"]
                        ),
                        min_value=0.0
                    )

                    pay_idx = safe_index(
                        PAYMENT_METHODS,
                        row["Payment Method"]
                    )

                    payment = st.selectbox(
                        "Payment Method",
                        PAYMENT_METHODS,
                        index=pay_idx
                    )

                    update_btn = st.form_submit_button(
                        "✏️ Save Expense Changes"
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

                st.write(
                    f"Are you sure you want to delete "
                    f"**'{row['Description']}'**?"
                )

                if st.button(
                    "🗑️ Confirm Delete Expense"
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
# ==============================================================================

elif page == "Person Profile":

    st.markdown(
        '<p class="eyebrow">STEP 9</p>'
        '<h2 class="section-title">'
        'Person Profile'
        '</h2>',
        unsafe_allow_html=True
    )

    if not person_options:

        st.info(
            "Add a person first."
        )

    else:

        selected = st.selectbox(
            "Select Person Profile",
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
                    person_expenses[
                        "Amount"
                    ].sum()
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
            "<br>",
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
                "This person has no expenses registered."
            )

        else:

            st.markdown("---")

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
                .dt.to_period("M")
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

            st.markdown("---")

            st.subheader(
                "📈 Personal Analytics & Charts"
            )

            c1, c2 = st.columns(2)

            with c1:

                prof_chart_type = st.selectbox(
                    "Monthly Trend Graph Type",
                    [
                        "Line Chart",
                        "Bar Chart",
                        "Area Chart"
                    ]
                )

            with c2:

                prof_color = st.color_picker(
                    "Pick Analytics Theme Color",
                    "#8e24aa"
                )

            col_a, col_b = st.columns(2)

            with col_a:

                st.write(
                    "**Monthly Expenses Trend**"
                )

                fig1, ax1 = plt.subplots()

                if prof_chart_type == "Line Chart":

                    ax1.plot(
                        monthly["Month"],
                        monthly["Amount"],
                        color=prof_color,
                        marker="o",
                        linewidth=2
                    )

                elif prof_chart_type == "Bar Chart":

                    ax1.bar(
                        monthly["Month"],
                        monthly["Amount"],
                        color=prof_color
                    )

                elif prof_chart_type == "Area Chart":

                    ax1.fill_between(
                        range(len(monthly)),
                        monthly["Amount"],
                        color=prof_color,
                        alpha=0.5
                    )

                    ax1.plot(
                        range(len(monthly)),
                        monthly["Amount"],
                        color=prof_color
                    )

                    ax1.set_xticks(
                        range(len(monthly))
                    )

                    ax1.set_xticklabels(
                        monthly["Month"]
                    )

                plt.xticks(
                    rotation=45
                )

                ax1.set_ylabel(
                    "Amount (₹)"
                )

                st.pyplot(fig1)

            with col_b:

                st.write(
                    "**Expense Category Breakdown**"
                )

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
                    labels=pie_data[
                        "Category"
                    ],
                    autopct="%1.1f%%",
                    startangle=90
                )

                ax2.axis("equal")

                st.pyplot(fig2)


# ==============================================================================
# PAGE 10: DOWNLOAD EXCEL
# ==============================================================================

elif page == "Download Excel":

    st.markdown(
        '<p class="eyebrow">STEP 10</p>'
        '<h2 class="section-title">'
        'Download Excel'
        '</h2>',
        unsafe_allow_html=True
    )

    if not person_options:

        st.warning(
            "⚠️ Please add a person first."
        )

    else:

        # --------------------------------------------------------------
        # SELECT PERSON
        # --------------------------------------------------------------

        selected_download_person = st.selectbox(
            "👤 Select Person to Download Expenses",
            list(person_options.keys()),
            key="download_person"
        )

        selected_person_id = person_options[
            selected_download_person
        ]

        # --------------------------------------------------------------
        # GET SELECTED PERSON EXPENSES
        # --------------------------------------------------------------

        selected_expenses = get_expenses(
            selected_person_id
        )

        st.markdown("---")

        st.subheader(
            f"📊 Expenses for {selected_download_person}"
        )

        if selected_expenses.empty:

            st.info(
                "ℹ️ No expenses found for this person. "
                "Add expenses first to enable Excel download."
            )

        else:

            # ----------------------------------------------------------
            # SUMMARY
            # ----------------------------------------------------------

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Spending",
                money(
                    selected_expenses[
                        "Amount"
                    ].sum()
                )
            )

            c2.metric(
                "Total Expenses",
                len(selected_expenses)
            )

            c3.metric(
                "Person",
                selected_expenses[
                    "Person"
                ].iloc[0]
            )

            # ----------------------------------------------------------
            # EXPENSE TABLE
            # ----------------------------------------------------------

            download_data = selected_expenses.drop(
                columns=[
                    "DB_ID",
                    "Person ID"
                ]
            )

            st.dataframe(
                download_data,
                use_container_width=True,
                hide_index=True
            )

            # ----------------------------------------------------------
            # DOWNLOAD
            # ----------------------------------------------------------

            st.markdown("---")

            st.subheader(
                "📥 Download Selected Person's Excel File"
            )

            excel_data = excel_file(
                download_data
            )

            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=(
                    f"{selected_expenses['Person'].iloc[0]}"
                    "_travel_expenses.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="download_selected_person_excel",
                disabled=selected_expenses.empty
            )
