"""
Presidency University Facility Booking System - Demo (Streamlit)
Includes Development Office / Principal Calendar module.
Zero hallucination: venue names, departments and document rules as previously fixed.
Equipment lists remain DEMO PLACEHOLDERS only.
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import os
import io

# Optional reportlab import (PDF generation). Falls back gracefully if not installed.
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# -------------------------------------------------
# Constants
# -------------------------------------------------
DB_PATH = "bookings.db"

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

# DEMO PLACEHOLDER equipment only
DEMO_EQUIPMENT = {
    "A. K. Basak Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "P. C. Mahalanobis Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "Derozio Hall": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set", "Stage Lighting (basic)"],
    "Manik Bandyopadhyay Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
    "Bankim Sabha Griha": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Whiteboard", "Sound System", "Cordless Microphone Set"],
    "Satyen Bose Sabha Griha": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Whiteboard", "Sound System", "Cordless Microphone Set"],
    "Acharya Prafulla Chandra Roy Auditorium": ["Projector", "Screen", "HDMI / Laptop Connectivity", "Laser Pointer", "Sound System", "Cordless Microphone Set"],
}

# Simple demo password for Development Office
DEV_OFFICE_PASSWORD = "devoffice2026"

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
            created_at TEXT,
            created_by TEXT
        )
    """)
    conn.commit()
    conn.close()

def is_available(venue: str, start_dt: datetime, end_dt: datetime) -> bool:
    """True if no overlapping Confirmed or Blocked booking exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE venue = ?
          AND status IN ('Confirmed', 'Blocked')
          AND start_dt < ?
          AND end_dt > ?
    """, (venue, end_dt.isoformat(), start_dt.isoformat()))
    count = c.fetchone()[0]
    conn.close()
    return count == 0

def save_booking(data: dict, status: str = "Confirmed", created_by: str = "User") -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings (
            venue, start_dt, end_dt, department, applicant_name, applicant_email,
            purpose, status, docs_hod, docs_registrar, docs_development, docs_finance,
            equip_required, mic_count, other_logistics, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["venue"],
        data["start_dt"].isoformat(),
        data["end_dt"].isoformat(),
        data.get("department", ""),
        data.get("applicant_name", ""),
        data.get("applicant_email", ""),
        data.get("purpose", ""),
        status,
        data.get("docs_hod", ""),
        data.get("docs_registrar", ""),
        data.get("docs_development", ""),
        data.get("docs_finance", ""),
        1 if data.get("equip_required") else 0,
        data.get("mic_count", 0),
        data.get("other_logistics", ""),
        datetime.now().isoformat(),
        created_by
    ))
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def get_active_bookings(venue_filter: str = None, date_from: str = None, date_to: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = """
        SELECT id, venue, start_dt, end_dt, department, applicant_name,
               purpose, status, created_by, created_at
        FROM bookings
        WHERE status IN ('Confirmed', 'Blocked')
    """
    params = []
    if venue_filter and venue_filter != "All":
        query += " AND venue = ?"
        params.append(venue_filter)
    if date_from:
        query += " AND start_dt >= ?"
        params.append(date_from)
    if date_to:
        query += " AND end_dt <= ?"
        params.append(date_to + "T23:59:59")
    query += " ORDER BY start_dt"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def cancel_booking(booking_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

def get_all_bookings_for_display():
    """Simple list used on the final certificate page."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, venue, start_dt, end_dt, department, status
        FROM bookings
        WHERE status IN ('Confirmed', 'Blocked')
        ORDER BY start_dt
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------------------------------
# Certificate Generator
# -------------------------------------------------
def generate_certificate(data: dict, booking_id: int) -> bytes:
    if not REPORTLAB_AVAILABLE:
        lines = [
            "PRESIDENCY UNIVERSITY",
            "86/1 College Street, Kolkata – 700073",
            "",
            "FACILITY BOOKING – FINAL APPROVAL CERTIFICATE",
            "",
            f"Booking ID: PU-FAC-{booking_id:05d}",
            f"Issue Date: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            "",
            "BOOKING DETAILS",
            f"Venue: {data['venue']}",
            f"Date & Time: {data['start_dt'].strftime('%d %B %Y')} | {data['start_dt'].strftime('%H:%M')} – {data['end_dt'].strftime('%H:%M')}",
            f"Department: {data['department']}",
            f"Applicant: {data['applicant_name']} ({data['applicant_email']})",
            f"Purpose: {data.get('purpose') or 'Not specified'}",
            "",
            "DOCUMENTS VERIFIED",
            f"- Approval from Departmental Head: {data.get('docs_hod', 'Submitted')}",
            f"- Approval from Registrar Office: {data.get('docs_registrar', 'Submitted')}",
            f"- Approval from Development Office: {data.get('docs_development', 'Submitted')}",
            f"- Approval from Finance Department: {data.get('docs_finance') or 'Not submitted (Optional)'}",
            "",
            "LOGISTICS REQUIREMENTS",
            f"Electronic Presentation Equipment: {'Yes' if data.get('equip_required') else 'No'}",
        ]
        if data.get("equip_required"):
            equip_list = DEMO_EQUIPMENT.get(data['venue'], [])
            lines.append(f"Available equipment at venue (DEMO list): {', '.join(equip_list)}")
        lines.extend([
            f"Number of Microphones requested: {data.get('mic_count', 0)}",
            f"Other Logistic Supports: {data.get('other_logistics') or 'None specified'}",
            "",
            "APPROVAL STATUS",
            "This booking has been recorded in the central facility calendar and is marked as CONFIRMED for demo purposes.",
            "",
            "_______________________________",
            "Development Office / Facility Coordinator",
            "(Digital stamp – Demo Version)",
            "",
            "This is a DEMO certificate. It has no official validity.",
            "Note: Install reportlab for PDF version."
        ])
        return "\n".join(lines).encode("utf-8")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'],
                                 fontSize=16, alignment=TA_CENTER, spaceAfter=6,
                                 textColor=colors.HexColor("#1a365d"))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'],
                                    fontSize=11, alignment=TA_CENTER, spaceAfter=12)
    normal = ParagraphStyle('NormalStyle', parent=styles['Normal'],
                            fontSize=10, leading=14, spaceAfter=4)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'],
                                fontSize=10, leading=14, spaceAfter=4, fontName='Helvetica-Bold')

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
    story.append(Paragraph("<i>This is a DEMO certificate. It has no official validity.</i>",
                           ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                                          textColor=colors.grey, alignment=TA_CENTER)))

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

    # Session state
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "booking_data" not in st.session_state:
        st.session_state.booking_data = {}
    if "dev_logged_in" not in st.session_state:
        st.session_state.dev_logged_in = False
    if "mode" not in st.session_state:
        st.session_state.mode = "user"   # "user" or "dev"

    # Sidebar
    with st.sidebar:
        st.header("Mode")
        mode = st.radio("Select mode", ["User Booking", "Development Office"],
                        index=0 if st.session_state.mode == "user" else 1)
        if mode == "User Booking":
            st.session_state.mode = "user"
            st.session_state.dev_logged_in = False
        else:
            st.session_state.mode = "dev"

        st.divider()

        if st.session_state.mode == "user":
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
            if st.button("Reset / Start Over"):
                st.session_state.step = 1
                st.session_state.booking_data = {}
                st.rerun()

        st.caption("Demo only • SQLite calendar backend")

    # =====================================================
    # DEVELOPMENT OFFICE MODULE
    # =====================================================
    if st.session_state.mode == "dev":
        st.title("Development Office")
        st.subheader("Principal Calendar & Slot Control")

        if not st.session_state.dev_logged_in:
            st.info("This module is for Development Office / Principal use only.")
            pwd = st.text_input("Enter password", type="password")
            if st.button("Login"):
                if pwd == DEV_OFFICE_PASSWORD:
                    st.session_state.dev_logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            st.caption("Demo password: `devoffice2026`")
            return

        # ----- Logged-in Admin View -----
        st.success("Logged in as Development Office")
        if st.button("Logout"):
            st.session_state.dev_logged_in = False
            st.rerun()

        tab1, tab2 = st.tabs(["View Calendar", "Block a Slot"])

        # ----- Tab 1: View & Cancel -----
        with tab1:
            st.markdown("### Active Bookings & Blocked Slots")
            colf1, colf2, colf3 = st.columns(3)
            with colf1:
                venue_f = st.selectbox("Filter by venue", ["All"] + VENUES)
            with colf2:
                date_from = st.date_input("From date", value=None)
            with colf3:
                date_to = st.date_input("To date", value=None)

            date_from_str = date_from.isoformat() if date_from else None
            date_to_str = date_to.isoformat() if date_to else None

            rows = get_active_bookings(
                venue_filter=venue_f if venue_f != "All" else None,
                date_from=date_from_str,
                date_to=date_to_str
            )

            if not rows:
                st.write("No active bookings or blocked slots found for the selected filters.")
            else:
                for r in rows:
                    bid, venue, start, end, dept, applicant, purpose, status, created_by, created_at = r
                    start_fmt = start[:16].replace("T", " ")
                    end_fmt = end[11:16]
                    with st.expander(f"{'🔒 BLOCKED' if status == 'Blocked' else '✅ CONFIRMED'}  |  {venue}  |  {start_fmt} – {end_fmt}"):
                        st.write(f"**ID:** {bid}")
                        st.write(f"**Status:** {status}")
                        st.write(f"**Department / Reason:** {dept or purpose or '—'}")
                        st.write(f"**Applicant:** {applicant or '—'}")
                        st.write(f"**Created by:** {created_by} on {created_at[:16].replace('T', ' ')}")
                        if st.button(f"Cancel / Unblock this slot", key=f"cancel_{bid}"):
                            cancel_booking(bid)
                            st.success(f"Booking #{bid} cancelled.")
                            st.rerun()

        # ----- Tab 2: Block New Slot -----
        with tab2:
            st.markdown("### Block a Date / Time Slot")
            st.caption("Blocked slots cannot be booked by regular users.")

            b_venue = st.selectbox("Venue to block", VENUES, key="block_venue")
            colb1, colb2 = st.columns(2)
            with colb1:
                b_date = st.date_input("Date", key="block_date")
                b_start = st.time_input("Start time", value=datetime.strptime("09:00", "%H:%M").time(), key="block_start")
            with colb2:
                b_end = st.time_input("End time", value=datetime.strptime("17:00", "%H:%M").time(), key="block_end")
            b_reason = st.text_input("Reason for blocking (required)", placeholder="e.g. University Convocation / Maintenance / VIP Visit")

            if st.button("Block this slot", type="primary"):
                if not b_reason.strip():
                    st.error("Reason is required.")
                else:
                    start_dt = datetime.combine(b_date, b_start)
                    end_dt = datetime.combine(b_date, b_end)
                    if end_dt <= start_dt:
                        st.error("End time must be after start time.")
                    elif not is_available(b_venue, start_dt, end_dt):
                        st.error("This slot overlaps with an existing Confirmed or Blocked entry.")
                    else:
                        data = {
                            "venue": b_venue,
                            "start_dt": start_dt,
                            "end_dt": end_dt,
                            "purpose": b_reason,
                            "department": "Development Office Block",
                            "applicant_name": "Development Office",
                            "applicant_email": ""
                        }
                        new_id = save_booking(data, status="Blocked", created_by="Development Office")
                        st.success(f"Slot blocked successfully. ID: {new_id}")
                        st.rerun()

        return   # end of Development Office module

    # =====================================================
    # USER BOOKING FLOW (unchanged logic + updated availability)
    # =====================================================
    st.title("Presidency University")
    st.subheader("Centralized Facility Booking System (Demo)")
    st.caption("A. K. Basak • P. C. Mahalanobis • Derozio Hall • Manik Bandyopadhyay • Bankim Sabha Griha • Satyen Bose Sabha Griha • Acharya P. C. Roy")

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
        other = st.text_area("Other Logistic Supports", placeholder="e.g., extra chairs, water bottles, technical staff...")

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
                booking_id = save_booking(st.session_state.booking_data, status="Confirmed", created_by="User")
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

        cert_bytes = generate_certificate(data, booking_id)
        if REPORTLAB_AVAILABLE:
            st.download_button(
                label="Download Final Approval Certificate (PDF)",
                data=cert_bytes,
                file_name=f"PU_Facility_Approval_{booking_id:05d}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("reportlab is not installed → serving plain-text certificate.")
            st.download_button(
                label="Download Final Approval Certificate (TXT)",
                data=cert_bytes,
                file_name=f"PU_Facility_Approval_{booking_id:05d}.txt",
                mime="text/plain",
                type="primary"
            )

        st.divider()
        st.subheader("Current Calendar (SQLite)")
        bookings = get_all_bookings_for_display()
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
