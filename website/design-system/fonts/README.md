# Vendored design fonts

The two WOFF2 files in the Claude Design archive were not accepted because the archive supplied no license or source receipt. These replacements are fresh, normal-style Latin variable subsets served by the official Google Fonts infrastructure and downloaded only for local vendoring. The website makes no font CDN request.

| Family | Weights | Immutable binary source | SHA-256 | License |
|---|---|---|---|---|
| Inter | 100–900 | `https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7W0Q5nw.woff2` | `c940764593d0fe5d596be327ca7558855e018039fb78509aa21921fd3644c3e4` | [Inter-OFL.txt](Inter-OFL.txt) |
| Roboto Condensed | 100–900 | `https://fonts.gstatic.com/s/robotocondensed/v31/ieVl2ZhZI2eCN5jzbjEETS9weq8-19K7DQk6YvM.woff2` | `718ced55c5d8e207d6d14b1765fe6cf5886882834f45cc0ad23283cd210f9a96` | [RobotoCondensed-OFL.txt](RobotoCondensed-OFL.txt) |

The license texts were read from `google/fonts` commit `389b770410cc0b7c21c85673bfa2077420fe7f65` and are preserved unmodified. Exact license-source URLs and hashes are in [`../SOURCE_RECEIPT.json`](../SOURCE_RECEIPT.json).

Coverage is the Google Fonts `latin` subset used by the accepted English-first website direction. Do not imply that this subset covers future locales. Add script-specific subsets only through a separate reviewed dependency update with its own receipt.

