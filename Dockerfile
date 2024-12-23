FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    default-libmysqlclient-dev \
    pkg-config \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# mecab-python3 looks for /usr/local/etc/mecabrc; Debian puts it in /etc/mecabrc
RUN mkdir -p /usr/local/etc && ln -sf /etc/mecabrc /usr/local/etc/mecabrc

# Install mecab-ko-dic (Korean dictionary)
# Colab script uses Jupyter "!" syntax and does not work in plain bash
RUN cd /tmp && \
    curl -sL -o mecab-ko-dic-2.1.1-20180720.tar.gz https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz && \
    tar xfz mecab-ko-dic-2.1.1-20180720.tar.gz && \
    cd mecab-ko-dic-2.1.1-20180720 && \
    ./configure && \
    make && \
    make install && \
    ldconfig && \
    rm -rf /tmp/mecab-ko-dic-2.1.1-20180720 /tmp/mecab-ko-dic-2.1.1-20180720.tar.gz

# mecab-ko-dic 경로 (make install 기본 prefix=/usr/local). 여러 환경에서 안정적으로 사용하려면 ENV로 지정.
ENV MECAB_DIC_PATH=/usr/local/lib/mecab/dic/mecab-ko-dic

# Install Poetry
RUN pip install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy project files
COPY src/ ./src/
COPY data/ ./data/

# Create models directory
RUN mkdir -p /app/models

WORKDIR /app/src

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
