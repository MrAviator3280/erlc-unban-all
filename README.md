# ER:LC Mass Unban Tool

Mass unban utility for Emergency Response: Liberty County servers.

---

## Overview

This script retrieves all banned user IDs from a server and issues `:unban` commands through the ER:LC API. It is designed to be safe, rate-limit aware, and simple to run from the command line.

---

## Features

* Fetches full ban list via API
* Sequential unban execution
* Built-in rate limit handling (429 + headers)
* Progress bar with live updates
* Graceful error handling and summaries

---

## Tech Stack

* Python 3
* `requests` (HTTP client)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/erlc-mass-unban.git
cd erlc-mass-unban
```

Install dependencies:

```bash
pip install requests
```

---

## Usage

Run the script:

```bash
python main.py
```

You will be prompted to enter your ER:LC API key.

---

## Configuration

Inside the script:

```python
BATCH_SIZE = 1
FALLBACK_WAIT_SECONDS = 5
```

* `BATCH_SIZE` must remain `1` (API limitation - to be fixed/improved)
* `FALLBACK_WAIT_SECONDS` is used if rate limit headers are missing

---

## How it works

1. Sends `GET /v1/server/bans` to retrieve banned user IDs
2. Splits IDs into batches (currently size = 1)
3. Sends `POST /v2/server/command` with `:unban <id>`
4. Monitors rate limit headers and pauses when required
5. Displays progress and logs failures

---

## Example

```text
● Fetching ban list …
✓ 87 banned user(s) found.

● Sending :unban commands …
[====================----------] 66% (58/87)
```

---

## Limitations

* ER:LC requires at least one player in-game for `:unban` to work
* Multiple IDs per command are not supported
* Large ban lists may take time due to rate limiting

---

## Error Handling

* `403` → Invalid API key
* `422` → Server empty (no players online)
* `400` → Bad request
* `429` → Automatically retried after delay

All failed batches are logged at the end of execution.

---

## Support / Feedback

Message **2g.m49 on Discord** to report bugs or suggest fixes.

---

## License

This project uses a **custom proprietary license**.

* Modification is not permitted
* You may not claim the project as your own
* Credit to the original author must be maintained

See the `LICENSE` file for full terms.

---

## Author

2g.m49
