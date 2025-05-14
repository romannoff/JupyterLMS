from jupyterhub.auth import LocalAuthenticator
from jupyterhub.spawner import LocalProcessSpawner
from jupyterhub.auth import Authenticator

# Конфигурация аутентификации
c = get_config()

# Используем LocalAuthenticator для аутентификации пользователей
c.JupyterHub.authenticator_class = LocalAuthenticator

# Разрешаем токен для user1
c.LocalAuthenticator.create_system_users = True

c.JupyterHub.tornado_settings = {
    'cookie_secret': '/srv/jupyterhub/jupyterhub_cookie_secret',
    'signed_cookie_secret': '/srv/jupyterhub/jupyterhub_cookie_secret',
}

# Установка пользователей
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import base

# Авторизация для существующего пользователя
c.Authenticator.allowed_users = {'user1'}
c.Authenticator.admin_users = {'user1'}

# Настройка API токена для взаимодействия с вашим приложением
c.JupyterHub.api_tokens = {
    "07551b6a34fa4bbbac6fe6d3645fc6d8": "user1"  # Задайте токен здесь
}
c.Spawner.cmd = ['jupyterhub-singleuser']
c.Spawner.environment = {
    'JUPYTERHUB_SINGLEUSER_APP': 'jupyter_server.serverapp.ServerApp'
}