# System Design Document

## Architecture
Three-tier architecture (Frontend, Backend, Database)

## Components
### Authentication Service
Handles user authentication and authorization

### Database Layer
Manages data persistence and retrieval

### Business Logic Layer
Implements core business rules and workflows

### Frontend UI
User interface components and views

### API Gateway
Manages API requests and responses

## Data Models
### User
- Fields: id, username, email, password_hash, created_at, updated_at
- Relationships: Has many: Sessions, Activities

### Session
- Fields: id, user_id, token, expires_at, created_at
- Relationships: Belongs to: User

### File
- Fields: id, name, description, status, created_at, updated_at
- Relationships: Belongs to: User

### Task
- Fields: id, name, description, status, created_at, updated_at
- Relationships: Belongs to: User

### Team
- Fields: id, name, description, status, created_at, updated_at
- Relationships: Belongs to: User

