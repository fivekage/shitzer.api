
Create virtual env
https://fastapi.tiangolo.com/virtual-environments/#create-a-virtual-environment
.venv\Scripts\Activate.ps1

movie-recommendation/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── item.py
│   │   └── like.py
│   └── routers/
│       ├── __init__.py
│       ├── users.py
│       ├── items.py
│       └── likes.py
├── .env
├── requirements.txt
└── docker-compose.yml