"""Tiny in-process event bus + structured decision log."""
import json
import logging
from collections import defaultdict
from typing import Callable

log = logging.getLogger("scamshield.decisions")


class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, fn: Callable) -> None:
        self._subs[topic].append(fn)

    def publish(self, topic: str, **data) -> None:
        log.info(json.dumps({"event": topic, **data}, default=str, ensure_ascii=False))
        for fn in self._subs[topic]:
            try:
                fn(topic, data)
            except Exception:  # noqa: BLE001
                log.exception("subscriber failed")


bus = EventBus()
