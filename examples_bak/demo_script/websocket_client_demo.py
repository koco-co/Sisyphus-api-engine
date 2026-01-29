"""WebSocket Client Demo for Sisyphus API Engine.

This script demonstrates how to connect to the WebSocket server
and receive real-time test execution updates.

Usage:
    python websocket_client_demo.py [--host HOST] [--port PORT]
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

import websockets


async def connect_to_websocket(host: str = "localhost", port: int = 8765):
    """Connect to WebSocket server and receive updates.

    Args:
        host: WebSocket server host
        port: WebSocket server port
    """
    uri = f"ws://{host}:{port}"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to WebSocket server at {uri}")
            print("Waiting for test execution updates...\n")

            # Receive messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print_event(data)
                except json.JSONDecodeError as e:
                    print(f"⚠ Invalid JSON received: {e}")
                except Exception as e:
                    print(f"⚠ Error processing message: {e}")

    except websockets.exceptions.ConnectionClosed:
        print("\n⚠ Connection closed by server")
    except ConnectionRefusedError:
        print(f"\n✗ Connection refused. Make sure the server is running at {uri}")
        print("  Start the server with: sisyphus-api-engine --cases test.yaml --ws-server")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def print_event(data: dict):
    """Pretty print WebSocket event.

    Args:
        data: Event data dictionary
    """
    event_type = data.get("type", "unknown")
    timestamp = data.get("timestamp", "")
    event_data = data.get("data", {})

    # Parse timestamp for display
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = timestamp[:19] if timestamp else "--:--:--"

    # Format output based on event type
    if event_type == "test_start":
        print(f"[{time_str}] 🚀 TEST START")
        print(f"  Name: {event_data.get('test_name', 'N/A')}")
        print(f"  Total Steps: {event_data.get('total_steps', 0)}")
        if event_data.get('description'):
            print(f"  Description: {event_data['description']}")

    elif event_type == "test_complete":
        print(f"\n[{time_str}] 🏁 TEST COMPLETE")
        print(f"  Status: {event_data.get('status', 'N/A').upper()}")
        print(f"  Duration: {event_data.get('duration', 0):.2f}s")
        stats = {
            'total': event_data.get('total_steps', 0),
            'passed': event_data.get('passed_steps', 0),
            'failed': event_data.get('failed_steps', 0),
            'skipped': event_data.get('skipped_steps', 0),
        }
        print(f"  Results: {stats['passed']}✓ {stats['failed']}✗ {stats['skipped']}⊘ / {stats['total']} total")
        pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  Pass Rate: {pass_rate:.1f}%")

    elif event_type == "step_start":
        step_num = event_data.get('step_index', 0) + 1
        total = event_data.get('total_steps', 0)
        step_name = event_data.get('step_name', 'N/A')
        step_type = event_data.get('step_type', 'N/A')
        print(f"[{time_str}] ▶ Step {step_num}/{total}: {step_name} ({step_type})")

    elif event_type == "step_complete":
        step_name = event_data.get('step_name', 'N/A')
        status = event_data.get('status', 'N/A')
        duration = event_data.get('duration', 0)
        retry_count = event_data.get('retry_count', 0)
        has_error = event_data.get('has_error', False)

        status_icon = {"success": "✓", "failure": "✗", "skipped": "⊘"}.get(status, "?")
        retry_info = f" (retry #{retry_count})" if retry_count > 0 else ""
        error_info = " ⚠ ERROR" if has_error else ""

        print(f"  [{time_str}] {status_icon} {step_name} - {status}{retry_info}{error_info} ({duration:.3f}s)")

    elif event_type == "progress":
        current = event_data.get('current_step', 0)
        total = event_data.get('total_steps', 0)
        percentage = event_data.get('percentage', 0)
        passed = event_data.get('passed_steps', 0)
        failed = event_data.get('failed_steps', 0)
        estimated = event_data.get('estimated_remaining')

        # Create progress bar
        bar_width = 30
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        est_time = f" (~{estimated:.0f}s remaining)" if estimated else ""

        print(f"[{time_str}] 📊 Progress: [{bar}] {percentage:.0f}% - {passed}✓ {failed}✗{est_time}")

    elif event_type == "log":
        level = event_data.get('level', 'info')
        message = event_data.get('message', '')

        level_icons = {
            'debug': '🔍',
            'info': 'ℹ',
            'warning': '⚠',
            'error': '❌',
            'critical': '🚨',
        }
        icon = level_icons.get(level, '•')
        print(f"[{time_str}] {icon} [{level.upper()}] {message}")

    elif event_type == "error":
        error_type = event_data.get('error_type', 'N/A')
        error_category = event_data.get('error_category', 'N/A')
        message = event_data.get('message', '')
        step_name = event_data.get('step_name', '')

        print(f"[{time_str}] ❌ ERROR: {message}")
        print(f"  Type: {error_type}")
        print(f"  Category: {error_category}")
        if step_name:
            print(f"  Step: {step_name}")

    elif event_type == "variable_update":
        var_name = event_data.get('variable_name', 'N/A')
        var_value = event_data.get('variable_value', 'N/A')
        source = event_data.get('source', 'extracted')

        print(f"[{time_str}] 🔖 Variable: ${var_name} = {var_value} ({source})")

    else:
        print(f"[{time_str}] Unknown event type: {event_type}")
        print(f"  Data: {json.dumps(data, indent=2)[:200]}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WebSocket Client Demo for Sisyphus API Engine"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="WebSocket server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="WebSocket server port (default: 8765)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(connect_to_websocket(args.host, args.port))
    except KeyboardInterrupt:
        print("\n\nClient disconnected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
