"""
Kubernetes Agentic AI - Main Entry Point

True Agentic AI for Kubernetes self-healing.
Uses LLM to diagnose and fix ANY Kubernetes issue automatically.

Usage:
    python main.py              # Run agent (continuous)
    python main.py --diagnose   # Run diagnosis only
    python main.py --docs       # Generate documentation
"""

import sys
from config import print_config


def main():
    """Main entry point."""
    # Print configuration
    print_config()

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--diagnose":
            # Run diagnosis only
            from agent import run_once
            run_once()
            return

        elif arg == "--docs":
            # Generate documentation
            from doc_generator import generate_all_docs
            print("\nGenerating documentation...")
            generate_all_docs()
            print("\nDone!")
            return

        elif arg == "--help":
            print("""
Usage: python main.py [OPTIONS]

Options:
    (none)      Run agent continuously
    --diagnose  Run diagnosis only (no fixes)
    --docs      Generate documentation
    --help      Show this help
            """)
            return

    # Run agent
    from agent import run_agent
    run_agent()


if __name__ == "__main__":
    main()