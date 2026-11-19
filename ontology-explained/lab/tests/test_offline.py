"""Every step runs with the network blocked and no LAB_* settings: recorded answers only."""
import os
import subprocess
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
NETBLOCK = Path(__file__).resolve().parent / "netblock"
STEPS = sorted(LAB.glob("ep*/step.py"))


def offline_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("LAB_")}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(NETBLOCK), env.get("PYTHONPATH")]))
    return env


def test_network_is_blocked():
    code = "import socket; socket.create_connection(('127.0.0.1', 9))"
    r = subprocess.run(["uv", "run", "python", "-c", code], cwd=LAB, env=offline_env(),
                       capture_output=True, timeout=600)
    assert r.returncode != 0
    assert b"network blocked by lab/tests/netblock" in r.stderr


def test_live_api_fails_when_blocked():
    # the block reaches the steps: asking ep06 for the live API fails, as it would with no network
    r = subprocess.run(["uv", "run", "ep06_real_data/step.py", "--only", "api"], cwd=LAB,
                       env={**offline_env(), "LAB_API": "live"}, capture_output=True, timeout=600)
    assert r.returncode == 2
    assert b"Can't reach the API" in r.stderr


@pytest.mark.parametrize("step", STEPS, ids=[s.parent.name for s in STEPS])
def test_step_runs_offline(step):
    r = subprocess.run(["uv", "run", str(step.relative_to(LAB))], cwd=LAB, env=offline_env(),
                       capture_output=True, timeout=600)
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == (step.parent / "expected.txt").read_text(encoding="utf-8")
