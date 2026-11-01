# Quickstart: bring a voice assistant into your meeting

This project lets an AI assistant join a meeting, listen to what people say,
and reply out loud. MeetStream gets the assistant into the call. Pipecat manages
listening, generating an answer, and speaking. You control it from your computer.

Google Meet, Zoom, and Teams have been tested with scripted speech, including
interrupting the assistant while it talks. Human microphone, echo, and overlapping
speech still need further testing.

## Before you begin

You need a Windows, Mac, or Linux computer, an internet connection, and this
project folder. On Windows, the commands run directly in PowerShell or Command
Prompt; WSL and Ubuntu are not needed.
The computer must stay awake and connected while the assistant is in a meeting.

Have these tools installed first. A technical teammate can help with this one-time setup:

- **Docker Desktop**, open and running, or Docker Engine with Compose on Linux.
  Docker runs the project in the background.
- **Python 3.11, 3.12, or 3.13**, which the start command needs.
- **The ngrok command-line tool**, which gives the meeting service a connection
  to the project on your computer.

### Windows setup (without WSL)

Use a supported **64-bit Windows Pro, Enterprise, or Education** installation on
an Intel/AMD computer. This setup needs Hyper-V, which Windows Home does not
provide. Follow [Docker's Windows installation guide](https://docs.docker.com/desktop/setup/install/windows-install/):
choose the **all-users installation** and **Hyper-V backend**, then run Docker
Desktop in **Linux-container mode**. A technical teammate may need to enable
Hyper-V and hardware virtualization and restart your computer once. The app runs
in the same Linux container as on a Mac; you control it with native Windows commands.

Install **Python 3.11–3.13 for Windows** and **ngrok for Windows**, with their
commands available on PATH. Reopen your terminal after installing them. Save the
project in a local NTFS folder under your own user account, rather than a shared
or network folder. The launcher restricts `.env` and `.run` to your account.

Windows uses `start.cmd`, `status.cmd`, and `stop.cmd`. The `./start`, `./status`,
and `./stop` examples below are for Mac/Linux; use the matching Windows command
shown beside each step. Do not use `--native` on Windows: that flag is only the
Mac/Linux development mode. Windows controls Docker directly without WSL.

Windows CI passed on Python 3.11–3.13 on November 1, including first-run setup, commands,
locking, permissions, and background-process shutdown. Full Docker Desktop and
live-meeting acceptance on a Windows desktop is still pending; see
[verification](docs/verification.md#native-windows-launcher--implementation-and-acceptance-status).

You also need the following account credentials. An API key is a secret code
that lets the project use a service on your behalf.

| Service | What it does | Setting to fill in |
| --- | --- | --- |
| MeetStream | Sends the assistant into the meeting | `MEETSTREAM_API_KEY` |
| Deepgram | Turns speech into text and answers into speech | `DEEPGRAM_API_KEY` |
| Google Gemini | Generates the assistant's answers | `GOOGLE_API_KEY` |
| ngrok | Connects the meeting service to your computer | `NGROK_AUTHTOKEN` |

These services need working accounts and available usage credit. Meeting and
voice usage may incur charges.

## 1. Get the project and open it in Terminal

Open [the project on GitHub](https://github.com/Arjun220905/meetstream-pipecat-bridge), choose **Code → Download ZIP**,
and extract the ZIP before running anything. Keep the extracted folder under
your own user account. If you already have Git, you can instead clone
`https://github.com/Arjun220905/meetstream-pipecat-bridge.git`.

The downloaded folder may be named `meetstream-pipecat-bridge-main`; the examples
below use `meetstream-pipecat-bridge`. Use your actual extracted folder name.

Open Terminal on Mac/Linux, or PowerShell on Windows. Type `cd` followed by a
space, then the path to this project folder, and press Enter. For example (Mac/Linux):

```sh
cd "/path/to/meetstream-pipecat-bridge"
```

On Windows, for example:

```powershell
cd "C:\Users\YourName\meetstream-pipecat-bridge"
```

Replace the example path with the folder's actual location. On a Mac,
you can drag the folder from Finder into Terminal after typing `cd `.

Run all the commands below from this folder. Paste one command at a time and
press Enter to run it.

## 2. Set up your credentials once

Run:

```sh
./start
```

Windows: `.\start.cmd`.

The first run installs the project's dependencies and creates a settings file
called `.env`. If credentials are missing, it stops and tells you which ones to
add. This is an expected part of first-time setup.

Open `.env` in a plain-text editor. It is a hidden file: in Finder, press
Command + Shift + period to show hidden files; most Linux file managers use
Ctrl + H. On Windows, run `notepad .env` from the project folder; turn on file
name extensions in File Explorer so you can check the name stays `.env`.

Find these four lines and paste your own credentials after each `=`:

```text
MEETSTREAM_API_KEY=your_meetstream_key
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_google_key
NGROK_AUTHTOKEN=your_ngrok_token
```

Replace the example values above with your actual credentials. Save the file
as `.env`, without adding `.txt`. Keep the other settings as they are; the project
generates its own security settings automatically. Never share this file or
include it in a screenshot.

With the ngrok setup above, leave `PUBLIC_URL` blank on first setup. The start
command fills it in automatically. If a teammate has already configured a public
connection for you, follow their settings instead.

## 3. Start the assistant and invite it

Create or open your Google Meet and copy its meeting link. In Terminal, run:

```sh
./start 'https://meet.google.com/your-meeting-code'
```

Windows (PowerShell or Command Prompt):

```powershell
.\start.cmd "https://meet.google.com/your-meeting-code"
```

Replace the entire example link with your real meeting link and keep the quotes.
Use double quotes on Windows, especially for Zoom/Teams links that contain `&`.
The first build can take several minutes. Wait for the success messages before
continuing. For Zoom or Teams, use the same command with the meeting's invitation
link instead. For Zoom, copy the full invitation link, including its passcode,
rather than the host's Start link.

Admit **MeetStream Pipecat** if it waits in the meeting lobby. On Zoom, the host
must also approve the bot's recording permission for live audio capture. Zoom can
show a recording indicator even when this project's stored recording is off.
Speak first:
the assistant listens rather than greeting the room automatically. Try asking,
“What is the capital of France?” Wait for its spoken answer. You can then try
interrupting with a new question while it is speaking.

Use headphones and take turns when trying it. Human microphone, speaker echo,
and people talking over one another still need further testing.

**Every start command containing a meeting link invites another bot.** To start
the project without inviting a bot, or to reuse an already running project, run:

```sh
./start
```

Windows: `.\start.cmd`.

To check whether the project is running:

```sh
./status
```

Windows: `.\status.cmd`.

The normal result is `Running`. This checks the project and its connection;
it does not guarantee that every paid service has credit or is available.

## 4. Stop when you are finished

Run this before putting your computer to sleep or turning it off:

```sh
./stop
```

Windows: `.\stop.cmd`.

It removes the meeting bots created by this project and shuts down the background
services and connection. Wait for confirmation that shutdown is complete.
Closing Terminal or leaving the meeting yourself does not replace this step.

If removal cannot be confirmed, the command reports an incomplete shutdown.
Restore your internet connection and run `./stop` (Windows: `.\stop.cmd`) again. Keep Docker running
until cleanup succeeds.

## Quick fixes

| What you see | What to do |
| --- | --- |
| `No such file or directory` when running `./start` | Return to step 1 and open Terminal in the correct project folder. |
| `Permission denied` on Mac/Linux | Run `chmod +x start stop status` once in the project folder, then retry. |
| Windows says a command is not recognized | Install Windows Python/ngrok and reopen the terminal. Use `.\start.cmd` from the project folder. |
| Docker reports Windows containers or cannot start without WSL | Select Linux containers and the Hyper-V backend. Windows Home cannot use this no-WSL setup. |
| A message asking for Python or Docker | Install the supported tools above; open Docker Desktop before retrying. |
| A message naming missing keys | Fill in the named settings in `.env`, save it, and rerun the command. |
| The assistant is waiting to join | Ask the meeting host to admit it and allow its audio. |
| The assistant does not answer | Check that your microphone works, speak first, and check your service accounts have credit. Run `./status` (Windows: `.\status.cmd`) to check the project. |
| `Unhealthy`, a lost connection, or an assistant that left | Run `./stop` (Windows: `.\stop.cmd`), resolve the reported problem, then use the meeting-link start command to invite a fresh bot. Conversation history starts over. |
| You changed a setting in `.env` | Run `./stop` (Windows: `.\stop.cmd`), then start again with your meeting link. |
| Shutdown is incomplete | Keep Docker running and retry `./stop`. If needed, ask a teammate to check the bots in MeetStream's dashboard. |

By default, each bot has a one-hour limit and about five minutes to join. Audio
and video recording are requested off; Zoom's capture permission and recording
indicator still apply. The voice services process meeting speech. Let participants know an AI assistant is joining.

If you need help, share the error message with a trusted teammate. Keep `.env`
and the private `.run` folder out of public messages. Do not delete the project's
saved state or Docker storage to fix a failed shutdown, because cleanup may still
need it.

For more detail, see the [README](README.md), [operations guide](docs/operations.md),
and [tested behavior and limits](docs/verification.md).
