import { chromium } from 'playwright';
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 1000 });
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/Users/franzccm/.gemini/antigravity/brain/af62640c-d3e7-4909-b355-207d4cafac1e/artifacts/dashboard_overhaul.png' });
  await browser.close();
})();
