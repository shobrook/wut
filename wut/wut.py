# Standard library
import os
import argparse
import subprocess

# Third party
from rich.console import Console
import questionary
import pyperclip

# Local
try:
    from wut.utils import (
        get_shell,
        get_terminal_context,
        explain,
        fix,
    )
except ImportError:
    from utils import ( # type: ignore
        get_shell,
        get_terminal_context,
        explain,
        fix,
    )

def main():
    parser = argparse.ArgumentParser(
        description="Understand the output of your latest terminal command."
    )
    parser.add_argument(
        "--query",
        type=str,
        required=False,
        default="",
        help="A specific question about what's on your terminal.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug information.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Propose a fix for the previous command.",
    )
    args = parser.parse_args()
    console = Console()
    debug = lambda text: console.print(f"wut | {text}") if args.debug else None

    # Environment checks without status
    if not os.environ.get("TMUX") and not os.environ.get("STY"):
        console.print(
            "[bold red]wut must be run inside a tmux or screen session.[/bold red]"
        )
        return
    if (
        not os.environ.get("OPENAI_API_KEY", None)
        and not os.environ.get("ANTHROPIC_API_KEY", None)
        and not os.environ.get("OLLAMA_MODEL", None)
    ):
        console.print(
            "[bold red]Please set your OpenAI or Anthropic API key in your environment variables. Or, alternatively, specify an Ollama model name and if necessary an Ollama host.[/bold red]"
        )
        return

    # Only show status during data gathering and LLM processing
    with console.status("[bold green]Trying my best...") as status:
        shell = get_shell()
        terminal_context = get_terminal_context(shell)

        debug(f"Retrieved shell information:\n{shell}")
        debug(f"Retrieved terminal context:\n{terminal_context}")
        debug("Sending request to LLM...")

        if args.fix:
            command, response = fix(terminal_context)
        else:
            response = explain(terminal_context, args.query)
            command = None

        # Clear status before any output
        status.stop()

    # Handle outputs after status is cleared
    console.print(response)
    
    if args.fix and command:
        debug(f"Got command: {command}")
        console.print("\n")
        # First ask what to do, before any action
        choice = questionary.select(
            f"What would you like to do with the command {command}?",
            choices=[
                "Execute",
                "Copy to clipboard",
                "Discard"
            ],
        ).ask()
        
        # Only perform action after user choice
        if choice == "Execute":
            try:
                subprocess.run(command, shell=True)
            except Exception as e:
                console.print(f"[bold red]Error executing command: {e}[/bold red]")
        elif choice == "Copy to clipboard":
            pyperclip.copy(command)
            console.print("[green]Command copied to clipboard![/green]")