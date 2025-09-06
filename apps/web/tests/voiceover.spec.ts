import { test, expect } from '@playwright/test';

test.describe('Voiceover page navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Start from script page to mimic flow
    await page.goto('/script');
  });

  test('loads sanitized script on voiceover page when navigating forward', async ({ page }) => {
    const original = `Scene 1 (0:00-0:30): [Intro visuals] Hello there!\n\nScene 2: [Narrator: "This should be read."]`;

    await page.addInitScript((orig) => {
      localStorage.setItem('tubeai_script', orig);
      localStorage.setItem('tubeai_original_script', orig);
      localStorage.setItem('tubeai_from_script', 'true');
    }, original);

    await page.goto('/voiceover');

    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();
    const text = await textarea.inputValue();
    expect(text).not.toContain('Scene 1');
    expect(text).not.toContain('0:00');
    expect(text).not.toContain('[');
    expect(text).toContain('Hello there!');
    expect(text).toContain('This should be read.');

    // navigation flag should be cleared after mount
    await expect(page.evaluate(() => localStorage.getItem('tubeai_from_script'))).resolves.toBeNull();
  });

  test('shows empty sanitized warning when sanitization becomes empty', async ({ page }) => {
    const original = `Scene 1: [Intro visuals] (0:00-0:30)`; // sanitized => empty

    await page.addInitScript((orig) => {
      localStorage.setItem('tubeai_script', orig);
      localStorage.setItem('tubeai_original_script', orig);
      localStorage.setItem('tubeai_from_script', 'true');
    }, original);

    await page.goto('/voiceover');
    const warn = page.locator('text=No narratable text found after sanitizing');
    await expect(warn).toBeVisible();
  });
});


