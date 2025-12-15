# Competitive Intelligence Dashboard

A dashboard for monitoring competitor pricing across delivery platforms (DoorDash, Uber Eats).

## Project Structure

```
FORKAST_DEMO/
├── frontend/          # Next.js 14 frontend (TypeScript + Tailwind CSS)
├── backend/           # FastAPI backend (Python 3.11+)
├── PRD.md            # Product Requirements Document
└── README.md         # This file
```

## Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **npm** (comes with Node.js)

## Installation & Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Start the Backend Server

From the `backend` directory (with virtual environment activated):

```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### Start the Frontend Server

From the `frontend` directory:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Verifying Connectivity

1. Start the backend server first
2. Start the frontend server
3. Open http://localhost:3000 in your browser
4. You should see a green "Status: ok" message indicating successful backend connection

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check endpoint |
| GET | `/` | API information |

## Tech Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- React 18

### Backend
- FastAPI
- Python 3.11+
- SQLAlchemy
- Pydantic
- Uvicorn
