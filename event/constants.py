class EventStatus:
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"

    @classmethod
    def values(cls) -> list[str]:
        return [cls.UPCOMING, cls.ONGOING, cls.COMPLETED]
