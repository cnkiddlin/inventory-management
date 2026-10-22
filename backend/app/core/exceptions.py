from typing import Any


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "bad_request",
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str = "请求的资源不存在", details: Any = None) -> None:
        super().__init__(message, status_code=404, code="not_found", details=details)


class ConflictError(AppError):
    def __init__(self, message: str = "当前状态不允许执行该操作", details: Any = None) -> None:
        super().__init__(message, status_code=409, code="conflict", details=details)


class ValidationError(AppError):
    def __init__(self, message: str = "请求参数不合法", details: Any = None) -> None:
        super().__init__(message, status_code=422, code="validation_error", details=details)

