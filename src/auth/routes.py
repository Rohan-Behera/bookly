from fastapi import APIRouter, Depends, status
from .schemas import (
    UserCreateModel,
    UserLoginModel,
    UserBooksModel,
    EmailModel,
    PasswordRequestModel,
    PasswordResetConfirmModel,
)
from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from .utils import (
    create_access_token,
    verify_password,
    create_url__safe_token,
    decode_url_safe_token,
    generate_password_hash,
)
from fastapi.responses import JSONResponse
from datetime import timedelta
from src.config import Config
from .dependencies import (
    RefreshTokenBearer,
    AccessTokenBearer,
    get_current_user,
    RoleChecker,
    get_user_service,
)
from datetime import datetime
from src.db.redis import add_jti_to_blocklist
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from src.mail import mail, create_message

# objects
auth_router = APIRouter()


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    """
    Create user account using email, username, first_name, last_name
    params:
        user_data: UserCreateModel
    """
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()

    new_user = await user_service.create_user(user_data, session)
    token = create_url__safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/V1/auth/verify/{token}"
    message = create_message(
        recipient=[email], subject="Verify your email", template_body={"link": link},
    )
    await mail.send_message(message=message, template_name="verify_email.html")

    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }


@auth_router.get("/verify/{token}")
async def verify_user_account(
    token: str,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(email=user_email, session=session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"Message": "Account verified sucessfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"Message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):

    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        password_valid = verify_password(password, user.password)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role,
                }
            )

            refresh_token = create_access_token(
                user_data={"email": user.email, "user_uid": str(user.uid)},
                refresh=True,
                expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRY),
            )

            return JSONResponse(
                content={
                    "message": "login Successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"email": user.email, "uuid": str(user.uid)},
                }
            )

        raise InvalidCredentials()


@auth_router.get("/refresh-token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_date = token_details["exp"]

    if datetime.fromtimestamp(expiry_date) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise InvalidToken()


@auth_router.get("/me", response_model=UserBooksModel)
async def get_me(
    user=Depends(get_current_user), _: bool = Depends(RoleChecker(["admin", "user"]))
):
    return user


@auth_router.post("/send-mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses
    message = create_message(recipient=emails, subject="Welcome", template_body={"title": "Welcome to Bookly", "message": "Thanks for joining us!"},)

    await mail.send_message(message=message, template_name="welcome.html")

    return {"Message": "Email sent sucessfully"}


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"Message": "logout Sucessfully"}, status_code=status.HTTP_200_OK
    )


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordRequestModel):

    email = email_data.email

    token = create_url__safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/V1/auth/password-reset-confirm/{token}"
    message = create_message(
        recipient=[email], subject="Reset your Password", template_body={"link": link}
    )
    await mail.send_message(message=message, template_name="password_reset.html")

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password"
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/password-reset-confirm/{token}")
async def password_reset_confirm(token: str):
    token_data = decode_url_safe_token(token)

    if not token_data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    return JSONResponse(
        content={"message": "Token is valid", "token": token},
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def reset_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
):

    new_password = passwords.new_password
    confirm_password = passwords.confirm_password

    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords donot match"
        )

    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(email=user_email, session=session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(
            user, {"password": generate_password_hash(new_password)}, session
        )

        return JSONResponse(
            content={"Message": "Password Reset sucessfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"Message": "Error occured during password reset"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
