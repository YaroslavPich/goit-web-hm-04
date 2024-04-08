FROM python:3.12

ENV APP_HOME /main

WORKDIR $APP_HOME

COPY . .


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

CMD ["python", "main.py"]