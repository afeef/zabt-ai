# Research: Generic Audit Hooks for BaseService

## Decision: Service-Layer Hooks

I have chosen to implement audit hooks at the service layer (`BaseService`) rather than the database layer (SQLAlchemy event listeners).

### Rationale
- **Context Awareness**: Service-layer hooks have easy access to the `owner_id` and action context (e.g., "transcribing") which are harder to reconstruct at the raw SQL level.
- **Simplicity**: No need to manage complex SQLAlchemy ORM event registrations.
- **Portability**: The logic is tied to our business services, not the specific database driver or ORM implementation details.

### Alternatives Considered

#### SQLAlchemy Event Listeners (`before_insert`, `after_update`)
- **Pros**: Catches all changes, even those outside services.
- **Cons**: "Invisible" side effects, harder to pass high-level context (like "meeting_id" if it's not part of the primary object being saved).

#### Decorators
- **Pros**: Very clean syntax.
- **Cons**: Harder to implement with generics and inheritance in a way that allows easy overriding in sub-classes without breaking the decorator chain.

## Performance Impact
- **Decision**: Use standard method calls for hooks.
- **Rationale**: Python's method invocation overhead is negligible ($< 1\mu s$) compared to database I/O. Using `**kwargs` allows for flexible data passing without manual attribute mapping.
