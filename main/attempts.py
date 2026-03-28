# This module is retained only for compatibility with extremely old
# code that depended on the original schema of the ``attempts`` table.
#
# The application now uses ``main.models.save_attempt`` which understands the
# current column layout (``section``/``topic``/``total_q``/``avg_speed``)
# and does not rely on the obsolete ``speed`` column.  The legacy version of
# ``save_attempt`` below will raise so that callers are forced to migrate.

import uuid
from datetime import datetime, timezone
from db import conn as get_conn

def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def save_attempt(*args, **kwargs):
    raise RuntimeError(
        "attempts.save_attempt is deprecated; use main.models.save_attempt instead"
    )