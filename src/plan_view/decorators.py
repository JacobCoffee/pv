"""Decorators for command functions."""

import argparse
import sys
from collections.abc import Callable
from functools import wraps
from typing import Concatenate

from plan_view.io import load_plan, resolve_plan_path


def require_plan[**P, R](
    func: Callable[Concatenate[dict, argparse.Namespace, P], R],
) -> Callable[Concatenate[argparse.Namespace, P], R]:
    """Decorator to load plan from args.file and inject it as first argument.

    This eliminates the boilerplate of loading plan, checking for None,
    and asserting for the type checker. The wrapped function receives
    the loaded plan dict as its first positional argument.

    Args:
        func: Command function that takes (plan: dict, args: Namespace, ...) -> R

    Returns:
        Wrapped function that takes (args: Namespace, ...) -> R

    Example::

        @require_plan
        def cmd_add_task(plan: dict, args: argparse.Namespace) -> None:
            phase = find_phase(plan, args.phase)
            ...
    """

    @wraps(func)
    def wrapper(args: argparse.Namespace, /, *inner_args: P.args, **inner_kwargs: P.kwargs) -> R:
        # Resolve the file path from config if not explicitly set
        file_path = resolve_plan_path(args.file)
        # Update args.file so save operations use the resolved path
        args.file = file_path

        # Load the plan
        plan = load_plan(file_path)

        # Exit with error if plan not found
        if plan is None:
            sys.exit(1)

        # Call the original function with plan as first arg
        return func(plan, args, *inner_args, **inner_kwargs)

    return wrapper
