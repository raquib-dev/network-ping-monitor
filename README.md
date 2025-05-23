# 📡 Network Reachability Monitor

A FastAPI-based internal monitoring tool to ping and track multiple client devices (e.g., tablets on machines in a factory) — enabling real-time reachability checks and historical log viewing for root cause analysis.

---

## ❓ Why This Project

In a real-world manufacturing deployment, we encountered connectivity issues on several customer-end tablets that track machine OEE. Diagnosing the problem manually was slow and error-prone.

This tool was built to solve that:
- ✅ Pings all configured client devices asynchronously
- ✅ Logs each result with timestamps
- ✅ Shows real-time and historical status per IP
- ✅ Simplifies IP address management via UI

---

## ⚙️ Features

- ✏️ Editable IP list from web UI
- 📊 Real-time ping dashboard with status + stats
- 📁 Date- and IP-wise log storage
- 🔍 Filter logs by IP, reachability status, and date
- 🧠 Smart thread-based ping scheduler with cleanup
- 🧱 Log retention logic (auto cleanup after 5 days)

---

## 🚀 Tech Stack

- **Backend:** FastAPI
- **Frontend:** Jinja2 Templates, HTML/CSS
- **Scheduler:** Python `threading`
- **Platform Support:** Cross-platform (Linux/Windows)
- **Persistence:** Filesystem-based logs (no DB required)

---

## 🧪 How to Run

> Requirements: Python 3.10+

```bash
pip install -r requirements.txt
```

1. Add IPs in `ip_addresses.txt` (one per line)
2. Start the server:

```bash
python main.py
```

3. Visit [http://localhost:5005](http://localhost:5005) to:
   - Edit IPs
   - Monitor live status
   - View logs (by IP/date/status)

---

## 📁 Project Structure

```
.
├── main.py                # FastAPI app & threading logic
├── ip_addresses.txt       # Source for client IPs
├── templates/             # Jinja2 HTML pages
├── Log/                   # Date/IP-wise logs
└── requirements.txt
```

---

## 🛠 Use Cases

- Monitoring industrial tablet connectivity
- Diagnosing random WiFi outages
- Tracking machine IP/device uptime
- Factory-floor diagnostics tool for IT teams

---

## 💡 Future Ideas

- Ping graph trends per IP
- Export logs to CSV
- Email/Telegram alerts for offline devices