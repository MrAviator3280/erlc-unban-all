import requests
import json
import time
import sys
import os

os.system('cls' if os.name == 'nt' else 'clear')

print(" __   __  _______  ______   _______        _______  __   __        _______  _______        __   __  _   ___  _______ ")
print("|  |_|  ||   _   ||      | |       |      |  _    ||  | |  |      |       ||       |      |  |_|  || | |   ||  _    |")
print("|       ||  |_|  ||  _    ||    ___|      | |_|   ||  |_|  |      |____   ||    ___|      |       || |_|   || | |   |")
print("|       ||       || | |   ||   |___       |       ||       |       ____|  ||   | __       |       ||       || |_|   |")
print("|       ||       || |_|   ||    ___|      |  _   | |_     _|      | ______||   ||  | ___  |       ||___    ||___    |")
print("| ||_|| ||   _   ||       ||   |___       | |_|   |  |   |        | |_____ |   |_| ||   | | ||_|| |    |   |    |   |")
print("|_|   |_||__| |__||______| |_______|      |_______|  |___|        |_______||_______||___| |_|   |_|    |___|    |___|")

time.sleep(5)

os.system('cls' if os.name == 'nt' else 'clear')

print("\nLoading", end="")
for _ in range(5):
    time.sleep(0.5)
    print(".", end="", flush=True)
print()

os.system('cls' if os.name == 'nt' else 'clear')

inputkey = input(str("Please input your ER:LC API Key: "))

SERVER_KEY = inputkey


BASE_URL_V1 = "https://api.policeroleplay.community/v1"
BASE_URL_V2 = "https://api.policeroleplay.community/v2"

HEADERS = {
    "server-key": SERVER_KEY,
    "Content-Type": "application/json",
}

BATCH_SIZE            = 1   # IDs per :unban command (THIS IS BROKEN DO NOT USE MORE THAN 1 OR IT WILL NOT WORK!)
FALLBACK_WAIT_SECONDS = 5

time.sleep(1)

if BATCH_SIZE >= 2:
    print("Multiple ID's per command is currently not supported. Please change your batch size to 1.")
    sys.exit(1)
else:
    print("Script OK")
    input("Press ENTER to continue...")
    
def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def progress_bar(current: int, total: int, width: int = 40) -> str:
    if total == 0:
        return "[" + "=" * width + "] 100%"
    filled = int(width * current / total)
    bar    = "=" * filled + "-" * (width - filled)
    pct    = int(100 * current / total)
    return f"[{bar}] {pct}%  ({current}/{total})"


def handle_rate_limit(response) -> bool:
    """
    Reads dynamic X-RateLimit-* headers from the response and sleeps
    if the bucket is exhausted.  Returns True if a 429 was received
    (caller should retry the same request).
    """
    if response.status_code == 429:
        try:
            retry_after = float(response.json().get("retry_after", FALLBACK_WAIT_SECONDS))
        except Exception:
            retry_after = FALLBACK_WAIT_SECONDS
        clear_line()
        print(f"Rate-limited (429). Retrying in {retry_after:.1f}s …")
        time.sleep(retry_after)
        return True  # signal: retry

    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_ts  = response.headers.get("X-RateLimit-Reset")

    if remaining is not None and reset_ts is not None:
        if int(remaining) == 0:
            sleep_for = max(0.0, float(reset_ts) - time.time())
            if sleep_for > 0:
                clear_line()
                print(f"Bucket exhausted. Waiting {sleep_for:.1f}s for reset …")
                time.sleep(sleep_for)

    return False  # no retry needed


def make_request(method: str, url: str, **kwargs):
    """Auto-retrying wrapper that honours dynamic rate-limit headers."""
    while True:
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if not handle_rate_limit(resp):
            return resp

def fetch_banned_ids() -> list[str]:
    print("  Contacting API …", end="", flush=True)
    resp = make_request("GET", f"{BASE_URL_V1}/server/bans")

    clear_line()

    if resp.status_code == 403:
        print("  [ERROR] 403 Forbidden — double-check your SERVER_KEY.")
        sys.exit(1)
    elif resp.status_code != 200:
        print(f"  [ERROR] Unexpected status {resp.status_code}: {resp.text}")
        sys.exit(1)

    ids = list(resp.json().keys())
    return ids


def build_batches(user_ids: list[str]) -> list[dict]:
    batches = []
    for i in range(0, len(user_ids), BATCH_SIZE):
        chunk = user_ids[i : i + BATCH_SIZE]
        batches.append({
            "num": (i // BATCH_SIZE) + 1,
            "ids": ",".join(chunk),
        })
    return batches


def run_unbans(batches: list[dict]):
    total   = len(batches)
    success = 0
    failed  = 0
    errors  = []

    for i, batch in enumerate(batches):
        command = f":unban {batch['ids']}"

        sys.stdout.write(f"\r  {progress_bar(i, total)}  batch {i+1}/{total} …")
        sys.stdout.flush()

        resp = make_request(
            "POST",
            f"{BASE_URL_V2}/server/command",
            json={"command": command},
        )

        if resp.status_code == 200:
            success += 1
        elif resp.status_code == 422:
            failed += 1
            msg = "Server is empty — at least 1 player must be online for :unban to work."
            errors.append(f"Batch {batch['num']}: {msg}")
            clear_line()
            print(f"  [!] {msg}")
            break  # pointless to continue if server is empty
        elif resp.status_code == 400:
            failed += 1
            errors.append(f"Batch {batch['num']}: 400 Bad Request — {resp.text}")
        else:
            failed += 1
            errors.append(f"Batch {batch['num']}: HTTP {resp.status_code} — {resp.text}")

        if i < total - 1:
            reset_ts  = resp.headers.get("X-RateLimit-Reset")
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and reset_ts is not None and int(remaining) <= 1:
                sleep_for = max(0.0, float(reset_ts) - time.time())
            else:
                sleep_for = FALLBACK_WAIT_SECONDS
            time.sleep(sleep_for)

    # Final bar at 100 %
    clear_line()
    sys.stdout.write(f"\r  {progress_bar(total, total)}\n")
    sys.stdout.flush()

    return success, failed, errors

def main():
    os.system("")

    print()
    print("╔══════════════════════════════════════════╗")
    print("║    ER:LC  Mass Unban  (Made by 2g.m49    ║")
    print("╚══════════════════════════════════════════╝")
    print()

    if SERVER_KEY == "YOUR_SERVER_KEY_HERE":
        print("[ERROR] Open the script and set SERVER_KEY before running.")
        sys.exit(1)

    print("● Fetching ban list …")
    user_ids = fetch_banned_ids()

    if not user_ids:
        print("\n  No banned users found — nothing to do.\n")
        return

    print(f"  ✓  {len(user_ids):,} banned user(s) found.\n")

    batches = build_batches(user_ids)
    print(f"● Built {len(batches)} batch(es) of up to {BATCH_SIZE} IDs each.\n")

    try:
        confirm = input(f"  Proceed to unban all {len(user_ids):,} users? [y/N] ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n  Cancelled.")
        return

    if confirm != "y":
        print("  Cancelled.")
        return

    print()

    # ── Step 4: run unbans ────────────────────────────────────
    print("● Sending :unban commands …")
    success, failed, errors = run_unbans(batches)

    # ── Summary ───────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════╗")
    print("║                 Summary                  ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Total batches : {len(batches):<24}║")
    print(f"║  Succeeded     : {success:<24}║")
    print(f"║  Failed        : {failed:<24}║")
    print("╚══════════════════════════════════════════╝")

    if errors:
        print("\n  Errors:")
        for e in errors:
            print(f"    • {e}")

    print()


if __name__ == "__main__":
    main()