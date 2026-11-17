# Font sources

All fonts are Noto, released under the SIL Open Font License 1.1 (OFL). Everything came from github.com/notofonts. Sizes were checked with a HEAD request before download and match the files on disk. Licence texts sit next to the fonts. The fonts are used only to bake sign textures in tools/signs/. They do not ship in the game build, only the baked PNGs do.

| File | Use | Size | Source URL | Licence |
|---|---|---|---|---|
| NotoSansSC-Black.otf | Chinese (Simplified), chunky sans | 8.86 MB | https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Black.otf | OFL-NotoCJK.txt |
| NotoSansSC-Bold.otf | Chinese (Simplified) and small Latin | 8.54 MB | https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Bold.otf | OFL-NotoCJK.txt |
| NotoSerifSC-Black.otf | Chinese (Simplified), signboard serif | 11.86 MB | https://github.com/notofonts/noto-cjk/raw/main/Serif/SubsetOTF/SC/NotoSerifSC-Black.otf | OFL-NotoCJK.txt |
| NotoSansTamil-Bold.ttf | Tamil | 0.05 MB | https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansTamil/unhinted/ttf/NotoSansTamil-Bold.ttf | OFL-NotoTamil.txt |
| NotoSansTamil-Black.ttf | Tamil, heavy | 0.05 MB | https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansTamil/unhinted/ttf/NotoSansTamil-Black.ttf | OFL-NotoTamil.txt |
| NotoSerifDisplay-Black.ttf | Bold Latin display face for stall lettering | 0.48 MB | https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSerifDisplay/unhinted/ttf/NotoSerifDisplay-Black.ttf | OFL-NotoTamil.txt (same OFL text, Noto Project Authors) |
| OFL-NotoCJK.txt | licence | 4 KB | https://github.com/notofonts/noto-cjk/raw/main/Sans/LICENSE | OFL 1.1 |
| OFL-NotoTamil.txt | licence | 4 KB | https://github.com/notofonts/tamil/raw/main/OFL.txt | OFL 1.1 |

Total about 29.8 MB. The CJK files are the "SubsetOTF/SC" builds (about 8,000 common Simplified Chinese characters, enough for the signs, checked by tools/signs/check.py). Malay and English use Latin glyphs from Noto Sans SC and Noto Serif Display.
