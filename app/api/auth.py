@router.post("/login", response_model=LoginResponse)
def login_user(login: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == login.email).first()

    if not user:
        print("LOGIN: No user found for", login.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    print("LOGIN: Stored hash =", user.hashed_password)
    print("LOGIN: Input password =", login.password)
    print("LOGIN: Password valid =", verify_password(login.password, user.hashed_password))

    if not verify_password(login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active or user.is_forgotten:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is no longer active.")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60*60*24*7
    )

    return {"access_token": access_token}
