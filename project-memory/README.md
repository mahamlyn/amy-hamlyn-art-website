# Amy Hamlyn Art — Project Memory

This folder stores the working plan, decisions, and notes for the website build. It acts as a lightweight project memory that can be revisited during future development.

## Current project goal
Build a premium, modern artist portfolio for Amy Hamlyn Art with:
- elegant home page
- about section
- gallery of artwork
- exhibitions section
- blog/journal section
- contact/commission page
- content managed with Markdown files

## Core decisions
- Use Flask as the lightweight web framework.
- Store editable content in Markdown files under `content/`.
- Keep site styling polished and editorial, with a premium neutral palette.
- Use reusable templates to make future updates simple.
- Maintain easy editing for non-technical users.

## Planned development path
1. Finalise visual polish and homepage structure.
2. Add real artwork images and final content copy.
3. Improve contact/commission workflow and submission handling.
4. Add optional enhancements such as SEO metadata, gallery filtering, and image uploads.
5. Prepare for deployment with a production-ready hosting setup.

## Current to-do list
- [x] Set up site structure
- [x] Build Flask app and templates
- [x] Add sample content and styling
- [x] Validate app runs
- [x] Add contact/commission page
- [x] Refine premium visual style
- [ ] Add real Amy artwork content and photos
- [ ] Review and tighten site copy
- [ ] Connect the enquiry form to a real endpoint or email workflow
- [ ] Prepare deployment configuration

## Useful notes
- Site runs locally at `http://127.0.0.1:5000`
- Main app entry point: `app.py`
- Content files live in `content/`
- Templates live in `templates/`
- Styling lives in `static/css/styles.css`

## Memory prompts
Use this as a quick recall document when returning to the project:
- What is the tone and audience of the site?
- How should new artwork and blog entries be added?
- What information should the contact form collect?
- What real images and final copy are still needed?
- Which deployment target should be used once the site is ready?
