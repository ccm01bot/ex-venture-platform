import { chromium } from 'playwright';
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/scan');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/tmp/scan_feed.png', fullPage: true });
  await browser.close();
})();
