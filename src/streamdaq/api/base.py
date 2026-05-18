import uvicorn
from fastapi import FastAPI

from streamdaq.api.routers import root as root_router_module
from streamdaq.api.routers import session as session_router_module
from streamdaq.api.routers import tasks as tasks_router_module
from streamdaq.sessions.base import Session


class API:
    def __init__(
        self,
        *,
        title: str = "StreamDaQ API",
        host: str = "127.0.0.1",
        port: int = 8000,
        log_level: str = "info",
        reload: bool = False,
        session: Session,
    ) -> None:
        self.host = host
        self.port = port
        self.log_level = log_level
        self.reload = reload
        self.session = session
        self.app = FastAPI(title=title)
        self._register_routes()

    def _register_routes(self) -> None:
        # Register root router
        root_router = root_router_module.create_router()
        self.app.include_router(root_router)

        # Register tasks router
        tasks_router = tasks_router_module.create_router(self.session)
        self.app.include_router(tasks_router)

        # Register session router
        session_router = session_router_module.create_router(self.session)
        self.app.include_router(session_router)

    def start(self) -> None:
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level=self.log_level,
            reload=self.reload,
        )
