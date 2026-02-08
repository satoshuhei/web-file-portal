# Decision Log

## 001

### Decision
- Require committing code changes with a descriptive commit message.

### Context
- User requested that code changes be committed with a message describing the changes.

### Alternatives
- Keep commits optional.
- Allow batching multiple changes before committing.

### Consequences
- Ensures a consistent history tied to each change.
- Requires committing more frequently during work.

### Follow-ups
- TBD

## 002

### Decision
- Use a batch sync command to reflect file system changes into the database.

### Context
- The system needs to mirror changes from local shared folders while remaining read-only.
- Real-time watchers are not in scope for the initial setup.

### Alternatives
- Scan on every request without a database index.
- Add a real-time file watcher service.

### Consequences
- Requires running a command or scheduled job to stay in sync.
- Keeps the web app responsive by relying on indexed metadata.

### Follow-ups
- TBD

