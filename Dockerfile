# Image légère : python slim (au lieu de l'image complète, ~150 Mo au lieu de ~1 Go)
FROM python:3.13-slim

# Empêche Python de générer des fichiers .pyc et force l'affichage direct des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# On copie d'abord uniquement requirements.txt pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis on copie le reste du code
COPY . .

EXPOSE 5000

# Gunicorn = serveur de production Python 
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
