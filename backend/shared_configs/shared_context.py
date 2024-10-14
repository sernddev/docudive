import contextvars

from danswer.db.models import User
user = User(id="SYSTEM")
# Define the ContextVar in a shared module
user_id_context = contextvars.ContextVar("user_id", default=user.id)
