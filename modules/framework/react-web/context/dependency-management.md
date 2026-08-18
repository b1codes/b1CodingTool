# React Web: Dependency Management

## Overview

React web projects use a JavaScript/Node.js package manager to install dependencies from the npm registry. The three main options are **npm**, **pnpm**, and **Yarn**. All three read `package.json` and produce a lockfile, but they differ in performance, disk usage, and workspace support.

**Recommendation: use pnpm for new projects.** It is significantly faster than npm, uses a content-addressable store to eliminate duplicate packages across projects, and has first-class monorepo support.

## Comparison

| | npm | pnpm | Yarn Berry |
|---|---|---|---|
| **Bundled with Node** | Yes | No (`npm i -g pnpm`) | No |
| **Install speed** | Baseline | ~2× faster | Similar to pnpm |
| **Disk usage** | High (copies per project) | Low (global content store, hard links) | Low (PnP mode) |
| **Lockfile** | `package-lock.json` | `pnpm-lock.yaml` | `yarn.lock` |
| **Workspaces / monorepo** | Basic | Excellent | Excellent |
| **Compatibility** | Universal | Very high | High (PnP mode can break some tools) |
| **Ecosystem tooling** | Universal | Widely supported | Varies |

## pnpm (Recommended)

### Setup
```bash
npm install -g pnpm          # install once globally
# or: corepack enable pnpm   # use Node's built-in corepack (preferred)
```

### Common Commands
```bash
pnpm install                 # install from pnpm-lock.yaml (CI / after pull)
pnpm add react-router-dom    # add a runtime dependency
pnpm add -D vitest           # add a dev dependency
pnpm remove axios            # remove a package
pnpm update                  # update all packages within semver constraints
pnpm update --latest         # bump all to latest (ignores constraints — review carefully)
pnpm outdated                # list packages with newer versions available
pnpm run dev                 # run a script from package.json
pnpm dlx create-vite         # run a one-off package without installing globally (like npx)
```

### package.json with pnpm
```json
{
  "name": "my-react-app",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint ."
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "@reduxjs/toolkit": "^2.2.7",
    "react-redux": "^9.1.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.3.1",
    "vitest": "^1.6.0",
    "eslint": "^9.0.0"
  },
  "engines": {
    "node": ">=20.0.0",
    "pnpm": ">=9.0.0"
  }
}
```

Enforce the correct package manager with a `.npmrc`:
```ini
# .npmrc
engine-strict=true
```

And optionally a `package.json` field to warn users who use a different manager:
```json
{
  "packageManager": "pnpm@9.4.0"
}
```

---

## npm

npm ships with Node.js and requires no extra installation. Use it when simplicity matters more than speed, or when a team/environment has constraints against additional tooling.

### Common Commands
```bash
npm install                  # install from package-lock.json
npm install react-router-dom # add a runtime dependency
npm install -D vitest        # add a dev dependency
npm uninstall axios          # remove a package
npm update                   # update within semver constraints
npm outdated                 # list packages with newer versions
npm run dev                  # run a script
npx create-vite              # run a one-off package
```

---

## Yarn

Yarn Classic (v1) is largely superseded. Yarn Berry (v2+) introduced Plug'n'Play (PnP) mode which eliminates `node_modules` entirely — fast and disk-efficient, but can break tools that expect `node_modules` on disk (some Vite plugins, Jest configs). Use Yarn Berry only if your team is already on it.

---

## Version Constraints

All three managers use npm's semver constraint syntax:

| Constraint | Meaning | Use when |
|------------|---------|----------|
| `^1.2.3` | `>=1.2.3 <2.0.0` | Most dependencies — allows compatible updates |
| `~1.2.3` | `>=1.2.3 <1.3.0` | Patch-only updates |
| `1.2.3` | Exact pin | Rarely — when a specific version is required |
| `*` or `""` | Any version | Never |

**Prefer `^`.** It allows minor and patch updates (non-breaking by semver) while preventing unexpected major version jumps.

## Lockfiles

Always commit the lockfile (`package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`). Without it, `npm install` / `pnpm install` in CI may install different patch versions than what you tested locally, causing hard-to-debug environment-specific bugs.

Never commit `node_modules/` — add it to `.gitignore`.

## Keeping Dependencies Updated

Run `pnpm outdated` (or `npm outdated`) regularly. For automated updates, use **Renovate** or **Dependabot** — they open PRs with changelogs when new versions are available, keeping updates small and reviewable rather than accumulating into a painful big-bang upgrade.

```bash
# One-off audit for security vulnerabilities
pnpm audit
npm audit

# Auto-fix non-breaking vulnerabilities
pnpm audit --fix
npm audit fix
```
