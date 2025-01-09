class EventStatus:
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"

    @classmethod
    def values(cls) -> list[str]:
        return [cls.UPCOMING, cls.ONGOING, cls.COMPLETED]
