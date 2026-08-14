# After Hours

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-08
**Tags:** Windows, Forensics, WMI, Persistence, Fileless, .NET, Reverse Engineering

## The target

A resort back-office machine where something logs in during the small hours, well
after the night technician has gone home. The briefing is explicit that the usual
autoruns triage comes up empty: nothing in the Startup folder, Scheduled Tasks, or
the registry Run keys. No live host, no IP. The task files are five raw artifacts
plus a bundled copy of ILSpy, and the goal is a single flag: parse the artifacts,
find the malicious class, extract and decode its payload.

This was my first time reverse-engineering fileless malware and WMI persistence,
so I let the file formats tell me where to look before running anything.

## Reading the artifacts before touching them

The five files name the technique before you run anything. `OBJECTS.DATA`,
`INDEX.BTR`, and `MAPPING1-3.MAP` are the **WMI CIM repository**, normally at
`C:\Windows\System32\wbem\Repository\`. That single fact explains the whole
briefing: the persistence is a **WMI event subscription** (MITRE T1546.003), which
lives inside this binary database rather than in any of the three places autoruns
tools check. The itinerary's phrasing ("hidden custom configuration data," "the
malicious class") points at the same subsystem, since WMI is the one place an
attacker registers custom *classes* to hold data. And the room shipping ILSpy, a
.NET decompiler, told me before I started that the final payload would be a .NET
assembly, not the PowerShell one-liner these subscriptions usually carry.

## What I tried

The room's own hint said the autoruns tooling misses this and you have to "dig
through the raw data by hand," and there was deliberately no WMI parser in the
`tools/` folder. So the intended route was `strings`, not Mandiant's `python-cim`.

WMI stores its data as UTF-16, so a plain `strings` misses most of it. The key
flag throughout was `-el` (16-bit little-endian). First pass, the class names:

```
strings -el OBJECTS.DATA | grep -iE 'EventConsumer|EventFilter|ConsumerBinding' | sort -u
```

That returned only the abstract parent classes (`__EventConsumer`,
`__FilterToConsumerBinding`), which exist in every stock repository. No malicious
consumer yet, so I widened the search for the custom class:

```
strings -el OBJECTS.DATA | grep -iE 'consumer|persist|config' | sort -u | head -50
```

Amongst genuine Windows classes sat `SystemConfig` and `SystemConfig_V0` through
`_V4`. No such stock class exists, so that looked like the malicious object, and the
`_V0..V4` numbering looked like a payload split across five classes. **This was a
dead end, and an instructive one.** Chasing the offsets of those classes produced
dozens of hits that were index and reference noise, not payload. The `_V*` cluster
was a decoy.

## What worked

I stopped hunting class names and hunted the payload directly, since long
unbroken base64 does not occur naturally in a CIM repository:

```
strings -el OBJECTS.DATA | grep -oE '[A-Za-z0-9+/]{200,}={0,2}' | sort -u
```

Two blobs came back. One began `JAB`, which is the signature of base64-encoded
UTF-16LE PowerShell starting with `$` (worth memorising: blue teams alert on that
string alone). Decoding it revealed the actual command line, stored as the
consumer's `CommandLineTemplate`:

```
cmd /C powershell.exe -Sta -Nop -Window Hidden -enc JAB...
```

Decoding *that* inner blob (`base64 -d | iconv -f UTF-16LE -t UTF-8`) gave the
loader, and it named everything:

```powershell
$file = ([WmiClass]'ROOT\cimv2:Win32_HardwareTelemetry').Properties['ConfigData'].Value
# base64 -> DeflateStream Decompress -> Reflection.Assembly.Load -> EntryPoint.Invoke
```

So the real malicious class was **`Win32_HardwareTelemetry`**, not `SystemConfig`.
Far better tradecraft: a `Win32_` prefix and a plausible name, hiding in `root\cimv2`
amongst thousands of legitimate classes. The `ConfigData` property held a second
base64 blob, and nothing ever touches disk: the loader decodes it, decompresses it
with **raw deflate**, and reflectively loads the resulting .NET assembly straight
from memory. That also explained two earlier empty searches: no `H4sI` (gzip
header) because raw deflate has no header, and no `TVqQ` (`MZ`) because the PE was
compressed before encoding.

Extracting the `ConfigData` value and reversing the two operations recovered the
assembly:

```
python3 -c "import base64,zlib;open('payload.dll','wb').write(zlib.decompress(base64.b64decode(open('b64.txt').read().strip()),-15))"
```

The `-15` is the whole trick: a negative window size tells zlib to expect raw
deflate with no header, matching .NET's `DeflateStream`. `file` confirmed a
`PE32 Mono/.Net assembly` with `MZ` at byte zero. `strings` on it found no flag, so
the flag was built at runtime, and ILSpy decompiled the entry point to plain C#:
a machine-name guard (`bytelotusdc`, a domain controller) wrapping a
`net user <name> <base64> /add`. The flag was the account password, base64 again.

## Finding & fix

**Finding:** fileless persistence via a WMI permanent event subscription. A
`CommandLineEventConsumer` runs an encoded PowerShell loader that pulls a
compressed .NET assembly from the `ConfigData` property of a rogue
`Win32_HardwareTelemetry` class and loads it reflectively in memory. The assembly
is environment-gated (it only detonates on the target DC and prints "Environment
mismatch" elsewhere, defeating naive sandboxing) and creates a local account named
to look like maintenance. Nothing lands on disk and nothing appears in Startup,
Scheduled Tasks, or Run keys, which is exactly why the standard triage missed it.

**Fix:**
- **Monitor the subscription itself.** Alert on creation of `__EventFilter`,
  `__EventConsumer`, and `__FilterToConsumerBinding` objects (Sysmon events 19/20/21
  cover WMI subscriptions directly). This is the detection the room is teaching.
- **Alert on the behaviour, not the file.** `powershell -enc` with a hidden window,
  `[Reflection.Assembly]::Load`, and `DeflateStream` in script-block logs are all
  high-signal. Constrained Language Mode and PowerShell v5 script-block/transcription
  logging make this loader far noisier.
- **Treat new local accounts on a DC as an incident**, especially benign-looking
  names like `patch`.
- **Hunt custom WMI classes.** Legitimate classes are overwhelmingly `Win32_`,
  `CIM_`, `MSFT_`, or `__`-prefixed *and* documented; a `Win32_`-named class holding
  a large base64 property is not. Periodically baseline `root\cimv2` and
  `root\subscription`.

The lesson is that "no artifact on disk" is not "no artifact." The subscription, the
class, and the payload were all sitting in a binary repository file the whole time,
readable with `strings` once you know the file format is telling you where to look.
