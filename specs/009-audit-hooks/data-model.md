# Data Model Design: Audit Hooks

This feature does not introduce new database tables. Instead, it defines a new architectural pattern for the `BaseService` class.

## Service Architecture

### BaseService (Generic Class)
- **Generic T**: Bounded by `SQLModel`.
- **Methods**:
    - `save(obj: T)`
    - `get(model: type[T], id)`
    - `get_all(model: type[T], owner_id, skip, limit)`
    - `delete(model: type[T], id)`

### Event Hooks (New)
- `on_before_action(action: str, **kwargs)`: Triggered before any operation.
- `on_after_action(action: str, result: any, **kwargs)`: Triggered after success.

## Relationships
- All application services (`MeetingService`, `StyleService`, etc.) inherit from `BaseService`.
- Inheriting the hooks allows these services to implement logging or side-effects (like clearing cache) without modifying the core CRUD logic.
