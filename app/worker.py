from celery import Celery
from kombu import Exchange, Queue

celery = Celery(
    "worker",
    broker="pyamqp://guest@rabbitmq//",
    backend="rpc://",
    include=["app.tasks"],
)

urls_exchange = Exchange("urls", type="direct")
dead_letter_exchange = Exchange("dead_letter_exchange", type="direct")

celery.conf.task_queues = (
    Queue(
        "urls",
        exchange=urls_exchange,
        routing_key="urls",
        queue_arguments={
            "x-dead-letter-exchange": "dead_letter_exchange",
            "x-dead-letter-routing-key": "dead_letter",
        },
    ),
    Queue(
        "dead_letter",
        exchange=dead_letter_exchange,
        routing_key="dead_letter",
    ),
)

celery.conf.task_default_queue = "urls"
celery.conf.task_default_exchange = "urls"
celery.conf.task_default_routing_key = "urls"
celery.conf.task_acks_on_failure_or_timeout = False
celery.conf.task_routes = {
    "app.tasks.fetch_url": {"queue": "urls", "routing_key": "urls"},
}


@celery.on_after_configure.connect
def declare_dead_letter_topology(sender, **kwargs):
    with sender.connection_or_acquire() as connection:
        dead_letter_exchange(connection.default_channel).declare()
        Queue(
            "dead_letter",
            exchange=dead_letter_exchange,
            routing_key="dead_letter",
        )(connection.default_channel).declare()