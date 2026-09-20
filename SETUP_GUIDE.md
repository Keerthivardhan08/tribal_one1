# Unified Tribal Scholarship Platform (UTSP) - Setup Guide

Welcome to the UTSP project! This guide will help you run the platform on your own local machine from scratch.

## Prerequisites
Before you start, make sure you have the following installed on your computer:
1. **Node.js** (v18 or higher) - For the React/Next.js frontend. Download from [nodejs.org](https://nodejs.org).
2. **Python** (v3.9 or higher) - For the Flask backend API. Download from [python.org](https://python.org).

---

## Step 1: Extract the Zip File
Unzip this package and open your terminal (Command Prompt, PowerShell, or VS Code Terminal) inside the extracted folder.

You will need to open **two separate terminal windows** (one for the backend, one for the frontend).

---

## Step 2: Start the Python Backend
The backend serves the API and the local JSON database.

1. Open your first terminal window and navigate into the `backend` folder:
   ```bash
   cd backend
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask API server:
   ```bash
   python -m app.main
   ```
*You should see a message saying the server is running on `http://127.0.0.1:8000`.*

---

## Step 3: Start the Next.js Frontend
The frontend contains the React user interface.

1. Open your **second** terminal window and navigate into the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install all the Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
*You should see a message saying the server is running on `http://localhost:3000`.*

---

## Step 4: Access the Application
Now that both servers are running, open your web browser and go to:
🌐 **[http://localhost:3000](http://localhost:3000)**

**Demo Login Credentials:**
- You can log in using any dummy credentials (e.g., username `test` and password `test`) for the **Student**, **Nodal Officer**, **Admin**, and **Bank** roles to explore the platform.

Enjoy!
