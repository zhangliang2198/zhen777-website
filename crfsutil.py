from itsdangerous import URLSafeSerializer
import secrets

csrf_secret_key = "zhen777.xxx.yyy.zzz"  # 生成一个安全的密钥
csrf_serializer = URLSafeSerializer(csrf_secret_key)

def generate_csrf_token():
    csrf_token = secrets.token_hex(16)  # 生成一个新的随机值
    return csrf_serializer.dumps(csrf_token)


def validate_csrf_token(client_token: str, cookie_token: str):
    try:
        client_csrf_token = csrf_serializer.loads(client_token)
        cookie_csrf_token = csrf_serializer.loads(cookie_token)
    except:
        return False
    return client_csrf_token == cookie_csrf_token
