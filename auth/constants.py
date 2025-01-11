class ValidRoles:
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"

    @classmethod
    def values(cls) -> list[str]:
        return [cls.ATTENDEE, cls.ORGANIZER, cls.ADMIN]


SECRET_KEY = "1e9356e2ef00d712c017be0e7f5e8ae5da1fa4f60522cc35638148566f0932f9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
