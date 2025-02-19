# VTOP API 🚀

A FastAPI-based service to programmatically retrieve academic data from VIT University's VTOP portal using web scraping techniques.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)  
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=for-the-badge&logo=playwright&logoColor=white)

---

## Features ✨

- Student authentication with VTOP credentials
- Captcha solving automation
- Retrieval of comprehensive academic data:
  - Attendance records
  - Course details
  - Marks/grades
  - CGPA breakdown
  - Exam schedules
  - Semester information
- Docker container support
- CORS enabled for web client access

---

## Prerequisites 📋

- Docker Engine
- 2GB+ RAM (for Playwright browser automation)
- Stable internet connection

---

## Installation & Usage 🛠️

1. **Clone repository**

```bash
git clone https://github.com/yourusername/vtop-api.git
cd vtop-api
```

2. **Build Docker image**

```bash
docker build -t vtop-api .
```

3. **Run container**

```bash
docker run -d -p 8000:8000 --name vtop-container vtop-api
```

4. **Run setup script** (for Playwright browsers)

```bash
chmod +x setup.sh && ./setup.sh
```

---

## API Endpoint 🌐

**Base URL:**

```http
https://vtop-api-w1ux.onrender.com/vtopdata?username={username}&password={password}
```

**Alternate URL:**

```http
https://vtopapi-production.up.railway.app/vtopdata?username={username}&password={password}
```

**Parameters:**

- `username`: VTOP registration number
- `password`: VTOP password
- `semIndex` (optional): Semester index (0-based, defaults to current semester)

**Example Request:**

```http
GET /vtopdata?username=20ABCD1234&password=secret123&semIndex=1
```

---

## Response Structure 📦

```json
{
  "status": "success",
  "data": {
    "semester": [...],
    "Attendance": [...],
    "Course": [...],
    "Marks": [...],
    "CGPA": {...},
    "ExamSchedule": [...]
  }
}
```

---

## Security & Disclaimer 🔒

⚠️ **Important Notice:**

- This project is **not officially affiliated** with VIT University.
- Use at your own risk - credentials are transmitted securely but depend on VTOP's security.
- API may break with VTOP portal updates.
- Never share your credentials with untrusted parties.
- Maintained for educational purposes only.

---

## Development 🤝

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open Pull Request

---

## Acknowledgments 🙏

- Playwright team for browser automation tools
- FastAPI for modern Python web framework
- Open source community for continuous inspiration
