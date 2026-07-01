const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && idx + 1 < process.argv.length) return process.argv[idx + 1];
  return fallback;
}

async function main() {
  const htmlPath = path.resolve(argValue("--html", "paper_zh_print.html"));
  const pdfPath = path.resolve(argValue("--pdf", "paper_zh_share.pdf"));
  const chromePath = argValue("--chrome", process.env.CHROME_PATH || "");

  if (!fs.existsSync(htmlPath)) {
    throw new Error(`Input HTML not found: ${htmlPath}`);
  }

  const launchOptions = { headless: true };
  if (chromePath && fs.existsSync(chromePath)) {
    launchOptions.executablePath = chromePath;
  } else {
    const defaultChrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
    if (fs.existsSync(defaultChrome)) launchOptions.executablePath = defaultChrome;
  }

  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({
    viewport: { width: 1240, height: 1754 },
    deviceScaleFactor: 1,
  });
  await page.goto(`file:///${htmlPath.replace(/\\/g, "/")}`, { waitUntil: "networkidle" });
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: false,
  });
  await browser.close();
  console.log(pdfPath);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
