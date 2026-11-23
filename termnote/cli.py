import argparse
import sys

from . import domains, journal, tasks, today_view
from .storage import ensure_storage


def build_parser():
    parser = argparse.ArgumentParser(prog="note")
    entity = parser.add_subparsers(dest="entity")

    domain_p = entity.add_parser("domain")
    domain_action = domain_p.add_subparsers(dest="action")
    d_add = domain_action.add_parser("add")
    d_add.add_argument("name")
    domain_action.add_parser("list")

    task_p = entity.add_parser("task")
    task_action = task_p.add_subparsers(dest="action")
    t_add = task_action.add_parser("add")
    t_add.add_argument("text")
    t_add.add_argument("-d", "--domain", required=True)
    t_add.add_argument("-t", "--tag", action="append", default=[])
    t_add.add_argument("--date", default="today")
    t_list = task_action.add_parser("list")
    t_list.add_argument("filter", nargs="?", default="today", choices=["today"])
    t_done = task_action.add_parser("done")
    t_done.add_argument("id", type=int)

    journal_p = entity.add_parser("journal")
    journal_action = journal_p.add_subparsers(dest="action")
    j_add = journal_action.add_parser("add")
    j_add.add_argument("text")
    j_list = journal_action.add_parser("list")
    j_list.add_argument("filter", nargs="?", default="today", choices=["today"])

    entity.add_parser("today")
    entity.add_parser("help")

    return parser


def main(argv=None):
    ensure_storage()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.entity == "domain":
            if args.action == "add":
                result = domains.add_domain(args.name)
                print(f"Domain '{args.name}' added. Domains: {', '.join(result)}")
            elif args.action == "list":
                for d in domains.list_domains():
                    print(d)
            else:
                parser.parse_args(["domain", "--help"])

        elif args.entity == "task":
            if args.action == "add":
                t = tasks.add_task(args.text, args.domain, args.tag, args.date)
                print(f"Task added: {tasks.format_task_line(t)}")
            elif args.action == "list":
                for t in tasks.list_today():
                    print(tasks.format_task_line(t))
            elif args.action == "done":
                t = tasks.mark_done(args.id)
                print(f"Done: {tasks.format_task_line(t)}")
            else:
                parser.parse_args(["task", "--help"])

        elif args.entity == "journal":
            if args.action == "add":
                journal.add_entry(args.text)
                print("Journal entry added.")
            elif args.action == "list":
                for line in journal.list_today():
                    print(line)
            else:
                parser.parse_args(["journal", "--help"])

        elif args.entity == "today":
            today_view.print_today()

        else:
            parser.print_help()

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
