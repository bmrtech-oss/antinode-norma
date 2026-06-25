# Antinode Norma – Step‑by‑Step Commands

## 1. Setup

```bash
# Clone and enter the project
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate          # Windows

# Install the package (all dependencies)
pip install -e .

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your LLM provider keys (OpenRouter, Anthropic, etc.)
```

---

## 2. Write a User Story

Create a file `story.md`:

```bash
cat > story.md <<EOF
# Story

## Title
As a registered user, I want to reset my password so that I can regain access to my account.

## Acceptance Criteria
- The system returns a "Forgot Password" link on the login page.
- The system returns a password reset email within 2 minutes after submitting a registered email.
- The system returns a secure, time‑limited reset link that expires in 1 hour.
- The system returns a confirmation when the new password is set.
- The system returns a successful login session with the new password.
EOF
```

---

## 3. Check INVEST Quality

```bash
anorm generate --quality-only "$(cat story.md)"
```

Expected output: `Quality score: 1.0` and `Passes INVEST: True`.

---

## 4. Generate Gherkin Feature File

```bash
anorm generate "$(cat story.md)"
```

This creates `features/reset_password.feature` (or custom name).

### Preview without writing files

```bash
anorm generate --dry-run "$(cat story.md)"
```

### Interactive mode for failed generation

```bash
anorm generate --interactive "$(cat story.md)"
```

---

## 5. Validate the Feature File (Optional)

```bash
python -m antinode_norma.codegen.cli.commands validate -f features/reset_password.feature --verbose
```

Expected: `✅ Feature file is valid and passes all quality checks.`

---

## 6. Generate Executable Tests

### Playwright (with Page Objects & Step Definitions)

```bash
python -m antinode_norma.codegen.cli.commands generate \
    -f features/reset_password.feature \
    -fw playwright \
    --use-page-objects \
    --generate-step-defs
```

Output: `generated_tests/playwright/`

### Cypress

```bash
python -m antinode_norma.codegen.cli.commands generate \
    -f features/reset_password.feature \
    -fw cypress
```

### Selenium (pytest)

```bash
python -m antinode_norma.codegen.cli.commands generate \
    -f features/reset_password.feature \
    -fw selenium
```

### Optional: Disable Formatter (if prettier not installed)

```bash
set CODEGEN_QUALITY_RUN_FORMATTER=false   # Windows
# export CODEGEN_QUALITY_RUN_FORMATTER=false  # Linux/Mac
```

---

## 7. Run the Generated Tests

### Playwright

```bash
npm init playwright@latest    # first time only
npx playwright test generated_tests/playwright/reset_password.spec.ts
```

### Cypress

```bash
npm install cypress            # first time only
npx cypress run --spec generated_tests/cypress/reset_password.cy.js
```

### Selenium

```bash
pip install selenium pytest   # first time only
pytest generated_tests/selenium/reset_password_test.py
```

---

## 8. Full Workflow in One Shot (Optional)

```bash
# Story → Feature → Playwright tests with quality enhancements
anorm generate "$(cat story.md)" \
    && python -m antinode_norma.codegen.cli.commands validate -f features/reset_password.feature \
    && python -m antinode_norma.codegen.cli.commands generate -f features/reset_password.feature -fw playwright --use-page-objects --generate-step-defs
```

---

## Additional Commands

| Action | Command |
| :--- | :--- |
| Generate only Page Objects | `python -m antinode_norma.codegen.cli.commands generate -f features/reset_password.feature -fw playwright --use-page-objects` |
| Generate only Step Definitions | `python -m antinode_norma.codegen.cli.commands generate -f features/reset_password.feature -fw playwright --generate-step-defs` |
| Custom output directory | `-o ./my_tests` |
| Verbose output | `--verbose` |
| Use a config file | `-c ./configs/codegen.yaml` |
| Validate a feature | `python -m antinode_norma.codegen.cli.commands validate -f features/reset_password.feature` |

---

**Happy testing!** 🧪
