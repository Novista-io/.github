# Novista-io/.github

The public profile shown on [github.com/Novista-io](https://github.com/Novista-io).

- `profile/README.md` is the page itself.
- `profile/assets/` holds its graphics. They are generated, so don't edit them by hand.
- `tools/build.py` generates the graphics. All the copy is at the top of the file and matches [novista.io](https://novista.io).

## Changing the page

```sh
pip install -r tools/requirements.txt
tools/fetch_fonts.sh            # once
python3 tools/build.py
```

Then commit `profile/assets/` with your change.

The graphics use novista.io's fonts (Bricolage Grotesque, Geist and Archivo, all under the SIL Open Font License), converted to outlines. GitHub shows images without web fonts, so this keeps the lettering the same everywhere. The icons come from [Lucide](https://lucide.dev) (ISC, `tools/lucide-LICENSE.txt`) and [Simple Icons](https://simpleicons.org) (CC0, `tools/simple-icons-LICENSE.md`). Brand names and logos belong to their owners. Every animation is plain CSS and stops when a visitor's system asks for reduced motion.
