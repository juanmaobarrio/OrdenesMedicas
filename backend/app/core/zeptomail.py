from typing import Any, Dict, Optional
import httpx
from loguru import logger
from backend.app.core.config import settings


class ZeptoMailService:
    """Cliente asíncrono para envío de correos transaccionales a través de ZeptoMail (Zoho)."""

    def __init__(self):
        self.api_url = settings.ZEPTOMAIL_API_URL
        self.api_token = settings.ZEPTOMAIL_API_TOKEN
        self.from_email = settings.ZEPTOMAIL_FROM_EMAIL
        self.from_name = settings.ZEPTOMAIL_FROM_NAME
        self.bounce_address = settings.ZEPTOMAIL_BOUNCE_ADDRESS

    @property
    def is_configured(self) -> bool:
        return bool(self.api_token and self.api_token.strip() and "dummy" not in self.api_token.lower())

    async def enviar_correo(
        self,
        destinatario_email: str,
        destinatario_nombre: str,
        asunto: str,
        cuerpo_html: str,
    ) -> Dict[str, Any]:
        """Envía un correo mediante la API REST de ZeptoMail.
        Si la API no está configurada (ej. en desarrollo local), simula el envío y registra en logs.
        """
        destinatario_email = destinatario_email.strip().lower()
        destinatario_nombre = destinatario_nombre.strip() if destinatario_nombre else "Paciente"

        if not self.is_configured:
            logger.warning(
                f"[ZeptoMail MOCK] API Token no configurado. Simulando envío a {destinatario_email} | Asunto: '{asunto}'"
            )
            return {
                "success": True,
                "mock": True,
                "message_id": f"mock-zepto-{destinatario_email.split('@')[0]}",
                "message": "Envío simulado correctamente (modo desarrollo sin API Token de ZeptoMail)",
            }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Zoho-enczapikey {self.api_token.strip()}",
        }

        payload: Dict[str, Any] = {
            "from": {
                "address": self.from_email,
                "name": self.from_name,
            },
            "to": [
                {
                    "email_address": {
                        "address": destinatario_email,
                        "name": destinatario_nombre,
                    }
                }
            ],
            "subject": asunto,
            "htmlbody": cuerpo_html,
        }

        if self.bounce_address:
            payload["bounce_address"] = self.bounce_address

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code in (200, 201):
                    res_data = response.json()
                    data_obj = res_data.get("data", [{}])[0] if isinstance(res_data.get("data"), list) and res_data.get("data") else {}
                    message_id = data_obj.get("message_id") or res_data.get("request_id") or "zepto-sent"
                    logger.info(f"[ZeptoMail] Correo enviado exitosamente a {destinatario_email}. ID: {message_id}")
                    return {
                        "success": True,
                        "mock": False,
                        "message_id": message_id,
                        "message": "Correo enviado exitosamente vía ZeptoMail",
                    }
                else:
                    error_msg = f"Error ZeptoMail [{response.status_code}]: {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "mock": False,
                        "message_id": None,
                        "message": error_msg,
                    }
        except Exception as e:
            err = f"Excepción al conectar con ZeptoMail: {str(e)}"
            logger.error(err)
            return {
                "success": False,
                "mock": False,
                "message_id": None,
                "message": err,
            }


zepto_mail_service = ZeptoMailService()
