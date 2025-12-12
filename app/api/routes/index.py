from fastapi import APIRouter

router = APIRouter(tags=["index"])

# Note: /voice and /chat routes are now handled by StaticFiles mount in main.py
# This allows proper serving of HTML and all static assets (JS, CSS, images, etc.)
