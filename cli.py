"""
CLI entry point.

Examples:
    python cli.py --config config.example.yaml
    python cli.py --config config.example.yaml --max-pages 2 --no-headless
    python cli.py --config config.example.yaml --fresh   # ignore checkpoint
"""

import argparse

from scraper import ScraperConfig, run


def parse_args():
    parser = argparse.ArgumentParser(description="Config-driven directory scraper")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--max-pages", type=int, help="Override max_pages from config")
    parser.add_argument(
        "--no-headless", action="store_true", help="Run with a visible browser window"
    )
    parser.add_argument(
        "--fresh", action="store_true", help="Ignore any existing checkpoint and start over"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = ScraperConfig(args.config)

    if args.max_pages:
        config.max_pages = args.max_pages
    if args.no_headless:
        config.headless = False

    items = run(config, resume=not args.fresh)

    print(f"\nDone. {len(items)} unique items saved to {config.output_file}")


if __name__ == "__main__":
    main()
