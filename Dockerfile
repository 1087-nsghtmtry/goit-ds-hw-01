FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pipenv

# копіюємо файли залежностей окремо для кешу
COPY Pipfile Pipfile.lock* /app/

# встановлюємо залежності в системний Python контейнера
RUN pipenv install --system --deploy

# копіюємо код
COPY . /app

CMD ["python", "main.py"]