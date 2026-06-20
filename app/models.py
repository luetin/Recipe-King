from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="created_by")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    servings: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_import_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    created_by: Mapped["User"] = relationship(back_populates="recipes")
    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="Ingredient.order"
    )
    steps: Mapped[list["Step"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="Step.order"
    )
    tags: Mapped[list["Tag"]] = relationship(secondary=recipe_tags, back_populates="recipes")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    servings_log: Mapped[list["ServingLog"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_text: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")


class Step(Base):
    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="steps")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(secondary=recipe_tags, back_populates="tags")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("recipe_id", "user_id", name="uq_rating_recipe_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="ratings")
    user: Mapped["User"] = relationship()


class ServingLog(Base):
    __tablename__ = "serving_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    served_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="servings_log")
    user: Mapped["User"] = relationship()
