# NETCRAFT API

A Flask REST API with MySQL database for user authentication and project management, built with Docker.

## Features

- User authentication with JWT tokens
- Project management (CRUD operations)
- User management
- MySQL database with proper relationships
- Docker containerization
- Blueprint-based architecture

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/change-password` - Change user password (requires JWT)
- `POST /api/auth/forgot-password` - Request password reset

### Projects
- `POST /api/projects/save` - Create/save a project (requires JWT)
- `GET /api/projects/my-projects` - Get user's projects (requires JWT)
- `GET /api/projects/{project_ulid}` - Get project by ULID (requires JWT)
- `DELETE /api/projects/{project_ulid}` - Delete project (requires JWT)

### Users
- `GET /api/users/{user_ulid}` - Get user information (requires JWT)

## Setup and Running

### Prerequisites
- Docker
- Docker Compose

### Environment Variables
Create a `.env` file in the root directory:
```
DATABASE_URL=mysql+pymysql://netcraft_user:netcraft_password@localhost:3306/netcraft
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
FLASK_ENV=development
```

### Running with Docker Compose

1. Clone the repository
2. Navigate to the project directory
3. Build and run the containers:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:3000`

### Database Schema

The application uses two main tables:

#### Users
- `user_ulid` (VARCHAR(26), PRIMARY KEY)
- `nickname` (VARCHAR(50), UNIQUE)
- `email` (VARCHAR(255), UNIQUE)
- `password_hash` (VARCHAR(255))
- `first_name` (VARCHAR(100))
- `last_name` (VARCHAR(100))
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Projects
- `project_ulid` (VARCHAR(26), PRIMARY KEY)
- `name` (VARCHAR(100))
- `data` (JSON)
- `owner_ulid` (VARCHAR(26), FOREIGN KEY)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Development

### Project Structure
```
├── app.py                 # Main application entry point
├── docker-compose.yaml    # Docker services configuration
├── Dockerfile            # Flask app container
├── requirements.txt      # Python dependencies
└── app/
    ├── __init__.py       # App factory
    ├── config.py         # Configuration
    ├── auth/             # Authentication blueprint
    ├── common/           # Shared utilities and models
    ├── projects/         # Projects blueprint
    └── users/            # Users blueprint
```

### Authentication
The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Password Requirements
- 8-30 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain at least one number

## Example Usage

### Register a new user
```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "johndoe",
    "email": "john@example.com",
    "password": "Password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "Password123"
  }'
```

### Create a project
```bash
curl -X POST http://localhost:3000/api/projects/save \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "name": "My Project",
    "data": {"key": "value"}
  }'
```
