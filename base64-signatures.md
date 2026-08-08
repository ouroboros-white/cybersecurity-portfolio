# Base64 magic-byte signatures

A quick-reference for identifying a base64 blob *before* decoding it. Base64
encodes 3 bytes into 4 characters, so a file's magic number (its first few bytes)
always produces the same first few base64 characters. That makes the prefix a
reliable fingerprint, which saves running dead-end conversions and shows you
understand what encoding does to bytes rather than guessing in CyberChef.

## The table

| Starts with | Decodes to | What it is |
|---|---|---|
| `JAB` | `$` + null | UTF-16LE PowerShell (a `$variable`), classic `-enc` payload |
| `TVqQ` / `TVpB` / `TVpQ` | `MZ` | Windows PE: .exe or .dll |
| `f0VMR` | `\x7FELF` | Linux ELF binary |
| `H4sI` | gzip magic | Gzip-compressed data |
| `UEsD` | `PK` | Zip, Office doc, .jar, or .apk |
| `Rar!` | `Rar!` | RAR archive |
| `N3q8` | 7z magic | 7-Zip archive |
| `iVBOR` | PNG magic | PNG image |
| `/9j/` | JPEG magic | JPEG image |
| `R0lG` | `GIF8` | GIF image |
| `JVBER` | `%PDF` | PDF document |
| `data:` | literal | A data URI (base64 usually follows `base64,`) |
| `eyJ` | `{"` | JSON, and a JWT if it has two dots |

## Signal from absence

The prefixes are useful even when they *don't* appear. In the After Hours room,
the payload had no `H4sI` (no gzip header) and no `TVqQ` (no `MZ`), which is how I
knew it was raw-deflated and compressed before encoding, and therefore needed
`zlib.decompress(..., -15)` (raw deflate, no header) rather than a gzip step.

## Two commands that pair with this table

```
# find base64 blobs of 200+ chars anywhere in a file
strings -el FILE | grep -oE '[A-Za-z0-9+/]{200,}={0,2}' | sort -u
```

`strings -el` reads UTF-16 (two bytes per character), which plain `strings` skips.
Essential on any Windows artifact.

```
# decode UTF-16LE PowerShell (the JAB case)
echo 'JAB...' | base64 -d | iconv -f UTF-16LE -t UTF-8
```
