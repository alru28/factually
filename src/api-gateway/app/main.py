from fastapi import FastAPI, Request, HTTPException, Response, Depends, Header
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware

import yaml
import httpx
import os

# GLOBAL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
TRANSFORMATION_SERVICE_URL = os.getenv("TRANSFORMATION_SERVICE_URL", "http://transformation-service:8000")
VERIFICATION_SERVICE_URL = os.getenv("VERIFICATION_SERVICE_URL", "http://verification-service:8000")
EXTRACTION_SERVICE_URL = os.getenv("EXTRACTION_SERVICE_URL", "http://extraction-service:8000")
ORCHESTRATOR_SERVICE_URL = os.getenv("ORCHESTRATOR_SERVICE_URL", "http://orchestrator-service:8000")
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")

# GATEWAY HELPER FUNCTIONS
async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is missing")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/validate", headers={"X-API-Key": api_key})

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid API Key")
        
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail="Authentication Service error")

# PROXY
async def proxy_request(request: Request, target_url: str, headers=None):
    method = request.method
    content = await request.body()

    headers = headers or dict(request.headers)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            
            response = await client.request(method, target_url, headers=headers, content=content)
            return Response(content=response.content, status_code=response.status_code, headers=response.headers)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=f"Gateway error: {str(exc)}")

# GATEWAY APP
app = FastAPI(title="Factually API", openapi_url = None)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PROXY ROUTES
@app.api_route("/extraction/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def collection_service_proxy(path: str, request: Request, token_verified: str = Depends(verify_api_key)):
    target_url = f"{EXTRACTION_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def auth_service_proxy(path: str, request: Request):
    target_url = f"{AUTH_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

@app.api_route("/orchestrator/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def exploration_service_proxy(path: str, request: Request, token_verified: str = Depends(verify_api_key)):
    target_url = f"{ORCHESTRATOR_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

@app.api_route("/storage/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def exploration_service_proxy(path: str, request: Request, token_verified: str = Depends(verify_api_key)):
    target_url = f"{STORAGE_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

@app.api_route("/transformation/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def exploration_service_proxy(path: str, request: Request, token_verified: str = Depends(verify_api_key)):
    target_url = f"{TRANSFORMATION_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

@app.api_route("/verification/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def exploration_service_proxy(path: str, request: Request, token_verified: str = Depends(verify_api_key)):
    target_url = f"{VERIFICATION_SERVICE_URL}/{path}".lstrip("/")
    return await proxy_request(request, target_url)

# SWAGGER CUSTOM DOCS
with open("api-doc.yaml", "r") as file:
    openapi_spec = yaml.safe_load(file)

@app.get("/api-doc.yaml", include_in_schema=False)
async def get_openapi_yaml():
    return Response(content=yaml.dump(openapi_spec), media_type="application/yaml")

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return get_swagger_ui_html(openapi_url="/api-doc.yaml", title="Custom API Docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
