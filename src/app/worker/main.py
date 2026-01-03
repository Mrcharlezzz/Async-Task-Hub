import os

from src.setup.stream_config import configure_stream_publisher
from src.app.infrastructure.celery.app import celery_app


def main() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO")
    concurrency = os.getenv("CELERY_CONCURRENCY", "1")
    configure_stream_publisher()
    celery_app.worker_main(
        [
            "worker",
            "-l",
            log_level,
            "--concurrency",
            concurrency,
        ]
    )


if __name__ == "__main__":
    main()
