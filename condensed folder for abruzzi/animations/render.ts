import {renderVideo} from '@revideo/renderer';

async function run() {
  console.log('Rendering video at 60 FPS...');
  await renderVideo({
    projectFile: './src/project.ts',
    variables: {},
    settings: {
      logProgress: true,
      puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
        headless: true,
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      },
    },
  });
  console.log('Render complete!');
}

run();