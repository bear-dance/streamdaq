from fastapi import APIRouter


def create_router() -> APIRouter:
    """Create the root router."""
    router = APIRouter(tags=["root"])

    @router.get("/")
    async def root():
        return {"message": "API is up and running. Visit /docs for the documentation."}

    return router
