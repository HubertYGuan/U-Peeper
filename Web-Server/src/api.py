from fastapi import FastAPI, HTTPException, Depends, Response, Request, status
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional
from fastapi.security import HTTPBearer, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
import time
import datetime
from dotenv import load_dotenv
import os
from redis import Redis

app = FastAPI()

@app.get('/')
def root():
    return {'message': 'Cool test json'}