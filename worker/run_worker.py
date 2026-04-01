import os
from redis import Redis
from rq import Worker, Queue, Connection
from app.schema import bootstrap_schema

def main():
    bootstrap_schema()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        qs = [Queue(os.getenv("RQ_DEFAULT_QUEUE", "default"))]
        w = Worker(qs)
        w.work(with_scheduler=False)

if __name__ == "__main__":
    main()
