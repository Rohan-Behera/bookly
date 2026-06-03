from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging

logger = logging.getLogger('uvicorn.access')
logger.disabled = True


# In middleware we cannot raise exceptions we can only return response.
# we can modify the response such that we can show exception errors using JSONResponse


def register_middleware(app: FastAPI):

    @app.middleware('http')
    async def custom_logging(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        message = f"{request.method} - {request.url.path} - {response.status_code} completes after{processing_time}s"
        print(message)
        return response
    
    app.add_middleware(CORSMiddleware,
        allow_origins = ["*"], 
        allow_methods = ["*"], 
        allow_headers = ["*"],
        allow_credentials = True,
    )

    app.add_middleware(TrustedHostMiddleware,
                       allowed_hosts=["localhost", "127.0.0.1"]
                       )
    

    """
    Below is just an example for the authorization middleware it is similar to that of dependecy injection in FASTAPI.
    Always remember If you only need logic for some routes (like specific admin panels), use FastAPI Dependencies. 
    Middleware is "heavy" because it runs on every single call to your server.
    """
    # @app.middleware('http')
    # async def authorization(request: Request, call_next):
    #     if not "Authorization" in request.headers:
    #         return JSONResponse(
    #             content={
    #                 "message" : "not authenticated",
    #                 "resolution" : "please provide the right credentials to proceed"
    #             },
    #             status_code=status.HTTP_401_UNAUTHORIZED
    #         )
        
    #     response = await call_next(request)
    #     return response