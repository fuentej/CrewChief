# Prerequisites for Windows

CrewChief requires Python 3.11+ and optionally Azure AI Foundry Local for AI features.

## Python 3.11+

### Check if Python is installed

```bash
python --version
```

You should see:
```
Python 3.11.x or higher
```

If you see Python 3.13.x, that's perfect!

### Install Python (if needed)

1. Download from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Verify: `python --version`

### Verify pip is installed

```bash
python -m pip --version
```

If pip is missing:
```bash
python -m ensurepip --upgrade
```

## Azure AI Foundry Local (Optional)

Azure AI Foundry Local is only required for AI-powered features (summary, suggest-maint, track-prep). All core garage management features work without it.

### System Requirements

- Windows 10/11 (x64/ARM) or Windows Server 2025
- Minimum 8 GB RAM (16 GB recommended)
- Minimum 3 GB free disk space (15 GB recommended)

### Check if installed

```bash
foundry --version
```

### Install Azure AI Foundry Local

```bash
winget install Microsoft.FoundryLocal
```

**Official docs:** [Microsoft Learn - Foundry Local](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started)

### Download and run a model

1. List available models:
   ```bash
   foundry model list
   ```

2. Download a model:
   ```bash
   foundry model download phi-3.5-mini
   ```

3. Start the service:
   ```bash
   foundry service start
   ```

4. Get your API endpoint:
   ```bash
   foundry service status
   ```

   **Important:** Copy the endpoint URL shown (e.g., `http://localhost:52734/v1`).

### Configure CrewChief

Create a `.env` file in your crewchief directory:

```
CREWCHIEF_LLM_BASE_URL=http://localhost:52734/v1
CREWCHIEF_LLM_MODEL=phi-3.5-mini
```

Replace `52734` with your actual port from `foundry service status`.

### Verify it works

```bash
curl http://localhost:YOUR_PORT/v1/models
```

You should see JSON output listing available models.

### Recommended models

- **phi-3.5-mini** (3.8B) - Fast, efficient
- **phi-3-medium** (14B) - Better reasoning, needs more RAM
- **GPT-OSS-20b** - Optimized for edge, requires 16GB+ RAM

### Running without Foundry Local

- ✅ All garage commands work: `add-car`, `list-cars`, `show-car`, `log-service`, `history`
- ❌ AI commands show friendly error: `summary`, `suggest-maint`, `track-prep`

Disable LLM in config:
```
CREWCHIEF_LLM_ENABLED=false
```

## Git

### Check if installed

```bash
git --version
```

### Install if needed

Download from [git-scm.com](https://git-scm.com/)

## Quick checklist

Before installing CrewChief:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] pip working (`python -m pip --version`)
- [ ] Git installed (`git --version`)
- [ ] (Optional) Azure AI Foundry Local running (`foundry service status`)

## Troubleshooting

### Python not found

Reinstall Python and check "Add Python to PATH" during installation.

### Virtual environment activation fails

If you get an execution policy error:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Foundry Local not responding

1. Check if service is running:
   ```bash
   foundry service status
   ```

2. Start it if needed:
   ```bash
   foundry service start
   ```

3. Check logs:
   ```bash
   foundry service logs
   ```

4. Restart if needed:
   ```bash
   foundry service restart
   ```

5. Verify correct port in `.env` file
