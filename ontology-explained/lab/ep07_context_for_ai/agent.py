"""The agent: the model picks tools, the MCP server runs them on the graph."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep07_context_for_ai.step import agent, retrieve, verdict_agent


def main(rows=None):
    # start graph_mcp.py over stdio, offer its tools, run each call the model
    # asks for (saved model turns unless LAB_LLM is set)
    trace, calls, answer = asyncio.run(agent())
    print("== agent: the model calls the graph as tools, through MCP ==")
    print("\n".join(trace))
    rows = retrieve() if rows is None else rows  # who it should name
    verdict(*verdict_agent(calls, answer, rows))


if __name__ == "__main__":
    main()
