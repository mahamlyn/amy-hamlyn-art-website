const fs = require('node:fs');

const reportPath = 'test-results/results.json';
const summaryPath = process.env.GITHUB_STEP_SUMMARY;

if (!summaryPath) {
  throw new Error('GITHUB_STEP_SUMMARY is not available.');
}

if (!fs.existsSync(reportPath)) {
  fs.appendFileSync(
    summaryPath,
    '## Playwright browser tests\n\nNo test report was produced. Check the preceding setup and test steps.\n',
  );
  process.exit(0);
}

const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const rows = [];

function collect(suite, parents = []) {
  const titlePath = suite.title ? [...parents, suite.title] : parents;
  for (const spec of suite.specs || []) {
    const specPath = spec.title ? [...titlePath, spec.title] : titlePath;
    for (const test of spec.tests || []) {
      const attempts = test.results || [];
      const lastAttempt = attempts.at(-1);
      let result = lastAttempt?.status || 'not run';
      if (result === 'passed' && attempts.some((attempt) => attempt.status !== 'passed')) {
        result = 'flaky';
      }
      const details = attempts
        .flatMap((attempt) => attempt.errors || [])
        .map((error) => error.message)
        .filter(Boolean)
        .join('; ');
      rows.push({
        title: specPath.join(' / '),
        result,
        details: details.slice(0, 500),
      });
    }
  }
  for (const child of suite.suites || []) {
    collect(child, titlePath);
  }
}

for (const suite of report.suites || []) {
  collect(suite);
}

const count = (result) => rows.filter((row) => row.result === result).length;
const passed = count('passed');
const flaky = count('flaky');
const failed = rows.length - passed - flaky - count('skipped');
const skipped = count('skipped');
const overall = failed === 0 ? 'Passed' : 'Failed';
const escapeCell = (value) => String(value).replaceAll('|', '\\|').replaceAll('\n', ' ');
const lines = [
  '## Playwright browser tests',
  '',
  `**${overall}**: ${passed} passed, ${failed} failed, ${flaky} flaky, ${skipped} skipped (${rows.length} total).`,
  '',
  '| Result | Test case | Details |',
  '| --- | --- | --- |',
  ...rows.map((row) => `| ${escapeCell(row.result)} | ${escapeCell(row.title)} | ${escapeCell(row.details || '—')} |`),
  '',
  'Download the `playwright-results` artifact for the full HTML report, screenshots, and traces.',
  '',
];

fs.appendFileSync(summaryPath, lines.join('\n'));