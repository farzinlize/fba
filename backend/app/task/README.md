## Task overview

Tasks are implemented using Celery.
For implementation details, see [#225](https://github.com/fastapi-practices/fastapi-best-architecture/discussions/225).

## Scheduled tasks

Define scheduled tasks in `backend/app/task/tasks/beat.py`.

### Simple tasks

Write task code in `backend/app/task/tasks/tasks.py`.

### Hierarchical tasks

You can organize tasks into subdirectories for a clearer structure. Follow these requirements:

1. Create a Python package under `backend/app/task/tasks`.
2. Add a `tasks.py` file in that package and define the tasks in it.

## Message broker

Select the message broker using `CELERY_BROKER`; Redis and RabbitMQ are supported.

Redis is recommended for local debugging.

RabbitMQ is required in production.
