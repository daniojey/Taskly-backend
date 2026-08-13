# Taskly BACKEND

Taskly [Frontend](https://github.com/daniojey/Taskly-Frontend)

**Real-time task and team management platform with live notifications, session tracking, and built-in task discussions.**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-DRF-092E20?style=flat&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Redis](https://img.shields.io/badge/Redis-Celery-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

[Tech Stack](#tech-stack) • [Getting Started](#getting-started) • [Architecture](#architecture) • [Demo](#demo)

---

## Overview
 
Taskly is a group-based project management tool built for teams that need to organize work, track time, and communicate — all in one place. Managers can organize users into groups, spin up projects, assign tasks with deadlines, and see real-time statistics on how their team is spending time. Every task doubles as a lightweight chat, so discussion never gets separated from the work itself.

## Tech Stack
 
| Layer | Technology |
|---|---|
| **Backend** | Python, Django, Django REST Framework |
| **Real-time** | Django Channels, WebSockets |
| **Async tasks & queue** | Celery, Redis |
| **Database** | PostgreSQL |
| **Infrastructure** | Docker, Docker Compose |


## Architecture
 
```
┌─────────────┐      WebSocket       ┌──────────────────┐
│   React     │ ◄──────────────────► │  Django Channels  │
│  (Vite/TS)  │                      │                    │
└─────────────┘      REST (DRF)      └────────┬───────────┘
                                               │
                                    ┌──────────┼──────────┐
                                    │          │          │
                              ┌─────▼───┐ ┌────▼────┐ ┌───▼────┐
                              │PostgreSQL│ │  Celery │ │  Redis │
                              └──────────┘ └─────────┘ └────────┘
```
 
- **REST API** (DRF) handles CRUD for groups, projects, tasks, and sessions
- **Django Channels** manages WebSocket connections for live chat and notifications
- **Celery workers** process background jobs (notification generation, statistics)
- **Redis** acts as the Channels layer backend and Celery broker

## Demo
 
<!-- Add a short screen recording / GIF / hosted demo link here -->
 
> 🎥 Demo video coming soon

## Getting Started
 
### Prerequisites
- Docker & Docker Compose

### Setup
 
```bash
# Clone the repository
git https://github.com/daniojey/Taskly-backend.git
cd Taskly-backend

# create docker-compose.override.yml and put this code
services:
  web:
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./Django:/app

  celery:
    volumes:
      - ./Django:/app

  celerybeat:
    volumes:
      - ./Django:/app

# Create a .env file in the project root (Taskly-Frontend folder)
# And specify the parameters as shown in this example 
SECRET_KEY = <your secket key> # put here django secret key
ENABLE_CELERY = True # default celery On 
REDIS_URL = redis://localhost:6379 # default redis url if you have another redis url just change it
DATABESE_URL_DOCKER: postgres://task_user:admin@db:5432/Taskly # example database url for docker

# After all build and run docker-compose
docker compose up --build -d
```

After install backend you can install Frontend part

Taskly [Frontend](https://github.com/daniojey/Taskly-Frontend#getting-started)

---
 
Built by [Dmytro](https://github.com/daniojey)
