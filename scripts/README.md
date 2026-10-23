# Project Scripts

- `run-site.bat` creates the project virtual environment if needed, installs requirements, and starts the Flask site. Run it from this folder or the project root.
- `activate-test-env.ps1` activates the project environment in the current PowerShell session. Dot-source it: `. .\scripts\activate-test-env.ps1`.
- `deactivate-test-env.ps1` deactivates and removes the project environment and root Python cache. Dot-source it: `. .\scripts\deactivate-test-env.ps1`.
- `convert_wordpress_posts.bat` runs the WordPress post converter. Its source and destination paths are configured in `convert_wordpress_blog_posts.py`.