# Rebuild the browser SDK

End users do not need Node.js. The widget already includes its SDK inline.

Maintainers need Node.js 20 or later. In this directory run:

```sh
npm ci --ignore-scripts
npm run build
```

The pinned lockfile is the dependency graph used for the accepted Windows build. The build replaces only the marked SDK script in the existing widget; it does not rewrite its transfer logic. Regenerate `SHA256SUMS.json` and the signed release after any change. See [third-party notices](../THIRD_PARTY_NOTICES.md) for bundled license texts.
