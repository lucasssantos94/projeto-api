from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import url_for
import asyncio
import json
from uuid import UUID




class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

def get_serializer(app):
    return URLSafeTimedSerializer(
        app.config['SECRET_KEY'],
        serializer=UUIDEncoder
    )

def generate_reset_token(app, user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    salt = app.config.get('SECURITY_PASSWORD_SALT', 'password-reset-salt')
    return serializer.dumps(str(user_id), salt=salt)

def verify_reset_token(app, token, max_age=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    salt = app.config.get('SECURITY_PASSWORD_SALT', 'password-reset-salt')
    try:
        user_id_str = serializer.loads(token, salt=salt, max_age=max_age)
        return UUID(user_id_str)
    except Exception as e:
        app.logger.error(f"Falha na verificação do token: {str(e)}")
        return None


async def send_reset_email(app, user_email, user_nickname, user_id):
    try:
        with app.app_context():
            token = generate_reset_token(app, user_id)
            frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:5173')
            reset_url = f"{frontend_url}/redefinir-senha?token={token}"
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Redefinição de Senha</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding: 40px 0;">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
          <tr>
            <td align="center" style="font-size: 24px; color: #333333;">
              <strong>Olá, {user_nickname}!</strong>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 0; font-size: 16px; color: #666666;">
              Você solicitou a redefinição da sua senha. Para isso, clique no botão abaixo:
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 20px 0;">
              <a href="{reset_url}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-size: 16px;">Redefinir Senha</a>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 0; font-size: 14px; color: #999999;">
              Este link expira em 1 hora. Se você não solicitou essa alteração, apenas ignore este e-mail.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
            
            msg = Message(
                'Redefinição de Senha',
                recipients=[user_email],
                html=html
            )
            
            mail = app.extensions['mail']
            await asyncio.to_thread(mail.send, msg)
            app.logger.info(f"Email de redefinição enviado para {user_email}")
            
    except Exception as e:
        app.logger.error(f"Falha ao enviar email: {str(e)}", exc_info=True)
        raise