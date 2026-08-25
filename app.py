"""
Presidency University Facility Booking System - Demo (Streamlit)
Constraint adhered to: Zero hallucination. All venue names, departments, and document types
are taken strictly from the optimized requirements + official sources where available.
Manik Bandyopadhyay Auditorium is included only because it was explicitly instructed.
Equipment lists are clearly marked DEMO PLACEHOLDERS.
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

# -------------------------------------------------
# Constants & Resources
# -------------------------------------------------
DB_PATH = "bookings.db"
RESOURCES_FILE = "resources.txt"

VENUES = [
    "A. K. Basak Auditorium",
    "P. C. Mahalanobis Auditorium",
    "Derozio Hall",
    "Manik Bandyopadhyay Auditorium",
    "Bankim Sabha Griha",
    "Satyen Bose Sabha Griha",
    "Acharya Prafulla Chandra Roy Auditorium",
]

DEPARTMENTS = [
    "Bengali", "English", "Hindi", "History", "Performing Arts",
    "Philosophy", "Political Science", "Sociology",
    "Chemistry", "Economics", "Geography", "Geology",
    "Life Sciences", "Mathematics", "Physics", "Statistics",
    "School of Astrophysics", "Institute of Health Sciences",
    "Other / Central Office"
]

REQUIRED_DOCS = [
    "Approval from Departmental Head",
    "Approval from Registrar Office",
    "Approval from Development Office",
]

OPTIONAL_DOCS = [
    "Approval from Finance Department"
]

# DEMO PLACEHOLDER equipment only – not real inventory
DEMO_EQUIPMENT = {
    "A. K. Basak Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "P. C. Mahalanobis Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "Derozio Hall": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set", "Stage Lighting (basic)"],
    "Manik Bandyopadhyay Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "Bankim Sabha Griha": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Whiteboard", "Sound System", "Cordless Microphone Set"],
    "Satyen Bose Sabha Griha": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Whiteboard", "Sound System", "Cordless Microphone Set"],
    "Acharya Prafulla Chandra Roy Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
}

# -------------------------------------------------
# Database (SQLite Calendar Backend)
# -------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue TEXT NOT NULL,
            start_dt TEXT NOT NULL,
            end_dt TEXT NOT NULL,
            department TEXT,
            applicant_name TEXT,
            applicant_email TEXT,
            purpose TEXT,
            status TEXT DEFAULT 'Confirmed',
            docs_hod TEXT,
            docs_registrar TEXT,
            docs_development TEXT,
            docs_finance TEXT,
            equip_required INTEGER DEFAULT 0,
            mic_count INTEGER DEFAULT 0,
            other_logistics TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def is_available(venue: str, start_dt: datetime, end_dt: datetime) -> bool:
    """Return True if no overlapping confirmed booking exists for the venue."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Overlap logic: existing.start < new.end AND existing.end > new.start
    c.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE venue = ?
          AND status = 'Confirmed'
          AND start_dt < ?
          AND end_dt > ?
    """, (venue, end_dt.isoformat(), start_dt.isoformat()))
    count = c.fetchone()[0]
    conn.close()
    return count == 0

def save_booking(data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings (
            venue, start_dt, end_dt, department, applicant_name, applicant_email,
            purpose, status, docs_hod, docs_registrar, docs_development, docs_finance,
            equip_required, mic_count, other_logistics, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["venue"],
        data["start_dt"].isoformat(),
        data["end_dt"].isoformat(),
        data["department"],
        data["applicant_name"],
        data["applicant_email"],
        data.get("purpose", ""),
        "Confirmed",
        data.get("docs_hod", ""),
        data.get("docs_registrar", ""),
        data.get("docs_development", ""),
        data.get("docs_finance", ""),
        1 if data.get("equip_required") else 0,
        data.get("mic_count", 0),
        data.get("other_logistics", ""),
        datetime.now().isoformat()
    ))
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def get_all_bookings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, venue, start_dt, end_dt, department, status FROM bookings ORDER BY start_dt")
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------------------------------
# PDF Certificate Generator
# -------------------------------------------------
def generate_certificate(data: dict, booking_id: int) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        fontSize=16, alignment=TA_CENTER, spaceAfter=6, textColor=colors.HexColor("#1a365d")
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle', parent=styles['Normal'],
        fontSize=11, alignment=TA_CENTER, spaceAfter=12
    )
    normal = ParagraphStyle(
        'NormalStyle', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=4
    )
    bold_style = ParagraphStyle(
        'BoldStyle', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=4, fontName='Helvetica-Bold'
    )

    story = []
    story.append(Paragraph("PRESIDENCY UNIVERSITY", title_style))
    story.append(Paragraph("86/1 College Street, Kolkata – 700073", subtitle_style))
    story.append(Paragraph("<b>FACILITY BOOKING – FINAL APPROVAL CERTIFICATE</b>", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Booking ID:</b> PU-FAC-{booking_id:05d}", normal))
    story.append(Paragraph(f"<b>Issue Date:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}", normal))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>BOOKING DETAILS</b>", bold_style))
    story.append(Paragraph(f"Venue: {data['venue']}", normal))
    story.append(Paragraph(f"Date & Time: {data['start_dt'].strftime('%d %B %Y')}  |  {data['start_dt'].strftime('%H:%M')} – {data['end_dt'].strftime('%H:%M')}", normal))
    story.append(Paragraph(f"Department: {data['department']}", normal))
    story.append(Paragraph(f"Applicant: {data['applicant_name']} ({data['applicant_email']})", normal))
    if data.get("purpose"):
        story.append(Paragraph(f"Purpose: {data['purpose']}", normal))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>DOCUMENTS VERIFIED</b>", bold_style))
    story.append(Paragraph(f"• Approval from Departmental Head: {data.get('docs_hod', 'Submitted')}", normal))
    story.append(Paragraph(f"• Approval from Registrar Office: {data.get('docs_registrar', 'Submitted')}", normal))
    story.append(Paragraph(f"• Approval from Development Office: {data.get('docs_development', 'Submitted')}", normal))
    if data.get("docs_finance"):
        story.append(Paragraph(f"• Approval from Finance Department: {data.get('docs_finance')} (Optional)", normal))
    else:
        story.append(Paragraph("• Approval from Finance Department: Not submitted (Optional)", normal))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>LOGISTICS REQUIREMENTS</b>", bold_style))
    story.append(Paragraph(f"Electronic Presentation Equipment: {'Yes' if data.get('equip_required') else 'No'}", normal))
    if data.get("equip_required"):
        equip_list = DEMO_EQUIPMENT.get(data['venue'], [])
        story.append(Paragraph(f"Available equipment at venue (DEMO list): {', '.join(equip_list)}", normal))
    story.append(Paragraph(f"Number of Microphones requested: {data.get('mic_count', 0)}", normal))
    story.append(Paragraph(f"Other Logistic Supports: {data.get('other_logistics') or 'None specified'}", normal))
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>APPROVAL STATUS</b>", bold_style))
    story.append(Paragraph("This booking has been recorded in the central facility calendar and is marked as <b>CONFIRMED</b> for demo purposes.", normal))
    story.append(Spacer(1, 20))

    story.append(Paragraph("_______________________________", normal))
    story.append(Paragraph("Development Office / Facility Coordinator", normal))
    story.append(Paragraph("(Digital stamp – Demo Version)", normal))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<i>This is a DEMO certificate generated by the Streamlit Facility Booking System. It has no official validity.</i>", 
                           ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# -------------------------------------------------
# Streamlit App
# -------------------------------------------------
def main():
    st.set_page_config(
        page_title="PU Facility Booking – Demo",
        page_icon="🏛️",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    init_db()

    st.title("Presidency University")
    st.subheader("Centralized Facility Booking System (Demo)")
    st.caption("A. K. Basak • P. C. Mahalanobis • Derozio Hall • Manik Bandyopadhyay • Bankim Sabha Griha • Satyen Bose Sabha Griha • Acharya P. C. Roy")

    # Session state initialization
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "booking_data" not in st.session_state:
        st.session_state.booking_data = {}

    # Sidebar navigation / progress
    with st.sidebar:
        st.header("Progress")
        steps = ["1. Date & Time", "2. Availability", "3. Department & Applicant", 
                 "4. Documents", "5. Logistics", "6. Certificate"]
        for i, s in enumerate(steps, 1):
            if i < st.session_state.step:
                st.success(s)
            elif i == st.session_state.step:
                st.info(s)
            else:
                st.write(s)
        st.divider()
        if st.button("Reset / Start Over"):
            st.session_state.step = 1
            st.session_state.booking_data = {}
            st.rerun()
        st.caption("Demo only • SQLite calendar backend")

    # ---------------- STEP 1: Date & Time ----------------
    if st.session_state.step == 1:
        st.header("Step 1 – Select Date and Time")
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", min_value=datetime.now().date())
        with col2:
            start_time = st.time_input("Start Time", value=datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("End Time", value=datetime.strptime("12:00", "%H:%M").time())

        if st.button("Check Availability →", type="primary"):
            start_dt = datetime.combine(date, start_time)
            end_dt = datetime.combine(date, end_time)
            if end_dt <= start_dt:
                st.error("End time must be after start time.")
            else:
                st.session_state.booking_data["start_dt"] = start_dt
                st.session_state.booking_data["end_dt"] = end_dt
                st.session_state.step = 2
                st.rerun()

    # ---------------- STEP 2: Availability ----------------
    elif st.session_state.step == 2:
        st.header("Step 2 – Venue Availability")
        start_dt = st.session_state.booking_data["start_dt"]
        end_dt = st.session_state.booking_data["end_dt"]
        st.write(f"**Selected slot:** {start_dt.strftime('%d %b %Y, %H:%M')} – {end_dt.strftime('%H:%M')}")

        available_venues = []
        for venue in VENUES:
            avail = is_available(venue, start_dt, end_dt)
            if avail:
                st.success(f"✅ {venue} — Available")
                available_venues.append(venue)
            else:
                st.error(f"❌ {venue} — Not Available")

        if not available_venues:
            st.warning("No venues available for this slot. Please go back and choose another time.")
            if st.button("← Back to Date/Time"):
                st.session_state.step = 1
                st.rerun()
        else:
            selected = st.selectbox("Select an available venue", available_venues)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back"):
                    st.session_state.step = 1
                    st.rerun()
            with col2:
                if st.button("Proceed →", type="primary"):
                    st.session_state.booking_data["venue"] = selected
                    st.session_state.step = 3
                    st.rerun()

    # ---------------- STEP 3: Department & Applicant ----------------
    elif st.session_state.step == 3:
        st.header("Step 3 – Department & Applicant Details")
        st.write(f"**Venue:** {st.session_state.booking_data['venue']}")

        dept = st.selectbox("Requesting Department", DEPARTMENTS)
        name = st.text_input("Applicant Name *")
        email = st.text_input("Applicant Email *")
        purpose = st.text_area("Purpose of Booking (optional)")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Proceed →", type="primary"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.booking_data["department"] = dept
                    st.session_state.booking_data["applicant_name"] = name
                    st.session_state.booking_data["applicant_email"] = email
                    st.session_state.booking_data["purpose"] = purpose
                    st.session_state.step = 4
                    st.rerun()

    # ---------------- STEP 4: Documents ----------------
    elif st.session_state.step == 4:
        st.header("Step 4 – Document Upload & Verification")
        st.write("**Required documents (PDF or JPEG only)**")
        st.info("Development Office approval is the final verification gate.")

        hod = st.file_uploader("1. Approval from Departmental Head *", type=["pdf", "jpg", "jpeg"])
        registrar = st.file_uploader("2. Approval from Registrar Office *", type=["pdf", "jpg", "jpeg"])
        development = st.file_uploader("3. Approval from Development Office *", type=["pdf", "jpg", "jpeg"])
        finance = st.file_uploader("4. Approval from Finance Department (Optional)", type=["pdf", "jpg", "jpeg"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("Verify & Proceed →", type="primary"):
                if not (hod and registrar and development):
                    st.error("All three required documents must be uploaded.")
                else:
                    st.session_state.booking_data["docs_hod"] = hod.name
                    st.session_state.booking_data["docs_registrar"] = registrar.name
                    st.session_state.booking_data["docs_development"] = development.name
                    st.session_state.booking_data["docs_finance"] = finance.name if finance else ""
                    st.session_state.step = 5
                    st.rerun()

    # ---------------- STEP 5: Logistics ----------------
    elif st.session_state.step == 5:
        st.header("Step 5 – Logistics / Requirements")
        venue = st.session_state.booking_data["venue"]

        equip_yes = st.radio("Electronic Presentation Equipment Required?", ["No", "Yes"])
        if equip_yes == "Yes":
            st.write("**Equipment available at this venue (DEMO PLACEHOLDER list):**")
            for item in DEMO_EQUIPMENT.get(venue, []):
                st.write(f"• {item}")

        mic_count = st.number_input("Number of Microphones required", min_value=0, max_value=20, value=0)
        other = st.text_area("Other Logistic Supports", placeholder="e.g., extra chairs, water bottles, technical staff, stage decoration...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.step = 4
                st.rerun()
        with col2:
            if st.button("Generate Certificate →", type="primary"):
                st.session_state.booking_data["equip_required"] = (equip_yes == "Yes")
                st.session_state.booking_data["mic_count"] = mic_count
                st.session_state.booking_data["other_logistics"] = other
                # Save to calendar DB
                booking_id = save_booking(st.session_state.booking_data)
                st.session_state.booking_data["booking_id"] = booking_id
                st.session_state.step = 6
                st.rerun()

    # ---------------- STEP 6: Certificate ----------------
    elif st.session_state.step == 6:
        st.header("Step 6 – Final Approval Certificate")
        data = st.session_state.booking_data
        booking_id = data["booking_id"]

        st.success(f"Booking Confirmed • ID: PU-FAC-{booking_id:05d}")
        st.write(f"**Venue:** {data['venue']}")
        st.write(f"**Slot:** {data['start_dt'].strftime('%d %b %Y, %H:%M')} – {data['end_dt'].strftime('%H:%M')}")
        st.write(f"**Department:** {data['department']}")
        st.write(f"**Applicant:** {data['applicant_name']}")

        pdf_bytes = generate_certificate(data, booking_id)
        st.download_button(
            label="Download Final Approval Certificate (PDF)",
            data=pdf_bytes,
            file_name=f"PU_Facility_Approval_{booking_id:05d}.pdf",
            mime="application/pdf",
            type="primary"
        )

        st.divider()
        st.subheader("Current Calendar (SQLite)")
        bookings = get_all_bookings()
        if bookings:
            for b in bookings:
                st.write(f"#{b[0]} | {b[1]} | {b[2][:16]} → {b[3][11:16]} | {b[4]} | {b[5]}")
        else:
            st.write("No bookings yet.")

        if st.button("New Booking"):
            st.session_state.step = 1
            st.session_state.booking_data = {}
            st.rerun()

if __name__ == "__main__":
    main()
