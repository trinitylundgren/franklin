#!/usr/bin/env python3

from precise_runner import PreciseEngine, PreciseRunner

engine = PreciseEngine("precise-engine/precise-engine", "ok-franklin.pb")
runner = PreciseRunner(engine, on_activation=lambda: print("hello"))
runner.start()

# Sleep forever
from time import sleep

while True:
    sleep(10)
