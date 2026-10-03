from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from salary.application.ports.security import TokenClaims, TokenService
from salary.domain.errors import AuthenticationError
from salary.domain.models import Role


class JwtTokenService(TokenService):
    ALGORITHM = "HS256"

    def __init__(self, secret: str, ttl: timedelta) -> None:
        self._secret = secret
        self._ttl = ttl

    def issue(self, claims: TokenClaims) -> str:
        now = datetime.now(UTC)
        payload = {"sub": str(claims.user_id), "role": claims.role.value, "iat": now, "exp": now + self._ttl}
        return jwt.encode(payload, self._secret, algorithm=self.ALGORITHM)

    def decode(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self.ALGORITHM], options={"require": ["sub", "exp"]})
            return TokenClaims(user_id=int(payload["sub"]), role=Role(payload["role"]))
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise AuthenticationError("Недействительный или просроченный токен") from exc
