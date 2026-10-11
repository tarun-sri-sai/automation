PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS todo_task_lists (
  id TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch('now'))
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_tasks (
  id TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch('now'))
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_task_list_tasks (
  todo_task_list_id TEXT NOT NULL,
  todo_task_id TEXT NOT NULL,
  PRIMARY KEY (todo_task_list_id, todo_task_id),
  FOREIGN KEY (todo_task_list_id) REFERENCES todo_task_lists(id)
  FOREIGN KEY (todo_task_id) REFERENCES todo_tasks(id)
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_file_attachments (
  id TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch('now'))
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_task_file_attachments (
  todo_task_id TEXT NOT NULL,
  task_file_attachment_id TEXT NOT NULL,
  PRIMARY KEY (todo_task_id, task_file_attachment_id),
  FOREIGN KEY (todo_task_id) REFERENCES todo_tasks(id)
  FOREIGN KEY (task_file_attachment_id) REFERENCES todo_file_attachments(id)
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_checklist_items (
  id TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch('now'))
) STRICT, WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS todo_task_checklist_items (
  todo_task_id TEXT NOT NULL,
  task_checklist_item_id TEXT NOT NULL,
  PRIMARY KEY (todo_task_id, task_checklist_item_id),
  FOREIGN KEY (todo_task_id) REFERENCES todo_tasks(id)
  FOREIGN KEY (task_checklist_item_id) REFERENCES todo_checklist_items(id)
) STRICT, WITHOUT ROWID;
