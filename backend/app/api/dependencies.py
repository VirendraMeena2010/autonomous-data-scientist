from fastapi import Request

from app.services.queue import AnalysisQueue
from app.services.storage import StorageService


def get_storage(request: Request) -> StorageService:
    return request.app.state.storage


def get_analysis_queue(request: Request) -> AnalysisQueue:
    return request.app.state.analysis_queue
