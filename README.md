<div align="center">

# 🚖 MOTUWA
### *The Right to Safe Ride with Pride*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Flutter](https://img.shields.io/badge/Flutter-Mobile-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**A volunteer-driven public transport safety platform — recognized globally — that empowers commuters, protects lives, and builds safer communities through technology and teamwork.**

[Features](#-features) · [Tech Stack](#-tech-stack) · [Getting Started](#-getting-started) · [Project Structure](#-project-structure) · [Contributing](#-contributing)

</div>

---

## 🌍 About MOTUWA

Every day, millions of people board taxis and public transport with no way to share their ride details, no real-time tracking, and no safety net if something goes wrong.

**MOTUWA** changes that.

MOTUWA is a community-powered safety platform that lets passengers record taxi details, share live location with trusted contacts, receive emergency alerts, and submit driver/vehicle reviews — all in one place. Born from a volunteer initiative in Cameroon, MOTUWA has earned global recognition for its impact on reducing transport insecurity and saving lives.

> *"Safe ride. Safe life. Safe community."*

---

## ✨ Features

### 🔴 For Passengers
- **Ride Registration** — Log your taxi's plate number, vehicle type, driver name, and route before you depart
- **Live GPS Tracking** — Real-time location tracking shared securely with emergency contacts via a unique live link
- **Emergency Alerts** — Automated email alerts sent to your nominated contacts at regular intervals until your ride is marked safe
- **Journey Progress** — Visual ETA countdown, distance remaining, and journey completion percentage
- **One-tap Share** — Share your live tracking link via WhatsApp or copy to clipboard instantly
- **Arrive Safely Notification** — Contacts are automatically notified the moment you mark your journey complete

### 📋 For the Community
- **Quick Reports** — Submit detailed reviews of drivers and vehicles including behavior, driving quality, and star rating
- **Public Safety Blog** — Approved community reviews are published for others to reference before boarding
- **Driver & Vehicle Database** — Searchable records of reported transport details

### 🛡️ For Administrators
- **Admin Dashboard** — Manage user accounts, verify identities, approve or reject community reviews
- **User Verification** — Review uploaded national ID documents and grant verified status
- **Review Moderation** — Approve or reject transport reviews before they go public

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

### Mobile App (Flutter)
| Layer | Technology |
|---|---|
| Framework | Flutter / Dart |
| Maps & Routing | Google Maps Flutter · Directions API · Geocoding API |
| Real-time Database | Firebase Firestore |
| GPS | Geolocator |
| Notifications | Custom NotificationService |
| HTTP | Dart `http` package |
| Deep Links | url_launcher |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- pip
- Git
- (For mobile) Flutter SDK, Firebase project, Google Maps API key

### 1. Clone the Repository

```bash
git clone https://github.com/DevNdehPaul/MOTUWA.git
cd MOTUWA
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The app will start in debug mode at `http://127.0.0.1:5000`.

### 5. Production Deployment (with Gunicorn)

```bash
gunicorn app:app
```

---

## 📁 Project Structure

```
MOTUWA/
├── app.py                  # Main Flask application & all routes
├── requirements.txt        # Python dependencies
├── safety_reports.db       # SQLite database (auto-created on first run)
│
├── static/                 # Static assets
│   └── uploads/            # Uploaded user files (national IDs, attachments)
│
├── templates/              # Jinja2 HTML templates
│   ├── MOTUWALanding.html  # Landing / home page
│   ├── FeaturesFlow.html   # Ride registration & monitoring
│   ├── QuickReport.html    # Submit a transport review
│   ├── Weblog.html         # Public safety blog (approved reviews)
│   ├── UserLogin.html      # Login page
│   ├── UserRegistration.html # Sign-up page
│   ├── ContactSupport.html # Contact form
│   └── MotuwaAdmin.html    # Admin dashboard
│
└── uploads/                # Legacy upload directory
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

## 🔐 Security Notes

> ⚠️ **Before deploying to production**, please make the following changes:

1. **Move credentials out of source code.** The admin username, password, email credentials, and secret key are currently hard-coded in `app.py`. Use environment variables instead:
   ```bash
   export MOTUWA_SECRET_KEY="your-secret-key"
   export ADMIN_EMAIL="your-admin-email"
   export ADMIN_PASSWORD="your-admin-password"
   export SMTP_PASSWORD="your-app-password"
   ```

2. **Use HTTPS** in production. Never serve user data over plain HTTP.

3. **Rate-limit the alert monitor.** The background email thread in `monitor_ride()` runs indefinitely until the process is killed. Consider adding a max-alert-count or a ride-end trigger.

4. **Restrict the admin route** with a proper `@login_required` decorator checking `session["role"] == "admin"`.

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

## 🤝 Contributing

MOTUWA is a volunteer-driven project and welcomes contributions from anyone who believes in safer communities.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your feature description"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please make sure your code is clean, commented, and tested before submitting.

---

## 🌐 Recognition

MOTUWA has been recognized globally as an innovative community initiative addressing public transport safety, reducing insecurity, and demonstrating how volunteer technology projects can save lives.

---

## 📬 Contact & Support

Have a question, want to report a bug, or interested in partnering?

- Open an [issue](https://github.com/DevNdehPaul/MOTUWA/issues) on GitHub
- Use the in-app [Contact & Support](https://github.com/DevNdehPaul/MOTUWA) form

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute it — just keep the spirit of community safety alive.

---

<div align="center">

Made with ❤️ by volunteers, for communities.

**MOTUWA — The Right to Safe Ride with Pride.**

</div>
