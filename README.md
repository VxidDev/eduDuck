# 🦆 EduDuck 🦆

<div align="center">
  <img src="duck.jpg" alt="EduDuck" width="980" height="350"/>
  <br><br>
  <a href="https://eduduck.onrender.com/">
    <img src="https://img.shields.io/badge/Live%20Demo-EduDuck-brightgreen?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo">
  </a>
  <a href="https://github.com/VxidDev/eduDuck/stargazers">
    <img src="https://img.shields.io/github/stars/VxidDev/eduDuck?style=for-the-badge&logo=github&logoColor=white" alt="Stars">
  </a>
  <a href="https://ko-fi.com/vxiddev">
    <img src="https://img.shields.io/badge/Support%20Me-Ko--fi-ff5f5f?style=for-the-badge&logo=kofi&logoColor=white" alt="Support">
  </a>
  <a href="https://eduduck.onrender.com/login/google">
    <img src="https://img.shields.io/badge/Login%20with-Google-red?style=for-the-badge&logo=google&logoColor=white" alt="Login with Google">
  </a>
  <a href="https://github.com/VxidDev/eduDuck/graphs/contributors">
    <img src="https://img.shields.io/badge/Contributors-👥-blue?style=for-the-badge" alt="Contributors">
  </a>
  <br>
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3.0-orange?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Gunicorn-20.1.0-red?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Gunicorn">
</div>

### EduDuck - Turn messy notes into clear explanations, quizzes, and flashcards with AI, so you can study less and remember more. 

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [👤 Accounts](#-accounts)
  - [🆓 Free Account Benefits](#-free-account-benefits)
  - [🔮 Planned Account Features](#-planned-account-features)
  - [📌 Why Accounts?](#-why-accounts)
- [🔑 Google OAuth Login](#-google-oauth-login)
- [🚀 Quick Start](#-quick-start)
- [🎓 Who Is EduDuck For?](#-who-is-eduduck-for)
- [🛠️ Tech Stack](#-tech-stack)
- [🛠️ Local Development](#-local-development)
- [🎯 Roadmap](#-roadmap)
- [🤝 Contributions](#-contributions)
- [💰 Support the Project](#-support-the-project)
- [❗ Known Issues](#-known-issues)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| **📝 Quiz Generator** | Upload notes → instant quizzes |
| **🗂️ Flashcard Generator** | Spaced repetition flashcards from any subject |
| **✨ Note Enhancer** | AI-powered summaries, diagrams, key concepts |
| **📆 Study Plan Generator** | AI-generated daily study plans tailored to your notes, goals, time, and learning style |
| **🦆 DuckAI** | Chat with your notes, get explanations & study tips |
| **📱 Multi-format** | TXT, PDF, PNG/JPG, handwritten notes via OCR |
| **🌍 Multi-language** | English, Polish, German, French, Ukrainian, Russian |
| **🎨 Modern UI** | Dark/light mode, mobile-first, glassmorphism design |
| **🔑 Google OAuth Login** | Sign in instantly with Google, no password required |

---

## 👤 Accounts

EduDuck supports **user accounts** to provide fair access limits and enable future personalization features.

### 🆓 Free Account Benefits

Creating a free account unlocks:

- 🎯 **3 free uses per day** across:
  - Quiz Generator
  - Flashcard Generator
  - Note Enhancer
  - Study Plan Generator
  - 🦆 DuckAI chat
- 🌍 Access across all supported languages
- 🗂️ Viewing past queries and chats.
- 🔒 Usage tracking to prevent abuse and keep the service available

Free usage resets **daily**. No payment required.

---

### 🔮 Planned Account Features

Accounts are the foundation for upcoming features, including:

- 📚 Quiz & study history
- 📊 Learning progress tracking
- ☁️ Cloud-saved notes and generated materials
- ⭐ Premium tiers with higher or unlimited usage

---

### 📌 Why Accounts?

EduDuck relies on paid AI APIs.  
Accounts help:

- keep a **free tier available for students**
- prevent abuse
- sustainably scale the platform 🚀

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=VxidDev/eduduck&type=date&legend=top-left)](https://www.star-history.com/#VxidDev/eduduck&type=date&legend=top-left)

## 🚀 Quick Start

### 1. Get a Free API Key  
*(Hugging Face, Google Gemini, or OpenAI)*

| Provider | Link | Free Tier |
|--------|------|-----------|
| 🤗 **Hugging Face** | https://huggingface.co/settings/tokens | 1M tokens/month |
| ⭐ **Google Gemini** | https://aistudio.google.com/app/apikey | 15 RPM |
| 🔥 **OpenAI** | https://platform.openai.com/api-keys | ~$0.001/quiz |

### 2. Try the Live Demo  
👉 **https://eduduck.app**

### 3. Paste your notes → Generate → Learn!

---

## 🎓 Who Is EduDuck For?

- Students who want to learn faster from their own notes  
- Teachers creating quizzes and study materials  
- Self-learners preparing for exams  
- Anyone tired of re-reading notes instead of testing knowledge

---

## 🛠️ Tech Stack

### Frontend
- Languages: HTML5, CSS3 (CSS variables), JavaScript, TypeScript
- Libraries: markdown-it

### Backend (Flask / Python)
- Framework: Flask
- Auth: Flask-Login, Authlib (Google/GitHub/Discord/Microsoft OAuth), Werkzeug (security + password hashing), secrets, JWT
- Data: MongoDB (PyMongo), BSON, certifi
- AI + HTTP: httpx (HTTP/2, connection pooling), OpenAI/Gemini/Hugging Face integrations, requests (Mailgun)
- Storage: Cloudflare R2 via boto3/botocore
- File processing: pypdf, Pillow (PIL), python-magic (file type detection), defusedxml (SVG/XML safety), io.BytesIO, base64
- Utilities: python-dotenv, uuid, re, functools, msgspec (fast JSON), json, os, atexit, datetime, collections, math, random
- Security & rate limiting: Flask-WTF (CSRF), Flask-Limiter, Werkzeug, defusedxml, python-magic
- Logging: rich
- i18n: Flask-Babel

### AI APIs
- Hugging Face Inference API
- Google Gemini (2.5 Flash)
- OpenAI (GPT models)

### Email
- Mailgun

### Rust extensions (PyO3)
- quiz_parser
- study_plan_parser
- submit_quiz

## 🛠️ Local Development

1. **Installation**
```bash
git clone https://github.com/VxidDev/eduDuck.git
cd eduDuck
python -m venv venv
source venv/bin/activate
bash build.sh
```

2. Add .env with the following variables:

```
FREE_TIER_API_KEY= ... (OpenAI key)
MONGODB_URI= ... (MongoDB API link)
SECRET_KEY= ... (32 char long)
GOOGLE_CLIENT_ID= ...
GOOGLE_CLIENT_SECRET= ...
MAILGUN_API_KEY= ...
VERIFICATION_EMAIL= ...
R2_ACCESS_KEY_ID= ...
R2_SECRET_ACCESS_KEY= ...
R2_ACCOUNT_ID= ...
R2_BUCKET_NAME= ...
```

3. Run locally using Gunicorn

```bash
# Production-style run with 4 workers on port 5000
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```
---

## 🎯 Roadmap

| Status | Feature |
|------|---------|
| ✅ Done | Basic quiz generation |
| ✅ Done | PDF/TXT/image upload + OCR |
| ✅ Done | Quiz & Flashcard visualization |
| ✅ Done | Note Enhancer |
| ✅ Done | DuckAI chat |
| ✅ Done | Multi-language support |
| ✅ Done | Dark mode + mobile UI |
| ✅ Done | Quiz difficulty levels |
| ✅ Done | Export generated material (.json) |
| ✅ Done | OpenAI API support |
| ✅ Done | Free daily usage (3/day) |
| ✅ Done | UI/UX improvements |
| ✅ Done | Study Plan Generator |
| ✅ Done | Google OAuth |
| ✅ Done | Email Verification |
| ✅ Done | User accounts & quiz history |
| ✅ Done | Improve OCR |
| ✅ Done | Add User PFP support |
| ✅ Done | Migrate quiz parser to C , C++ or Rust. |
| ✅ Done | Improve AiReq |
| ✅ Done | Add attaching files to DuckAI. |
| ✅ Done | Fix file uploading if edited notes.textContent |
| ✅ Done | Added password reset option |
| ✅ Done | Added account deletion option |
| ✅ Done | Improved UX/UI |
| ✅ Done | Migrated part of JS code to TS |
| ✅ Done | Fix footer not at the bottom bug. |
| ✅ Done | Migrated most of JS code to TS. |
| ✅ Done | Study progress tracking |
| ✅ Done | Add note analyzer |
| ✅ Done | Simplify UI |
| ✅ Done | Add multi-language pages. |
| 🔄 In Progress | Bug fixes and polishing. |
| ⏳ Planned | ??? |

---

## 🤝 Contributions

- **Art**: [netkv](https://github.com/netkv) ❤️  
- **Code & Testing**: [VxidDev](https://github.com/VxidDev)
- **Help with Russian translation and minor clean-up**: [abdussamad567](https://github.com/abdussamad567)

**Sponsors**
---
**Deathtyr – $30**  
> “Invest in this guy, makes life easier (I really said that!)”

---

## 💰 Support the Project

<div align="center">
  <a href="https://ko-fi.com/vxiddev">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Ko-fi" width="200"/>
  </a>
  <p>Your support helps upgrade hosting and add premium features! 🦆</p>
</div>

---

## ❗ Known Issues

None :D

## 📄 License

Apache License 2.0 - see LICENSE for details.

Made with ❤️ by **VoidDev** - self-taught since June 2025

<div align="center">
  <img src="https://img.shields.io/badge/version-2.0-blue?style=for-the-badge&logo=eduDuck&logoColor=white" alt="Version">
</div>
