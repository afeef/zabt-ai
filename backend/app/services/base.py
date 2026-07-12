from typing import List, Optional, TypeVar
from sqlmodel import Session, select, SQLModel
from app.db.engine import engine

T = TypeVar("T", bound=SQLModel)

class BaseService:
    def on_before_action(self, action: str, **kwargs):
        """
        Generic pre-event hook for audit logging.
        Subclasses can override this to implement custom auditing logic.
        """
        print(f"AUDIT [BEFORE]: {action} with context {kwargs}")

    def on_after_action(self, action: str, result: any, **kwargs):
        """
        Generic post-event hook for audit logging.
        Subclasses can override this to implement custom auditing logic.
        """
        print(f"AUDIT [AFTER]: {action} with result {result}")

    def save(self, obj: T) -> T:
        self.on_before_action("save", obj=obj)
        with Session(engine) as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        self.on_after_action("save", result=obj, obj=obj)
        return obj

    def get(self, model: type[T], obj_id: int) -> Optional[T]:
        self.on_before_action("get", model=model, obj_id=obj_id)
        with Session(engine) as session:
            result = session.get(model, obj_id)
        self.on_after_action("get", result=result, model=model, obj_id=obj_id)
        return result

    def get_all(self, model: type[T], owner_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        self.on_before_action("get_all", model=model, owner_id=owner_id, skip=skip, limit=limit)
        with Session(engine) as session:
            statement = select(model).where(model.owner_id == owner_id).offset(skip).limit(limit)
            result = session.exec(statement).all()
        self.on_after_action("get_all", result=result, model=model, owner_id=owner_id, skip=skip, limit=limit)
        return result

    def delete(self, model: type[T], obj_id: int) -> bool:
        self.on_before_action("delete", model=model, obj_id=obj_id)
        with Session(engine) as session:
            obj = session.get(model, obj_id)
            if not obj:
                self.on_after_action("delete", result=False, model=model, obj_id=obj_id)
                return False
            session.delete(obj)
            session.commit()
            self.on_after_action("delete", result=True, model=model, obj_id=obj_id)
            return True

