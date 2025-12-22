class TaskNotFoundError(Exception):
    """Raised when a task identifier does not exist in the task backend."""
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task with id '{task_id}' was not found.")
        self.task_id = task_id


class TaskAccessDeniedError(Exception):
    """Raised when a user attempts to access a task they do not own."""

    def __init__(self, task_id: str, user_id: str) -> None:
        super().__init__(f"User '{user_id}' has no access to task '{task_id}'.")
        self.task_id = task_id
        self.user_id = user_id
