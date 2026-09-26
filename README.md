# Smart Waste Management Simulator (SWMS)

This repository contains the **Smart Waste Management Simulator**, an integrated decision-support web application for local authorities to simulate waste generation, capacity needs, and GIS location planning.

---

## Prerequisites

Ensure you have the following installed on your local machine:
- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)
- **Git**
- *(Optional)* **PostgreSQL / PostGIS** (if testing against PostgreSQL; SQLite works out-of-the-box for local dev)

---


Follow these step-by-step instructions to set up and run the application on your local machine:

### 1. Clone the Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd HPL/waste-simulator-main
```

---

### 2. Backend Setup (FastAPI + Python)

1. **Navigate to the backend directory:**
2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Copy `.env.example` from the project root to `.env`:
   ```bash
   cp ../.env.example ../.env
   ```
   *Note: By default, SQLite is used for local development. If using PostgreSQL, update `DATABASE_URL` in `.env`.*

5. **Start the Backend Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   -  API documentation will be available at: **`http://localhost:8000/docs`**

---

### 3. Frontend Setup (React + Vite)

Open a **new terminal tab or window**:

1. **Navigate to the frontend directory:**

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the Frontend Development Server:**
   - **Using PowerShell (Windows script):**
     ```powershell
     .\start-frontend.ps1
     ```
   - **Or directly with npm:**
     ```bash
     npm run dev
     ```

4. Access the web interface at **`http://localhost:5173`** (or the URL output in your terminal).

---

## Initial User Setup

When running the system for the first time, register the first user account as `SUPER_ADMIN` via the register UI or API (`http://localhost:8000/docs`) to set up initial administrative privileges.