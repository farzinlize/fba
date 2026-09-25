from celery.backends.database.session import SessionManager as CelerySessionManager


class SessionManager(CelerySessionManager):
    """
    Override the Celery SessionManager
    """

    def __init__(self) -> None:
        super().__init__()

        # Prevent automatic creation of task result tables defined internally by Celery
        self.prepared = True
