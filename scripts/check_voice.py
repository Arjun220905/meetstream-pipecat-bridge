"""Paid-provider smoke test over local WebSockets; this is NOT a live meeting test."""

import argparse
import asyncio
import base64
import json
import os
import socket
import sys
import tempfile
import wave
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from loguru import logger
from pipecat.frames.frames import LLMTextFrame, TranscriptionFrame
from pipecat.observers.base_observer import BaseObserver
from websockets.asyncio.client import connect

from meetstream_pipecat.agent import create_agent
from meetstream_pipecat.server import create_app
from meetstream_pipecat.store import Store


class Evidence(BaseObserver):
    def __init__(self):
        super().__init__(observe_every_push=False)
        self.transcripts = []
        self.answers = []

    async def on_push_frame(self, data):
        if isinstance(data.frame, TranscriptionFrame):
            self.transcripts.append(data.frame.text)
        if isinstance(data.frame, LLMTextFrame):
            self.answers.append(data.frame.text)


def read_pcm(path):
    with wave.open(str(path)) as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 48000):
            raise ValueError("Test WAV must be 48 kHz mono PCM16")
        return audio.readframes(audio.getnframes())


async def check(args):
    question = read_pcm(args.question)
    interruption = read_pcm(args.interrupt_with) if args.interrupt_with else None
    evidence = Evidence()

    def factory(transport):
        worker = create_agent(transport)
        worker.add_observer(evidence)
        return worker

    directory = tempfile.TemporaryDirectory()
    store = Store(directory.name)
    session_id, session_token = store.reserve("https://meet.google.com/synthetic")
    store.bind(session_id, "provider-smoke-test")
    # This synthetic peer must never call MeetStream's real cleanup API.
    os.environ["EXTERNAL_REAPER"] = "true"
    app = create_app("local-provider-test-token", agent_factory=factory, store=store)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    base = f"ws://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
    serving = asyncio.create_task(server.serve(sockets=[sock]))
    sending = None
    output_bytes = after_interrupt = 0
    interrupted = resumed = interruption_sent = False
    try:
        while not server.started:
            if serving.done():
                await serving
                raise RuntimeError("Smoke test server failed to start")
            await asyncio.sleep(0.02)
        async with (
            connect(base + f"/bridge/audio?session={session_id}&token={session_token}") as audio,
            connect(base + f"/bridge?session={session_id}&token={session_token}") as control,
        ):
            for ws in (audio, control):
                await ws.send(json.dumps({"type": "ready", "bot_id": "provider-smoke-test"}))
            await asyncio.sleep(2)  # Allow the streaming provider connections to open.

            async def speak(pcm):
                pcm += bytes(1920 * 100)  # Two seconds of silence for turn completion.
                for offset in range(0, len(pcm), 1920):
                    await audio.send(
                        b"\x01\x05\x00human\x05\x00Alice" + pcm[offset : offset + 1920]
                    )
                    await asyncio.sleep(0.02)

            sending = asyncio.create_task(speak(question))
            async with asyncio.timeout(60):
                while True:
                    try:
                        wait = (
                            25
                            if not output_bytes or (interruption_sent and not after_interrupt)
                            else 3
                        )
                        event = json.loads(await asyncio.wait_for(control.recv(), timeout=wait))
                    except TimeoutError:
                        break
                    command = event.get("command")
                    if command == "interrupt" and interruption_sent:
                        interrupted = True
                    elif command == "resume_audio" and interrupted:
                        resumed = True
                    elif command == "sendaudio":
                        size = len(base64.b64decode(event["audiochunk"]))
                        output_bytes += size
                        if resumed:
                            after_interrupt += size
                        if interruption and not interruption_sent:
                            sending.cancel()
                            await asyncio.gather(sending, return_exceptions=True)
                            interruption_sent = True
                            sending = asyncio.create_task(speak(interruption))
            await sending
    finally:
        if sending and not sending.done():
            sending.cancel()
            await asyncio.gather(sending, return_exceptions=True)
        server.should_exit = True
        with suppress(TimeoutError):
            await asyncio.wait_for(serving, timeout=15)
        sock.close()
        directory.cleanup()
    passed = bool(output_bytes and evidence.transcripts and evidence.answers)
    if interruption:
        passed = passed and interrupted and resumed and after_interrupt > 0
    return {
        "test": "real-providers-synthetic-meeting",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "live_meeting": False,
        "pipecat": "1.14.0",
        "llm_model": os.getenv("LLM_MODEL", "gemini-3.5-flash-lite"),
        "user_transcripts": evidence.transcripts,
        "assistant_text": "".join(evidence.answers),
        "output_audio_seconds": round(output_bytes / 96000, 2),
        "spoken_interruption_tested": bool(interruption),
        "interrupted": interrupted,
        "resumed": resumed,
        "audio_after_interrupt_seconds": round(after_interrupt / 96000, 2),
        "passed": passed,
    }


def main():
    load_dotenv()
    logger.remove()
    logger.add(sys.stderr, level="ERROR")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", type=Path, help="48 kHz mono PCM16 WAV of a spoken question")
    parser.add_argument(
        "--interrupt-with", type=Path, help="A second question to speak during the reply"
    )
    parser.add_argument("--report", type=Path, help="Save sanitized JSON evidence locally")
    args = parser.parse_args()
    report = asyncio.run(check(args))
    result = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(result)
    print(result, end="")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
