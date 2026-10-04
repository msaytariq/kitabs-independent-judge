"""Thin editor endpoints. No provider, timing arithmetic or database logic."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from independent_judge.api.editorial_schemas import CreateEditorialReview,EditorialCommand


def build_editorial_router(service):
    router=APIRouter(prefix='/api/editorial')

    @router.post('',status_code=201)
    def create(request:CreateEditorialReview):
        return service.create(**request.model_dump())

    @router.get('/{review_id}')
    def get(review_id:str):
        return service.get(review_id)

    @router.post('/{review_id}/commands')
    def command(review_id:str,request:EditorialCommand):
        return service.command(review_id,request.model_dump())

    @router.get('/{review_id}/export')
    def export(review_id:str):
        result=service.export(review_id)
        return JSONResponse(result,headers={'Content-Disposition':f'attachment; filename="editorial-{result["state"]["id"]}.json"'})

    return router
