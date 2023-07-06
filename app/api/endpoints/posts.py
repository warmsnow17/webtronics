from typing import List

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app.schemas.schemas import PostCreate, Post, User
from app.models.database import get_db
from app.models.posts import Post as DBPost
from app.services.auth import get_current_user
from app.models.likes import Like as DBLike
from app.schemas.schemas import Like

router = APIRouter()


@router.post("/posts/", response_model=Post)
def create_post(post: PostCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """
    Создать новый пост

    - **title**: Заголовок поста
    - **content**: Содержание поста
    """
    db_post = DBPost(**post.dict(), user_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.put("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """
    Обновить существующий пост

    - **post_id**: ID поста для обновления
    - **title**: Новый заголовок поста
    - **content**: Новое содержание поста
    """
    db_post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if db_post is None or db_post.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.title = post.title  # type: ignore
    db_post.content = post.content  # type: ignore
    db.commit()
    db.refresh(db_post)
    return db_post


@router.delete("/posts/{post_id}", response_model=Post)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Удалить существующий пост

    - **post_id**: ID поста для удаления
    """
    db_post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if db_post is None or db_post.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(db_post)
    db.commit()
    return db_post


@router.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получить информацию о посте

    - **post_id**: ID поста
    """
    db_post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if db_post is None or db_post.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.get("/posts/", response_model=List[Post])
def get_posts(db: Session = Depends(get_db)):
    """
    Получить список всех постов на сайте
    """
    db_posts = db.query(DBPost).all()
    return db_posts


@router.post("/posts/{post_id}/like", response_model=Like)
def like_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Поставить лайк на указанный пост.

    - **post_id**: ID поста, который нужно лайкнуть.
    """
    db_post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if db_post is None or db_post.user_id == current_user.id:
        raise HTTPException(status_code=404, detail="Post not found or it's your own post")
    db_like = DBLike(user_id=current_user.id, post_id=post_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


@router.delete("/posts/{post_id}/unlike", response_model=Like)
def unlike_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Убрать лайк с указанного поста.

    - **post_id**: ID поста, с которого нужно убрать лайк.
    """
    db_like = db.query(DBLike).filter(DBLike.post_id == post_id, DBLike.user_id == current_user.id).first()
    if db_like is None:
        raise HTTPException(status_code=404, detail="Like not found")
    db.delete(db_like)
    db.commit()
    return db_like

