from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(BaseAPIException):
    def __init__(self, detail: str = "认证失败"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseAPIException):
    def __init__(self, detail: str = "权限不足"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(BaseAPIException):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(BaseAPIException):
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileUploadError(BaseAPIException):
    def __init__(self, detail: str = "文件上传失败"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class AnalysisError(BaseAPIException):
    def __init__(self, detail: str = "分析失败"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIServiceError(BaseAPIException):
    def __init__(self, detail: str = "AI服务调用失败"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
