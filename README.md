# College ERP Backend (Django REST)

## Run
1. Create/activate virtual environment.
2. Install deps:
   - `pip install -r requirements.txt`
3. Migrate DB:
   - `python manage.py makemigrations`
   - `python manage.py migrate`
4. Create admin user:
   - `python manage.py createsuperuser`
5. Start server:
   - `python manage.py runserver`

## API Base
- `http://127.0.0.1:8000/api`

## Auth
- `POST /api/token/`
- `POST /api/token/refresh/`
- `GET /api/users/me/` (Bearer token required)

## Main Modules
- Courses: `/api/courses/`
- Attendance: `/api/attendance/`
- Results: `/api/results/`
- Timetable: `/api/timetable/`
