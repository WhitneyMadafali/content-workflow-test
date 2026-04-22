# Non-Technical User Guide (Prompt-Based)

This guide is for users who do not code.
You only need to run one command and answer prompts.

## What this does

- Signs you in to Microsoft
- Shows your Teams as a numbered list
- Shows channels as a numbered list
- Lets you choose date range and person
- Generates a plain-English channel summary

## One-time setup (run once)

Copy and run this command:

```bash
cd /home/whitney-madafali/Test/content-workflow-test && python3 -m venv tools/teams/.venv && tools/teams/.venv/bin/pip install -r tools/teams/requirements.txt
```

## Daily use (simple)

Run:

```bash
cd /home/whitney-madafali/Test/content-workflow-test && bash run-summary.sh
```

The script will ask:

1. If you want Microsoft account picker (`y` or `n`)
2. Team number (example: `1`)
3. Channel number (example: `2`)
4. Date from (`YYYY-MM-DD`, or Enter to skip)
5. Date to (`YYYY-MM-DD`, or Enter to skip)
6. Person number (`0` means Everyone)
7. Confirm generation (`Y` to run)

You do not need to type team/channel names.

## Example

If the screen shows:

- `1) OVES All`
- `2) Marketing`

Type `1` for team.

Then if channels show:

- `1) General`
- `2) Announcements`

Type `1` for channel.

If people show:

- `0) Everyone`
- `1) Whitney Madafali`
- `2) Alex Doe`

Type `1` to summarize only Whitney's messages, or `0` for everyone.

## Common issues

- `Setup not complete`:
  - Run the setup command in this guide.
- Browser did not open:
  - Run with another browser:
  - `BROWSER=firefox bash run-summary.sh`
- Wrong Microsoft account:
  - When asked `Show Microsoft account picker?`, enter `y`.
