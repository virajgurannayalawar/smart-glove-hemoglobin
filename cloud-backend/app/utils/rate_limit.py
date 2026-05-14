from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# We configure the limiter to use the remote address as the key.
# For burst uploads from edge devices, we define a higher limit.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
