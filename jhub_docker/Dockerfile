FROM jupyterhub/jupyterhub:latest

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && pip install --no-cache-dir jupyterlab jupyter_server

# Создаём пользователя user1 с паролем
RUN useradd -m user1 && echo "user1:password" | chpasswd && adduser user1 sudo

# Устанавливаем права на директорию
RUN chown -R root:root /srv/jupyterhub

# Копируем конфигурацию и данные в контейнер
COPY jhub_data/jupyterhub.sqlite /srv/jupyterhub/jupyterhub.sqlite
COPY jhub_data/jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
# COPY jhub_data/jupyterhub_cookie_secret /srv/jupyterhub/jupyterhub_cookie_secret

# RUN chmod 600 /srv/jupyterhub/jupyterhub_cookie_secret

EXPOSE 8000

CMD ["jupyterhub"]