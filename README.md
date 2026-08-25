# Presidency University Facility Booking System – Demo

Streamlit + SQLite demo application for centralized booking of halls and conference rooms.

## Venues (as specified)
- A. K. Basak Auditorium
- P. C. Mahalanobis Auditorium
- Derozio Hall
- Manik Bandyopadhyay Auditorium
- Bankim Sabha Griha
- Satyen Bose Sabha Griha
- Acharya Prafulla Chandra Roy Auditorium

## How to run
```bash
cd /path/to/this/folder
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` contains:
- streamlit
- reportlab   (recommended for PDF certificates)

If reportlab is not installed the app still runs and offers a plain-text certificate (no crash).

## Features implemented
1. Date + time selection
2. Real-time availability check against SQLite calendar (overlap detection)
3. Department selection (official list from presiuniv.ac.in)
4. Required document uploads (HOD, Registrar, Development Office) + optional Finance
5. Logistics requirements (equipment Y/N, mic count, other supports)
6. Final Approval Certificate (PDF when reportlab is present, otherwise TXT)
7. Bookings persisted in local `bookings.db` (acts as the calendar backend)

## Important notes (Zero hallucination)
- Equipment lists are **DEMO PLACEHOLDERS only**. No official inventory data was used.
- “Manik Bandyopadhyay Auditorium” is included solely because it was explicitly requested; no public confirmation of this venue name on presiuniv.ac.in was found.
- Capacities shown in resources.txt are historical references or marked DEMO.
- This is a non-authenticated demo. No real institutional integration.

## Files
- `app.py` – main Streamlit application
- `resources.txt` – static reference data
- `bookings.db` – created automatically on first run (SQLite calendar)
