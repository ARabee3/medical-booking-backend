# Git Workflow

**Team:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Repos:** `medical-booking` (React frontend), `medical-booking-backend` (Django backend)

---

## 1. Branch Structure (Per Repo)

```
main          (production-ready, protected, no direct pushes)
  └── develop (integration branch, protected, no direct pushes)
       ├── feature/ahmed-auth-login
       ├── feature/ahmed-auth-register
       ├── feature/abdu-doctor-list
       ├── feature/gerges-appointments-list
       └── feature/mokhtar-admin-dashboard
```

**Never push directly to `main` or `develop`.** Always use Pull Requests.

---

## 2. Branch Naming Convention

```
feature/<name>-<short-description>
fix/<name>-<short-description>
docs/<name>-<short-description>
```

**Examples:**
- `feature/ahmed-auth-login`
- `feature/abdu-doctor-search`
- `fix/gerges-appointment-cancel`
- `docs/mokhtar-readme-update`

**Backend-specific examples:**
- `feature/ahmed-be-jwt-setup`
- `feature/abdu-be-doctor-models`
- `fix/gerges-be-appointment-booking`

---

## 3. Starting Work

```bash
# 1. Make sure develop is up to date
git checkout develop
git pull origin develop

# 2. Create your feature branch from develop
git checkout -b feature/ahmed-auth-login

# 3. Work on your feature, commit regularly
# 4. Push branch to remote
git push -u origin feature/ahmed-auth-login
```

---

## 4. Commit Messages

Use conventional commits for clarity:

```
type(scope): short description

Longer explanation if needed.
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semi colons, etc (no code change)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding tests
- `chore`: Updating build tasks, package manager configs, etc

**Examples:**
```
feat(auth): add login form with validation

feat(doctors): implement doctor list grid with filters

fix(appointments): prevent double booking in mock data

docs: update user stories for booking flow
```

**Rules:**
- Keep subject line under 50 characters
- Use present tense: "add" not "added"
- Don't end subject with a period

---

## 5. Pull Request Rules

### Before Opening a PR

```bash
# 1. Rebase on latest develop to avoid conflicts
git checkout develop
git pull origin develop
git checkout feature/your-branch
git rebase develop

# 2. Resolve any conflicts
# 3. Test your feature works
# 4. Run linting / formatting
make lint       # backend
npm run lint    # frontend
```

### PR Description Template

```markdown
## What
Brief description of changes

## Stories
- Closes BE-001
- Closes BE-002

## Testing
- [ ] All tests pass (`make test` or `pytest`)
- [ ] Follows backend conventions
- [ ] API contract verified against docs/API_CONTRACT.md

## Checklist
- [ ] I have not modified shared files without approval
- [ ] My code follows the project's conventions
```

### Review Requirements

- **At least 1 approval** from a teammate before merging
- PR creator cannot self-approve
- Address review comments before merge
- If shared files (`shared/permissions.py`, `config/settings/base.py`, etc.) are modified, **tag Ahmed** (steward of shared files) for review

---

## 6. Merging

```bash
# Use "Create a merge commit" or "Squash and merge"
# Team preference: Squash and merge for features (clean history)
# Preserve: Individual commits if you want full history
```

**After merge:**
```bash
# Delete your local and remote feature branch
git checkout develop
git pull origin develop
git branch -d feature/ahmed-auth-login        # local
git push origin --delete feature/ahmed-auth-login  # remote
```

---

## 7. Handling Merge Conflicts

If `develop` has moved forward while you worked:

```bash
git checkout feature/your-branch
git fetch origin
git rebase origin/develop

# Resolve conflicts in your editor
# Then:
git add .
git rebase --continue

# Force push the rebased branch (safe on feature branches)
git push --force-with-lease origin feature/your-branch
```

**Golden Rule:** Never rebase `main` or `develop`. Only rebase feature branches.

---

## 8. Emergency Fixes

If a critical bug is found on `main`:

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 2. Fix, commit, push

# 3. Open PR to BOTH main and develop
# 4. Fast-track review (all 4 devs approve if truly critical)
```

---

## 9. Shared File Changes

The following files are **"sacred"**. If you need to modify them, announce it:

- `shared/permissions.py`
- `shared/pagination.py`
- `shared/mixins.py`
- `shared/exceptions.py`
- `config/settings/base.py`
- `config/settings/local.py`
- `config/settings/production.py`
- `config/urls.py`
- `Makefile`
- `requirements/base.txt`

**Process:**
1. Mention in group chat: "I need to add `IsAdmin` permission to shared/permissions.py"
2. Create a focused PR just for that change, OR include it in your feature PR with clear comment
3. Tag teammates who might be affected

---

## 10. Communication

- **Daily sync:** Quick standup (even async in chat) — what you did, what you'll do, blockers
- **Blockers:** If you're waiting for a model or shared type, ask immediately
- **Demo day:** When a story is done, show it to the team before merging
