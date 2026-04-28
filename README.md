<div align="center">

# 🚖 MOTUWA
### *The Right to Safe Ride with Pride*

**A volunteer-driven public transport safety platform — recognized globally — that empowers commuters, protects lives, and builds safer communities through technology and teamwork.**


</div>

---

## 🌍 What is MOTUWA?

Every day, millions of people board taxis and public transport with no way to share their ride details, no real-time tracking, and no safety net if something goes wrong.

That moment when the door closes and nobody knows where you are — **MOTUWA was built to change that.**

MOTUWA is a community-powered safety platform born from a volunteer initiative in Cameroon. It lets passengers record taxi details, share live location with trusted contacts, trigger emergency alerts, and submit driver reviews — all from one place. It's earned global recognition not because it's complicated, but because it works for the people who need it most.

> *"Safe ride. Safe life. Safe community."*

---

## ✨ Features

### 🔴 For Passengers

- **Ride Registration** — Before you go anywhere, log the plate number, vehicle type, driver name, and route. Takes 30 seconds. Could matter enormously.
- **Live GPS Tracking** — Your location is shared in real time with the contacts you trust, through a unique link they can open anytime.
- **Emergency Alerts** — If something feels wrong, your nominated contacts receive automated email alerts at regular intervals — until you mark yourself safe.
- **Journey Progress** — A live view of your ETA, distance remaining, and how far along the trip you are.
- **One-tap Share** — Send your tracking link straight to WhatsApp, or copy it to share however you like.
- **Arrive Safely Notification** — The moment you mark your journey complete, your contacts are automatically notified. No follow-up needed.

### 📋 For the Community

- **Quick Reports** — Submit detailed reviews of drivers and vehicles: behavior, driving quality, star rating. Your experience helps the next person make a safer choice.
- **Public Safety Blog** — Approved community reviews are published for anyone to read before they board.
- **Driver & Vehicle Database** — A searchable record of reported transport details, built over time by the community.

### 🛡️ For Administrators

- **Admin Dashboard** — Manage accounts, verify identities, and moderate the community review queue.
- **User Verification** — Review national ID documents and grant verified status to trusted members.
- **Review Moderation** — Approve or reject transport reviews before they go public.

---

## 🛠️ Tech Stack

### Web Platform

| Layer | Technology |
|---|---|
| Backend | Python · Flask 3.1 |
| Database | SQLite (`safety_reports.db`) |
| Frontend | HTML · CSS · SCSS · Less · JavaScript |
| Email Alerts | Python `smtplib` (Gmail SMTP) |
| Background Jobs | APScheduler |
| Geolocation | Geopy |
| Auth | Werkzeug password hashing · Flask sessions |
| Deployment | Gunicorn |



---



## 📁 Project Structure

```
MOTUWA/
├── app.py                    # Main Flask application & all routes
├── requirements.txt          # Python dependencies
├── safety_reports.db         # SQLite database (auto-created on first run)
│
├── static/                   # Static assets
│   └── uploads/              # Uploaded user files (national IDs, attachments)
│
├── templates/                # Jinja2 HTML templates
│   ├── MOTUWALanding.html    # Landing / home page
│   ├── FeaturesFlow.html     # Ride registration & monitoring
│   ├── QuickReport.html      # Submit a transport review
│   ├── Weblog.html           # Public safety blog (approved reviews)
│   ├── UserLogin.html        # Login page
│   ├── UserRegistration.html # Sign-up page
│   ├── ContactSupport.html   # Contact form
│   └── MotuwaAdmin.html      # Admin dashboard
│
└── uploads/                  # Legacy upload directory
```

---

## 🗺️ Application Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/features` | GET, POST | Ride registration & emergency monitoring |
| `/submit-report` | GET, POST | Submit a transport/driver review |
| `/blog` | GET | Public safety blog (approved reviews only) |
| `/login` | GET, POST | User & admin login |
| `/signup` | GET, POST | New user registration |
| `/logout` | GET | End session |
| `/contact` | GET, POST | Contact & support form |
| `/admin` | GET | Admin dashboard (admin only) |
| `/verify/<id>` | POST | Verify a user account |
| `/revoke/<id>` | POST | Revoke user verification |
| `/admin/reviews/<id>/approve` | POST | Approve a community review |
| `/admin/reviews/<id>/reject` | POST | Reject a community review |

---

## 🔐 Before You Go Live

MOTUWA works out of the box for local development, but please make these changes before shipping to production — they matter for user safety.

**1. Move credentials out of source code.**
The admin username, password, email credentials, and secret key are currently hard-coded in `app.py`. Use environment variables instead:

```bash
export MOTUWA_SECRET_KEY="your-secret-key"
export ADMIN_EMAIL="your-admin-email"
export ADMIN_PASSWORD="your-admin-password"
export SMTP_PASSWORD="your-app-password"
```

**2. Use HTTPS.**
You're handling real-time location data and emergency contacts. Never serve that over plain HTTP in production.

**3. Rate-limit the alert monitor.**
The background email thread in `monitor_ride()` runs indefinitely until the process is killed. Add a max-alert-count or a ride-end trigger to keep it under control.

**4. Restrict the admin route.**
Add a proper `@login_required` decorator that checks `session["role"] == "admin"` — the current setup relies on trust alone.

---

## 📦 Dependencies

```
Flask==3.1.2
Werkzeug==3.1.3
apscheduler==3.10.4
geopy==2.4.1
gunicorn
requests==2.32.5
Jinja2==3.1.6
```

Full list in [`requirements.txt`](requirements.txt).

---


## 📬 Get in Touch

Have a question, spotted a bug, or want to partner with us?

- Open an [issue](https://github.com/DevNdehPaul/MOTUWA/issues) on GitHub
- Use the in-app [Contact & Support](https://github.com/DevNdehPaul/MOTUWA) form

---


Made with ❤️ by volunteers, for communities.

**MOTUWA — The Right to Safe Ride with Pride.**

</div>
