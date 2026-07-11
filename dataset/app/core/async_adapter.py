import asyncio
from typing import Callable, Any

class AsyncExecutionAdapter:
    """
    Adapter for executing blocking CPU or I/O bound tasks asynchronously in thread pools
    to prevent event loop starvation.
    """

    @staticmethod
    async def run(func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Executes a blocking function in a separate thread using the default event loop executor.
        """
        return await asyncio.to_thread(func, *args, **kwargs)
