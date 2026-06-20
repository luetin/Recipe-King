from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Collection, Recipe


def list_collections(db: Session, user_id: int) -> list[Collection]:
    return (
        db.query(Collection)
        .filter(Collection.user_id == user_id)
        .order_by(Collection.name.asc())
        .all()
    )


def get_collection(db: Session, collection_id: int) -> Collection | None:
    return (
        db.query(Collection)
        .options(joinedload(Collection.recipes).joinedload(Recipe.tags))
        .filter(Collection.id == collection_id)
        .first()
    )


def create_collection(db: Session, user_id: int, name: str, description: str | None) -> Collection:
    c = Collection(
        name=name.strip(),
        description=description or None,
        user_id=user_id,
        created_at=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def delete_collection(db: Session, collection: Collection) -> None:
    db.delete(collection)
    db.commit()


def add_recipe(db: Session, collection: Collection, recipe: Recipe) -> None:
    if recipe not in collection.recipes:
        collection.recipes.append(recipe)
        db.commit()


def remove_recipe(db: Session, collection: Collection, recipe: Recipe) -> None:
    collection.recipes = [r for r in collection.recipes if r.id != recipe.id]
    db.commit()
