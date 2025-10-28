

Quick start (dev):
1. Create & activate virtualenv:
   python -m venv venv
   source venv/bin/activate   
   # or venv\Scripts\activate on Windows
2. Install:
   pip install -r requirements.txt
3. Run migrations & create superuser:
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
4. Run server:
   python manage.py runserver
5. Open http://127.0.0.1:8000/

