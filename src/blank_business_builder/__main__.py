"""
Better Business Builder - Entry point for module execution
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "blank_business_builder.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
