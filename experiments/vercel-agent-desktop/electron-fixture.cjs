const { app, BrowserWindow } = require('electron');

app.setName('research-electron-fixture');
app.commandLine.appendSwitch('force-renderer-accessibility');
app.disableHardwareAcceleration();

app.whenReady().then(async () => {
  app.setAccessibilitySupportEnabled(true);
  const window = new BrowserWindow({
    title: 'Research Electron Fixture',
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  const html = [
    '<title>Research Electron Fixture</title>',
    '<main><h1>Synthetic query plan</h1>',
    '<input aria-label="Fixture Query" value="SELECT 1">',
    '<button aria-label="Fixture Run">Run fixture</button></main>',
  ].join('');
  await window.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
});
app.on('window-all-closed', () => app.quit());
