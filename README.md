# CivicScheme AI - Production Ready

A production-ready, authenticated AI-powered platform for discovering and tracking Indian government schemes.

## 🚀 Features

- **AI-Powered Search** - MistralAI embeddings + FAISS vector search
- **Application Tracking** - Track scheme applications with status updates
- **Profile Management** - Personalized recommendations based on user profile
- **Multilingual Support** - 11 Indian languages supported
- **Production Ready** - Proper error handling, validation, and security

## 📋 Prerequisites

- Python 3.9+
- MistralAI API Key (required)
- PostgreSQL/SQLite database

## 🔧 Installation

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd RagProject
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in the project root:

```bash
# Required: Hugging Face API Key
HUGGINGFACE_API_KEY=hf_your_actual_key_here

# JWT Secret (generate a secure random string, min 32 chars)
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters-long

# Database
DATABASE_URL=sqlite:///./data/app.db

# Optional
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### 3. Get MistralAI API Key

 Add to `.env` file

### 4. Run the Application

```bash
# Development
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will:
- ✅ Validate Hugging Face API key at startup
- ✅ Initialize database
- ✅ Load AI models
- ❌ Exit with error if configuration is invalid

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Chat
- `POST /api/chat/message` - Send message and get AI recommendations

### Profile
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update profile
- `POST /api/profile/saved-schemes` - Save a scheme
- `GET /api/profile/saved-schemes` - Get saved schemes

### Tracking
- `POST /api/tracking/applications` - Create application tracker
- `GET /api/tracking/applications` - Get all applications
- `PATCH /api/tracking/applications/{id}` - Update application status
- `DELETE /api/tracking/applications/{id}` - Delete application


## 🔒 Security

- All endpoints (except auth) require JWT authentication
- Passwords are hashed with bcrypt
- CORS configured (update for production domains)
- API keys validated at startup
- No mock/fallback implementations

## 📊 Database Schema

### Users
- id, email, hashed_password, full_name, is_active

### UserProfile
- user_id, age, gender, income, occupation, location, etc.

### Application
- user_id, scheme_id, status, notes, deadline, dates

### SavedScheme
- user_id, scheme_id, scheme_name, category

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MistralAI API_KEY` | Yes |  API key () |
| `DEBUG` | No | Enable debug mode (default: false) |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |

## 🐛 Troubleshooting

### "Invalid Hugging Face API key"
- Ensure key starts with `hf_`
- Verify key has not expired
- Check key has "Read" permissions

### "Application cannot start"
- Check all required environment variables are set
- Ensure JWT_SECRET_KEY is at least 32 characters
- Verify database is accessible

### "Failed to initialize RAG pipeline"
- Check Hugging Face API is accessible
- Verify API key is valid
- Check internet connection


