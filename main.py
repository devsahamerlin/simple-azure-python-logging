@app.get("/health")
async def health_check():
    """Health check endpoint"""
    api_logger.info("Health check endpoint accessed")
    return {
        "status": "healthy", 
        "service": "fastapi-demo",
        "environment": "azure-app-service" if os.environ.get("WEBSITE_SITE_NAME") else "local",
        "insights_configured": bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))
    }

@app.get("/app-info")
async def app_info():
    """Get information about the Azure App Service environment"""
    api_logger.info("App info endpoint accessed")
    
    app_info = {
        "app_name": os.environ.get("WEBSITE_SITE_NAME", "local"),
        "resource_group": os.environ.get("WEBSITE_RESOURCE_GROUP", "N/A"),
        "subscription_id": os.environ.get("WEBSITE_OWNER_NAME", "N/A"),
        "region": os.environ.get("WEBSITE_SITE_REGION", "N/A"),
        "instance_id": os.environ.get("WEBSITE_INSTANCE_ID", "N/A"),
        "hostname": os.environ.get("WEBSITE_HOSTNAME", "localhost"),
        "port": os.environ.get("PORT", "8000"),
        "insights_enabled": bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")),
        "python_version": os.environ.get("PYTHON_VERSION", "unknown")
    }
    
    business_logger.info(f"App running on: {app_info['hostname']} in region: {app_info['region']}")
    
    return app_info# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License in the project root for
# license information.
# --------------------------------------------------------------------------

from logging import INFO, Formatter, getLogger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

from azure.monitor.opentelemetry import configure_azure_monitor

# Configure Azure Monitor
# For Azure App Service, the connection string is typically set via environment variable
connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

if connection_string:
    configure_azure_monitor(
        connection_string=connection_string,
        # Set logger_name to the name of the logger you want to capture logging telemetry with
        # This is imperative so you do not collect logging telemetry from the SDK itself.
        logger_name="fastapi-demo",
        # You can specify the logging format of your collected logs by passing in a logging.Formatter
        logging_formatter=Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.info("Azure Application Insights configured successfully")
else:
    logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not found - Azure monitoring disabled")

# Set up loggers
logger = getLogger("fastapi-demo")
logger.setLevel(INFO)

# Child logger for API operations
api_logger = getLogger("fastapi-demo.api")
api_logger.setLevel(INFO)

# Child logger for business logic
business_logger = getLogger("fastapi-demo.business")
business_logger.setLevel(INFO)

# Logger that won't be tracked
untracked_logger = getLogger("untracked-logger")
untracked_logger.setLevel(INFO)

# FastAPI app
app = FastAPI(
    title="Azure Application Insights Demo",
    description="A simple FastAPI app to test Azure Application Insights logging",
    version="1.0.0"
)

# Pydantic models
class LogMessage(BaseModel):
    message: str
    level: str = "info"

class UserData(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting up")
    api_logger.info("API routes initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application shutting down")

@app.get("/")
async def root():
    """Root endpoint that logs a simple message"""
    logger.info("Root endpoint accessed")
    return {"message": "Hello World! Check your Azure Application Insights for logs."}

@app.get("/app-info")
async def app_info():
    """Get information about the Azure App Service environment"""
    api_logger.info("App info endpoint accessed")
    
    app_info = {
        "app_name": os.environ.get("WEBSITE_SITE_NAME", "local"),
        "resource_group": os.environ.get("WEBSITE_RESOURCE_GROUP", "N/A"),
        "subscription_id": os.environ.get("WEBSITE_OWNER_NAME", "N/A"),
        "region": os.environ.get("WEBSITE_SITE_REGION", "N/A"),
        "instance_id": os.environ.get("WEBSITE_INSTANCE_ID", "N/A"),
        "hostname": os.environ.get("WEBSITE_HOSTNAME", "localhost"),
        "port": os.environ.get("PORT", "8000"),
        "insights_enabled": bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")),
        "python_version": os.environ.get("PYTHON_VERSION", "unknown")
    }
    
    business_logger.info(f"App running on: {app_info['hostname']} in region: {app_info['region']}")
    
    return app_info

@app.post("/log")
async def create_log(log_data: LogMessage):
    """Endpoint to create custom log messages"""
    message = log_data.message
    level = log_data.level.lower()
    
    api_logger.info(f"Log endpoint accessed with level: {level}")
    
    if level == "info":
        logger.info(f"Custom info log: {message}")
        business_logger.info(f"Business logic - info: {message}")
    elif level == "warning":
        logger.warning(f"Custom warning log: {message}")
        business_logger.warning(f"Business logic - warning: {message}")
    elif level == "error":
        logger.error(f"Custom error log: {message}")
        business_logger.error(f"Business logic - error: {message}")
    else:
        api_logger.warning(f"Invalid log level requested: {level}")
        raise HTTPException(status_code=400, detail="Invalid log level. Use 'info', 'warning', or 'error'")
    
    return {"status": "logged", "message": message, "level": level}

@app.post("/user")
async def create_user(user: UserData):
    """Endpoint to create a user and demonstrate structured logging"""
    api_logger.info(f"User creation endpoint accessed for user: {user.name}")
    
    try:
        # Simulate business logic
        business_logger.info(f"Processing user creation for: {user.name} ({user.email})")
        
        if user.age and user.age < 0:
            business_logger.error(f"Invalid age provided for user {user.name}: {user.age}")
            raise HTTPException(status_code=400, detail="Age cannot be negative")
        
        # Simulate successful user creation
        business_logger.info(f"User successfully created: {user.name}")
        
        return {
            "status": "success", 
            "user": user.dict(),
            "message": f"User {user.name} created successfully"
        }
    
    except Exception as e:
        business_logger.error(f"Failed to create user {user.name}: {str(e)}")
        raise

@app.get("/error-demo")
async def error_demo():
    """Endpoint to demonstrate error logging"""
    api_logger.warning("Error demo endpoint accessed - this will generate an error")
    
    try:
        # Intentionally cause an error
        result = 1 / 0
    except ZeroDivisionError as e:
        business_logger.error(f"Intentional error for demo purposes: {str(e)}")
        raise HTTPException(status_code=500, detail="Demo error: Division by zero")

@app.get("/test-untracked")
async def test_untracked_logs():
    """Endpoint to test untracked logger (these won't appear in Azure Application Insights)"""
    api_logger.info("Testing untracked logger endpoint")
    
    # These logs won't be sent to Azure Application Insights
    untracked_logger.info("This info log won't be tracked")
    untracked_logger.warning("This warning log won't be tracked")
    untracked_logger.error("This error log won't be tracked")
    
    return {
        "message": "Untracked logs generated (check console vs Azure Application Insights)",
        "note": "The untracked logs should only appear in console, not in Azure Application Insights"
    }

@app.get("/log-all-levels")
async def log_all_levels():
    """Endpoint to generate logs at all levels for testing"""
    api_logger.info("Generating logs at all levels")
    
    logger.info("Main logger - info message")
    logger.warning("Main logger - warning message")
    logger.error("Main logger - error message")
    
    api_logger.info("API logger - info message")
    api_logger.warning("API logger - warning message")
    api_logger.error("API logger - error message")
    
    business_logger.info("Business logger - info message")
    business_logger.warning("Business logger - warning message")
    business_logger.error("Business logger - error message")
    
    return {
        "message": "All log levels generated",
        "loggers_used": ["fastapi-demo", "fastapi-demo.api", "fastapi-demo.business"]
    }

# For Azure App Service, we need to handle both local and production environments
import os

# Get port from environment variable for Azure App Service
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    logger.info("Starting FastAPI application with Azure Application Insights")
    # For production on Azure App Service, disable reload and adjust settings
    is_production = os.environ.get("WEBSITE_SITE_NAME") is not None
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,  # Disable reload in production
        log_level="info",
        access_log=True
    )