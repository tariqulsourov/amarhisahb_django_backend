import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled 500 error
    if response is None:
        view = context.get('view', 'UnknownView')
        logger.error(f"Unhandled Exception in API view {view}: {exc}", exc_info=True)
        return Response(
            {
                "error": "Internal Server Error",
                "detail": str(exc)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
