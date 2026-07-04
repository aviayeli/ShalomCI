# ShalomCI - Design System & Brand Guidelines

## 1. Core Identity & Vibe
*   **Product:** ShalomCI (Component Intelligence) - an Enterprise-grade B2B desktop application for electronic component lifecycle management (BOM, EOL, NRND, LTB alerts).
*   **Vibe:** Professional, trustworthy, engineered, and clean. It should look like a modern fintech or data-analytics platform.
*   **Language & Direction:** The interface is STRICTLY Hebrew and Right-To-Left (RTL).

## 2. RTL Typography Strict Rules
*   **Base Font Size:** Hebrew requires more "white space" inside the letters. The base body text must be at least `16px` (never smaller) to ensure perceived legibility equals a 14px Latin font.
*   **Line Height:** Set line-height to `1.5` or `1.7` for body text. 
*   **Letter Spacing (CRITICAL):** NEVER apply `letter-spacing` (tracking) to Hebrew text. It breaks the Gestalt recognition of Hebrew words. 
*   **Font Stack:** Use `Assistant`, `Heebo`, or `system-ui`.
*   **Numbers in Tables:** Use `Tabular Figures` (monospaced numbers) for financial and inventory data so columns align perfectly.

## 3. RTL Layout & CSS Logical Properties
*   **DO NOT use physical directions** like `margin-left`, `padding-right`, or `left: 0`.
*   **MUST use logical properties:**
    *   `margin-inline-start` / `margin-inline-end`
    *   `padding-inline-start` / `padding-inline-end`
    *   `border-inline-start`
    *   `inset-inline-start` / `inset-inline-end`
*   **Text Alignment:** Use `text-align: start` (which maps to right in RTL) instead of `text-align: right`. EXCEPTION: Numbers and LTR English words inside tables should be aligned to `end` (left) for easy reading.
*   **Bidirectional Isolation:** When mixing Hebrew with LTR elements (like English part numbers, phone numbers, or code snippets), wrap the LTR elements in `<bdo dir="ltr">` or use `unicode-bidi: isolate` so they don't flip backwards.

## 4. Components & Interaction
*   **Buttons & Touch Targets:** 
    *   Minimum touch target height must be `48px` (to comply with accessibility standards).
    *   Hebrew words are typically shorter than English words (e.g., "Search" -> "חפש"). To prevent buttons from looking too small/stubby, increase the horizontal padding (e.g., `padding-inline: 24px` or `32px`).
*   **Icons in Buttons:** 
    *   Leading icons go on the *right* side of the text.
    *   Trailing icons go on the *left* side of the text.

## 5. Iconography Mirroring Rules
*   **DO MIRROR (Flip horizontally):** Directional icons, navigation arrows, back/forward buttons, breadcrumb chevrons, progress bars, and "send" icons.
*   **DO NOT MIRROR:** Media controls (Play/Pause), clocks/time icons, math symbols (+, -), and real-world asymmetrical objects (e.g., camera, trash can).

## 6. Color Palette
*   **Primary:** Dark Navy/Slate (trust, engineering).
*   **Secondary/Accents:** Clean White/Gray backgrounds with subtle borders.
*   **Semantic Alerts (CRITICAL for BOM analysis):**
    *   Danger/EOL: Crisp Red (Ensure 4.5:1 contrast).
    *   Warning/NRND: Amber/Yellow.
    *   Safe/Active: Emerald Green.
