import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    request = context.get("request")
    if request is not None:
        logger.warning(
            "API request rejected: method=%s path=%s status=%s",
            request.method,
            request.path,
            response.status_code,
        )

    messages = {
        400: "Некоректний запит.",
        401: "Потрібна автентифікація.",
        403: "Недостатньо прав для виконання дії.",
        404: "Запис або сторінку не знайдено.",
        405: "Цей HTTP-метод не підтримується.",
        406: "Запитаний формат відповіді не підтримується.",
        415: "Формат тіла запиту не підтримується.",
        429: "Забагато запитів. Спробуйте пізніше.",
    }

    response.data = {
        "error": {
            "message": messages.get(
                response.status_code,
                "Не вдалося виконати запит.",
            ),
            "details": response.data,
        }
    }

    return response
