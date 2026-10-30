# Brand assets

All marks are vector paths in the site palette — no external fonts are required to render the icon,
and nothing is traced from another organisation's artwork.

## Files (`assets/img/`)

| File | Use |
|---|---|
| `logo.svg` | Site header icon and general-purpose tile |
| `favicon.svg` | Browser tab icon (scales to any size) |
| `icon-16.png`, `icon-32.png` | Legacy favicon fallbacks |
| `icon-180.png` | Apple touch icon |
| `icon-512.png` | App icon, slide decks, large placements |
| `mark.svg` | Book alone, no tile — for cream or white backgrounds |
| `lockup-light.svg` / `.png` | Mark plus wordmark, dark text — letterheads, posters, slides |
| `lockup-dark.svg` / `.png` | Mark plus wordmark on deep green — title slides, social banners |
| `og-image.png` | 1200×630 social preview card, referenced by `og:image` on every page |

## Palette

| Role | Hex |
|---|---|
| Deep green (primary) | `#14532d` |
| Mid green (links, secondary text) | `#1f6f45` |
| Soft green (page tint, accents) | `#8fcfa8` |
| Cream (background) | `#faf6ed` |
| Paper (surfaces) | `#fffdf8` |
| Ink (body text) | `#1d2321` |
| Amber (draft and warning notices) | `#8a5a12` |

## Usage

- Keep clear space of at least one quarter of the tile's width on every side.
- Minimum size: 16 px for the tile, 24 px for the bare mark, 120 px wide for a lockup.
- Do not stretch, recolour, add gradients or shadows, rotate the mark, or place the tile on a green
  background — use the bare `mark.svg` or the dark lockup instead.
- The wordmark is set in a transitional serif (Iowan Old Style, falling back to Palatino and
  Georgia). The lockup SVGs use live text, so install-free rendering may substitute a near-equivalent
  serif; use the PNG lockups where the exact form matters.

## Social card

`og-image.png` states the entry count and the scientific review line, so a link shared on social media
or in a message preview carries the corpus's actual status before anyone opens it. Regenerate it if the
entry count changes materially or when the review date moves.
