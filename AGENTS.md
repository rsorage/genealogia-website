## UI workflow
After any UI change:
1. Start the dev server and open the changed pages with playwright-cli.
2. Screenshot at 375px, 768px and 1440px widths. Look at each one
   and fix layout breaks, overflow, clipped text or bad spacing.
3. Check the browser console and network for errors and failed requests.
4. Run web-design-guidelines on the changed files. Fix every finding.
5. Repeat steps 2–4 until screenshots look right and the audit is clean.
Report what you found and fixed.

