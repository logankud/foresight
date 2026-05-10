"""``foresight.agents`` — agent abstraction layer.

Owns the ``AgentClient`` protocol, ``Tool`` registry, conversation persistence
helpers, and (eventually) one concrete agent implementation behind the
protocol. Real content lands across E6.* stories.

May import from ``foresight.core`` only.
"""

from __future__ import annotations
