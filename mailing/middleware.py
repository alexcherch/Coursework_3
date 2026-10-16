"""Middleware для управления клиентским кешированием."""

import logging

logger = logging.getLogger("django")


class ClientCacheMiddleware:
    """Добавляет HTTP-заголовки Cache-Control для клиентского (браузерного) кеша.

    Логика:
        - GET-запросы для авторизованных → private, max-age=60 (только в браузере юзера, 1 минута)
        - GET-запросы для анонимов → public, max-age=300 (можно кешировать в CDN, 5 минут)
        - Не-GET запросы (POST/PUT/DELETE) → no-store (нельзя кешировать, изменяет данные)

    Это даёт «клиентское кеширование» — браузер сам решает, переиспользовать ли ответ.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Не трогаем ответы с ошибками и редиректы — там уже свои заголовки
        if response.status_code >= 400 or 300 <= response.status_code < 400:
            return response

        if request.method == "GET":
            if request.user.is_authenticated:
                response["Cache-Control"] = "private, max-age=60"
            else:
                response["Cache-Control"] = "public, max-age=300"
        else:
            response["Cache-Control"] = "no-store"

        return response


class ErrorLoggingMiddleware:
    """Логирует необработанные исключения (5xx) в errors.log.

    Middleware вызывается Django, если view выбросил исключение.
    Мы логируем его с уровнем ERROR и добавляем контекст (путь, метод, юзер).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Вызывается Django при необработанном исключении."""
        user = request.user.email if request.user.is_authenticated else "anonymous"
        logger.error(
            f"Необработанное исключение на {request.method} {request.path} "
            f"(user: {user}): {type(exception).__name__}: {exception}"
        )
        return None
