from . import journal, tasks


def print_today():
    todays = tasks.list_today()
    overdue = tasks.list_overdue()

    print("Today's tasks:")
    if todays:
        for t in todays:
            print(f"  {tasks.format_task_line(t)}")
    else:
        print("  (none)")

    if overdue:
        print("\nOverdue:")
        for t in overdue:
            print(f"  {tasks.format_task_line(t)}")

    entries = journal.list_today()
    print("\nJournal:")
    if entries:
        for line in entries:
            print(f"  {line}")
    else:
        print("  (none)")
