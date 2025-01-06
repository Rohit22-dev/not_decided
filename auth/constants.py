class ValidRoles:
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"
    
    @classmethod
    def values(cls) -> list[str]:
        return [cls.ATTENDEE, cls.ORGANIZER, cls.ADMIN]