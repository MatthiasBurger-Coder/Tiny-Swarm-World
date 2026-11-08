"""Console consent without blocking the event loop or executor shutdown."""
from __future__ import annotations

import asyncio
import threading


async def request_console_consent(*, capability: str = "Incus") -> bool:
    loop = asyncio.get_running_loop()
    answer: asyncio.Future[bool] = loop.create_future()

    def deliver(value: bool, error: BaseException | None) -> None:
        if answer.done():
            return
        if error is None:
            answer.set_result(value)
        else:
            answer.set_exception(error)

    def read_answer() -> None:
        value = False
        error: BaseException | None = None
        try:
            value = input(f"Apply exactly this {capability} stage? Type 'yes' to continue: ") == "yes"
        except EOFError:
            pass
        except BaseException as failure:
            error = failure
        try:
            loop.call_soon_threadsafe(deliver, value, error)
        except RuntimeError:
            # Cancellation may close the loop before an unanswered prompt returns.
            pass

    # Never join an unanswered console prompt during cancellation or process exit.
    # Only the awaiting orchestration can approve or perform a mutation.
    threading.Thread(target=read_answer, name="incus-consent", daemon=True).start()
    return await answer
