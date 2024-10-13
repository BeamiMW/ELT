# menggunakan image base apache airflow versi 2.10.2 dengan python 3.10
FROM apache/airflow:2.10.2-python3.10

# ganti ke root user untuk instalasi paket
USER root

# install dependencies sistem yang dibutuhkan dan google chrome
RUN apt-get update && apt-get install -y \
    wget unzip xvfb libxi6 libgconf-2-4 curl gcc python3-dev \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libnspr4 libnss3 \
    libxcomposite1 libxrandr2 xdg-utils libx11-xcb1 libxss1 libxtst6 \
    libnss3 libatk1.0-0 && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# download dan install chrome driver sesuai dengan versi chrome yang terinstall
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/129.0.6668.89/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver-linux64.zip

# set environment variables untuk chrome dan chrome driver
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# copy file kredensial ke container
COPY gcloud_key.json /opt/airflow/gcloud_key.json

# Set izin pada file
RUN chmod 644 /opt/airflow/gcloud_key.json

# ganti ke user airflow
USER airflow

# upgrade pip dan install dependencies python yang diperlukan
RUN pip install --upgrade pip && \
    pip install \
    apache-airflow-providers-celery \  
    pandas \                          
    numpy \                          
    sqlalchemy-bigquery \             
    selenium \                        
    psycopg2-binary \                 
    python-dotenv \                   
    celery \                          
    redis \                           
    apache-airflow-providers-redis
