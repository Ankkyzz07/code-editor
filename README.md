# Code Editor Backend (FastAPI)

A backend system built using **FastAPI** with a clean and modular structure.  
Includes API development, test suite, Docker support and a scalable environment setup.  
Designed with a focus on maintainability, code quality and easy future enhancements.

---

##  Features

- FastAPI based backend with organized folder structure  
- Modular code under `src/` for easy scalability  
- API routing & configuration handling  
- Test cases included under `tests/`  
- Dockerfile added for containerized deployment  
- Logging & audit tracking support  
- Requirements file for easy setup  
- .gitignore configured to keep repo clean  

---

##  Tech Stack

| Component | Technology |
|----------|------------|
| Language | Python |
| Framework | FastAPI |
| Dependency Management | pip / requirements.txt |
| Containerization | Docker |
| Testing | pytest |
| Storage | `.db` (SQLite default, extendable to MySQL/Postgres) |

---

## Project Structure
project/
├─ src/
│ ├─ api.py
│ ├─ config.py
│ ├─ sandbox.py
│ ├─ static/
│ └─ ...
├─ tests/
│ └─ test_sandbox.py
├─ Dockerfile
├─ requirements.txt
├─ audit_log.db
└─ .gitignore
