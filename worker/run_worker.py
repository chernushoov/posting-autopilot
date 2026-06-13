import os
from redis import Redis
from rq import Worker, Queue, Connection
from app.schema import bootstrap_schema
from common.env_guard import validate_runtime_environment


def main():
    validate_runtime_environment("worker")
    bootstrap_schema()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    # RQ default job_timeout is 180s. Telegram anti-spam delay (POST_DELAY_MIN/MAX
    # in common/tg_client.py) plus Telethon connect/send margins can run multi-minutes,
    # so jobs were silently expiring. Allow override via env, default 900s.
    worker_ttl = int(os.getenv("RQ_WORKER_TIMEOUT", "900"))
    with Connection(conn):
        qs = [Queue(os.getenv("RQ_DEFAULT_QUEUE", "default"), default_timeout=worker_ttl)]
        w = Worker(qs)
        w.work(with_scheduler=False)


if __name__ == "__main__":
    main()
