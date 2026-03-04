#!/usr/bin/env python3
"""Skill Importer CLI

Import skills from various platforms (Coze, Dify, GPT Store, Hugging Face).

Usage:
    python -m scripts.import_skills --platform coze --api-key YOUR_KEY
    python -m scripts.import_skills --platform all --limit 50
    python -m scripts.import_skills --list
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skillpilot.core.importers.registry import load_all_importers, get_importer_config_help
from skillpilot.core.importers import list_importers, get_importer
from skillpilot.core.services.skill import skill_service
from skillpilot.db.seekdb import seekdb_client


def print_importers():
    """Print all available importers"""
    print("\n=== Available Skill Importers ===\n")
    for importer in list_importers():
        config_req = "Yes" if importer["requires_config"] else "No"
        print(f"  {importer['display_name']} ({importer['platform']})")
        print(f"    Requires config: {config_req}")
        print(f"    Status: {importer['status']}")
        print()


async def run_import(
    platform: str,
    limit: int = 100,
    config: dict = None,
    developer_id: str = "system",
):
    """Run skill import for a platform"""
    # Load all importers
    load_all_importers()

    # Get specific importer
    importer = get_importer(platform)
    if not importer:
        print(f"Error: Importer for '{platform}' not found")
        return

    print(f"\n=== Importing from {importer.display_name} ===\n")

    # Configure if needed
    if config:
        importer.configure(**config)

    # Validate configuration
    if not await importer.validate_config():
        print(f"Error: {importer.display_name} requires configuration")
        print(get_importer_config_help(platform))
        return

    # Connect to database
    print("Connecting to database...")
    seekdb_client.connect()

    try:
        # Run import
        summary = await importer.import_skills(
            skill_service=skill_service,
            limit=limit,
            developer_id=developer_id,
        )

        # Print results
        print("\n=== Import Summary ===")
        print(f"  Platform: {importer.display_name}")
        print(f"  Total: {summary.total}")
        print(f"  Success: {summary.success}")
        print(f"  Failed: {summary.failed}")
        print(f"  Skipped: {summary.skipped}")

        if summary.errors:
            print(f"\n  Errors ({len(summary.errors)}):")
            for error in summary.errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
            if len(summary.errors) > 5:
                print(f"    ... and {len(summary.errors) - 5} more")

    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        seekdb_client.close()


async def import_all_platforms(limit: int = 50, config_overrides: dict = None):
    """Import from all available platforms"""
    load_all_importers()

    print("\n=== Importing Skills from All Platforms ===\n")

    # Connect to database
    print("Connecting to database...")
    seekdb_client.connect()

    try:
        for importer in get_importer():
            # Skip importers that require config but don't have it
            if importer.requires_config:
                config = config_overrides.get(importer.platform, {}) if config_overrides else {}
                if not config:
                    print(f"Skipping {importer.display_name} (requires configuration)")
                    continue
                importer.configure(**config)

            summary = await importer.import_skills(
                skill_service=skill_service,
                limit=limit,
                developer_id="system",
            )

            print(f"\n{importer.display_name}: {summary.success}/{summary.total} imported")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        seekdb_client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import AI skills from various platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available importers
  %(prog)s --list

  # Import from Coze
  %(prog)s --platform coze --api-key YOUR_COZE_KEY

  # Import from Dify with specific app IDs
  %(prog)s --platform dify --api-key YOUR_DIFY_KEY --app-ids app1,app2

  # Import from Hugging Face (no config needed)
  %(prog)s --platform huggingface --limit 50

  # Import from all platforms
  %(prog)s --all --limit 25
        """,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available importers",
    )

    parser.add_argument(
        "--platform",
        "-p",
        type=str,
        help="Platform to import from (coze, dify, gptstore, huggingface)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Import from all available platforms",
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum number of skills to import per platform",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for the platform",
    )

    parser.add_argument(
        "--api-base",
        type=str,
        help="API base URL (for Dify)",
    )

    parser.add_argument(
        "--workspace-id",
        type=str,
        help="Workspace ID (for Coze/Dify)",
    )

    parser.add_argument(
        "--app-ids",
        type=str,
        help="Comma-separated app IDs (for Dify)",
    )

    parser.add_argument(
        "--developer-id",
        type=str,
        default="system",
        help="Developer ID to assign to imported skills",
    )

    parser.add_argument(
        "--help-config",
        type=str,
        help="Show configuration help for a platform",
    )

    args = parser.parse_args()

    # List importers
    if args.list:
        print_importers()
        return

    # Show config help
    if args.help_config:
        load_all_importers()
        print(get_importer_config_help(args.help_config))
        return

    # Import from all platforms
    if args.all:
        config_overrides = {}
        if args.platform and args.api_key:
            config_overrides[args.platform] = {
                "api_key": args.api_key,
            }
            if args.api_base:
                config_overrides[args.platform]["api_base"] = args.api_base
            if args.workspace_id:
                config_overrides[args.platform]["workspace_id"] = args.workspace_id

        asyncio.run(import_all_platforms(limit=args.limit, config_overrides=config_overrides))
        return

    # Import from specific platform
    if args.platform:
        config = {}
        if args.api_key:
            config["api_key"] = args.api_key
        if args.api_base:
            config["api_base"] = args.api_base
        if args.workspace_id:
            config["workspace_id"] = args.workspace_id
        if args.app_ids:
            config["app_ids"] = [x.strip() for x in args.app_ids.split(",")]

        asyncio.run(
            run_import(
                platform=args.platform,
                limit=args.limit,
                config=config,
                developer_id=args.developer_id,
            )
        )
        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
