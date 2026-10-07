# ASG Assistant

Desktop (Electron) AI chat for the ASG server system.

- **Online:** Claude API. **Offline:** local Ollama. `Auto` mode switches by itself.
- **Answers from ASG data and acts on it** through tools exposed by the ASG server (`docs/ASG-PLUGIN-API.md`). Changes need your approval.
- **Offline-safe:** cached reads, queued writes.

## Run
```
npm install
npm start          # development
npm test           # core logic tests
npm run dist       # Windows installer
```
First run: Settings → add Claude API key, ASG server URL + token. For offline: install Ollama and `ollama pull llama3.1`.
