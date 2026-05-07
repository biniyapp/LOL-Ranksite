from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database, riot_api
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/rankings", response_model=List[schemas.User])
def get_rankings(db: Session = Depends(get_db)):
    # Get all users and sort by score descending
    return db.query(models.User).order_by(models.User.score.desc()).all()

@app.post("/users", response_model=schemas.User)
def create_or_update_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Fetch score from Riot API
    score = riot_api.get_summoner_lp(user.nickname, user.tag)

    # Check if user already exists
    db_user = db.query(models.User).filter(
        models.User.nickname == user.nickname, 
        models.User.tag == user.tag
    ).first()
    
    if db_user:
        # Update existing user score
        db_user.score = score
        db.commit()
        db.refresh(db_user)
        return db_user
    else:
        # Create new user
        new_user = models.User(nickname=user.nickname, tag=user.tag, score=score)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
