"""
Script de login único no Instagram.
Salva a sessão em auth/instagram_session para uso futuro.

Execute uma vez:
    python setup_instagram.py
"""

import instaloader
from pathlib import Path

SESSION_FILE = Path("auth/instagram_session")
SESSION_FILE.parent.mkdir(exist_ok=True)

username = input("Instagram username: ").strip()
password = input("Instagram password: ").strip()

L = instaloader.Instaloader()

try:
    L.login(username, password)
    print("Login realizado com sucesso!")
except instaloader.TwoFactorAuthRequiredException:
    print("Código 2FA enviado para seu celular/app.")
    code = input("Digite o código 2FA: ").strip()
    L.two_factor_login(code)
    print("Login com 2FA realizado com sucesso!")

L.save_session_to_file(str(SESSION_FILE))
print(f"Sessão salva em: {SESSION_FILE}")
print("Agora rode: python main.py --collect")
