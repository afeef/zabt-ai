from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import json
# In production, use a proper logger (structlog) or database
# For MVP, we print to stdout which Docker captures

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract user ID if available (needs to be after auth middleware, 
        # but Starlette middleware runs before endpoint dependencies. 
        # So we might not have user in request.state yet unless we use a custom AuthMiddleware)
        # For now, we log path, method, IP.
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        log_entry = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else "unknown",
            "duration_ms": round(process_time * 1000, 2)
        }
        
        print(f"AUDIT_LOG: {json.dumps(log_entry)}")
        
        return response
