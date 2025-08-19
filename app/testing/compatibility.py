"""
TestClient Compatibility Fix

This module provides a fixed TestClient that works around the compatibility issue
between Starlette TestClient and newer versions of HTTPX where the TestClient 
constructor incorrectly passes 'app' parameter to the parent httpx.Client class.

The issue occurs in Starlette's TestClient.__init__ method when it calls:
    super().__init__(app=self.app, ...)

But httpx.Client.__init__ doesn't accept an 'app' parameter, causing:
    TypeError: Client.__init__() got an unexpected keyword argument 'app'
"""

import typing
import httpx
import anyio
from contextlib import contextmanager
from starlette.testclient import (
    _TestClientTransport, 
    _AsyncBackend, 
    _is_asgi3, 
    _WrapASGI2,
    ASGI2App,
    ASGI3App
)


class FixedTestClient(httpx.Client):
    """
    A fixed version of Starlette's TestClient that doesn't pass the 'app' 
    parameter to the parent httpx.Client constructor.
    
    This is a drop-in replacement for FastAPI's TestClient.
    """
    
    def __init__(
        self,
        app,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        cookies=None,
        headers: typing.Dict[str, str] = None,
    ) -> None:
        # Initialize the async backend
        self.async_backend = _AsyncBackend(
            backend=backend, backend_options=backend_options or {}
        )
        
        # Handle ASGI app versioning
        if _is_asgi3(app):
            app = typing.cast(ASGI3App, app)
            asgi_app = app
        else:
            app = typing.cast(ASGI2App, app)
            asgi_app = _WrapASGI2(app)
            
        self.app = asgi_app
        self.app_state: typing.Dict[str, typing.Any] = {}
        
        # Create the transport
        transport = _TestClientTransport(
            self.app,
            portal_factory=self._portal_factory,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            app_state=self.app_state,
        )
        
        # Set up headers
        if headers is None:
            headers = {}
        headers.setdefault("user-agent", "testclient")
        
        # Call parent constructor WITHOUT the 'app' parameter
        super().__init__(
            base_url=base_url,
            headers=headers,
            transport=transport,
            follow_redirects=True,
            cookies=cookies,
        )
    
    @contextmanager
    def _portal_factory(self) -> typing.Generator[anyio.abc.BlockingPortal, None, None]:
        """Create a portal for async operations"""
        with anyio.from_thread.start_blocking_portal(
            **self.async_backend
        ) as portal:
            yield portal


# For backwards compatibility, provide the same interface as FastAPI TestClient
TestClient = FixedTestClient
