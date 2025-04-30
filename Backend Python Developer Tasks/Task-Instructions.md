# Backend Developer Exercise - Medium Level

## Time Allocation
- Total: 3-4 hours
- Task A: ~1.5 hours
- Task B: ~2.5 hours

## Project Context
You're working on a content management system (CMS) API that handles users, content, categories, and permissions. The API uses FastAPI, SQLAlchemy with PostgreSQL, Alembic for migrations, and Celery for background tasks.

## Task A: Code Review and Optimization Exercise

Review the provided code in the following files:
- `app/main.py`
- `app/api/endpoints/users.py`
- `app/api/endpoints/content.py`
- `app/models/user.py`
- `app/models/content.py`
- `app/core/auth.py`
- `app/core/security.py`
- `app/worker.py`

**Your task is to review the code and:**
1. Identify at least 5 issues or bugs
2. Identify at least 3 opportunities for performance optimization
3. Suggest architectural improvements for better code organization

For each issue you find:
1. Identify the file and line number
2. Explain what the issue is and why it's problematic
3. Provide a fixed version of the code

## Task B: Implementation Exercise

Implement a role-based access control (RBAC) system with the following requirements:

1. **Database Models**:
   - Design and implement role and permission models
   - Set up appropriate relationships with the user model
   - Implement database migrations

2. **Authentication and Authorization**:
   - Implement OAuth2 with JWT tokens
   - Create a permission-based middleware/dependency
   - Enable role-based endpoint access

3. **API Endpoints**:
   - CRUD operations for roles and permissions
   - Endpoints to assign roles to users
   - Endpoints to assign permissions to roles

4. **Background Tasks**:
   - Implement a task for periodic permission auditing
   - Create a task for user session tracking

**Additional Requirements**:
- Implement proper transaction handling for critical operations
- Use SQLAlchemy relationships and joins efficiently
- Apply FastAPI dependency injection patterns
- Follow REST API best practices

## Submission Requirements

1. For Task A, submit a document with your analysis including:
   - Issues/bugs identified with fixes
   - Performance optimization opportunities
   - Architectural improvement suggestions

2. For Task B, submit:
   - All implementation code files
   - Alembic migration scripts
   - Brief documentation explaining your design decisions

## Evaluation Criteria

You will be evaluated on:
- Thoroughness of code review
- Quality of performance optimization suggestions
- Proper implementation of RBAC functionality
- Database schema design and relationship modeling
- Security best practices in authentication/authorization
- Effective use of FastAPI, SQLAlchemy, and Celery features
- Code organization and maintainability
- Transaction handling and data integrity approaches
