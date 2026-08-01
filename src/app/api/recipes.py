"""Reusable generation recipes for frequent content workflows."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.api.projects import _owner, _store
from app.dependencies import get_optional_user
from app.models.project import (
    ProjectCreate,
    ProjectResponse,
    RecipeCreate,
    RecipeProjectCreate,
    RecipeResponse,
    RecipeUpdate,
)

if TYPE_CHECKING:
    from app.models.auth import UserResponse

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    payload: RecipeCreate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> RecipeResponse:
    return _store().create_recipe(_owner(user, x_workspace_id), payload)


@router.get("", response_model=list[RecipeResponse])
async def list_recipes(
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> list[RecipeResponse]:
    return _store().list_recipes(_owner(user, x_workspace_id))


@router.patch("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    payload: RecipeUpdate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> RecipeResponse:
    try:
        return _store().update_recipe(_owner(user, x_workspace_id), recipe_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> Response:
    try:
        _store().delete_recipe(_owner(user, x_workspace_id), recipe_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{recipe_id}/projects", response_model=ProjectResponse, status_code=201)
async def create_project_from_recipe(
    recipe_id: str,
    payload: RecipeProjectCreate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    owner = _owner(user, x_workspace_id)
    store = _store()
    try:
        recipe = store.get_recipe(owner, recipe_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Recipe not found") from None
    return store.create(
        owner,
        ProjectCreate(
            title=payload.title,
            body=payload.body,
            source_format=payload.source_format,
            target_formats=recipe.target_formats,
            brand_voice=recipe.brand_voice,
            custom_instructions=recipe.custom_instructions,
        ),
    )
