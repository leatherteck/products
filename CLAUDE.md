# LeatherTek Development Rules

## Project Approach & Planning
1. Start by carefully reading the problem and scanning the codebase for relevant files.
2. Write a clear plan with the TodoWrite tool with a checklist of items to complete.
3. Share the plan with me for approval **before** starting implementation.
4. Work on tasks step by step, marking each as completed in the todo tracker.
5. After each step, provide a short, high-level explanation of what was changed.
6. Never skip steps in the plan unless I approve it.
7. If something is unclear, pause and ask me before continuing.

## Code Quality & Safety
8. Match the project's existing style (naming, formatting, structure).
9. Keep all changes **as simple and minimal as possible**. Avoid large or complex edits.
10. Prefer explicit typing (TypeScript/Python type hints) to reduce ambiguity.
11. Always add at least minimal error handling (try/catch, validation, fallback).
12. Do not remove or refactor code unless required by the task and confirmed with me.
13. **When adding or calling functions/services, always use the exact existing service names and method signatures. Do not invent or rename methods.**
14. **Before implementing ANY blockchain operations, API integrations, or database operations, FIRST examine existing working code to identify the exact patterns, field names, and constraints being used. Never assume documentation or schema files are accurate - the working code is the source of truth.**
15. **Security Priority**: All blockchain interactions and external API calls must include proper validation, rate limiting, and error handling to prevent exploits or service abuse.

## Communication
16. Always explain *why* a change is made, not just *what* was changed.
17. Provide mid-progress updates for tasks that take longer than ~15 minutes.
18. Clarify assumptions with me before proceeding if unsure.
19. **Never use special Unicode characters** (arrows →, bullets •, etc.) in code, print statements, or log messages. Use ASCII alternatives (like "->", "-", "*") to avoid encoding errors on Windows systems.

## Web Development Approach
19. **Use custom HTML/CSS/JS instead of drag-and-drop builders** - Build websites using clean div structures with custom code for better developer control and performance.
20. **Performance First** - Optimize for Core Web Vitals (LCP, FID, CLS) and aim for 90+ performance scores.
21. **Sales Funnel Structure** - Organize content to guide users through awareness → interest → desire → action (AIDA).
22. **Mobile-First Design** - Ensure responsive design that works perfectly on mobile devices.
23. **Clean Code Structure** - Use semantic HTML, organized CSS, and minimal JavaScript for maintainability.

## GoHighLevel (GHL) Custom Code Rules
24. **GHL strips addEventListener** - GHL's custom code sanitizer may strip or block `addEventListener()`. Always use inline event handlers (`onclick=""`, `onload=""`) instead of JavaScript event listeners.
25. **Avoid DOMContentLoaded** - Use inline `onclick` or global functions instead of `DOMContentLoaded` event listeners, as GHL may not execute them properly.
26. **Pre-load iframes when possible** - For video players, pre-load the iframe in the HTML with `display: none` and just swap `src` or visibility on click, rather than dynamically creating iframes with JavaScript.
27. **Use simple, global functions** - Define functions in global scope (not wrapped in IIFE or closures) so inline event handlers can access them. Example: `function playVideo() { ... }` with `onclick="playVideo()"`.
28. **Test YouTube autoplay separately** - YouTube autoplay (`?autoplay=1`) may be blocked by GHL or browser policies. Always verify autoplay works in the actual GHL environment, not just local testing.
29. **Inline event handlers are more reliable** - When JavaScript doesn't work in GHL, switch from `addEventListener` to inline `onclick=""` attributes on HTML elements.
30. **Keep IDs unique and simple** - Use simple, descriptive IDs without special characters for elements that JavaScript needs to access in GHL custom code.
31. **Validate in GHL builder, not just locally** - Code that works locally may not work in GHL due to script sanitization, CSP policies, or framework conflicts. Always test in the actual GHL environment.

## Lessons Learned from Video Player Implementation
### Challenge: YouTube video thumbnail displayed but video wouldn't play on click
**Root Cause**: GHL was stripping or blocking `addEventListener()` event listeners in custom code

**Failed Approaches**:
- Using `addEventListener('click', ...)` with IIFE wrapper
- Using `DOMContentLoaded` event listener
- Dynamically creating iframe with `document.createElement()`
- Adding event prevention (`e.preventDefault()`, `e.stopPropagation()`)
- Changing YouTube domains (`youtube.com` vs `youtube-nocookie.com`)
- Adding extra iframe attributes (`enablejsapi`, `allowfullscreen`, etc.)

**Working Solution**:
- Pre-loaded iframe in HTML with `display: none`
- Used inline `onclick="playVideo()"` on container div
- Created simple global function `playVideo()` that:
  1. Hides thumbnail with `style.display = 'none'`
  2. Shows iframe with `style.display = 'block'`
  3. Updates iframe src with `?autoplay=1` parameter

**Key Insight**: GHL's custom code environment has stricter limitations than standard HTML. When JavaScript event listeners fail, fall back to inline event handlers which are more reliable in restricted environments.