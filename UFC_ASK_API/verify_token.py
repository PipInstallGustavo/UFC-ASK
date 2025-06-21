from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import List

#mesma chave secreta usada no Node.js
SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = os.getenv("ALG")  # mesmo usado na aplicação Node.js

security = HTTPBearer()

#verificar se o token é válido
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        )

#verificar o role do usuário para permissões e segurança de rotas
def require_role(roles: List[str]):
    def role_checker(payload: dict = Depends(verify_token)):
        user_role = payload.get("role")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso Negado",
            )
        return payload  
    return role_checker