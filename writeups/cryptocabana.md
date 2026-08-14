# CryptoCabana

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-04
**Tags:** Cloud, Azure, Storage, Key Vault, SAS

## The target

An Azure environment: a "CryptoCabana" seed-phrase backup kiosk, served as an
Azure Storage static website, backed by Azure Key Vault. I was handed a
low-privilege Azure user login. The objective was to recover the real secret the
kiosk was supposed to keep behind glass.

This was my first time working in Azure, coming off the AWS Complimentary box, so
I treated the cloud-agnostic instincts as the constant and learned Azure's
specifics as I went.

## What I tried

I enumerated as my own user first: `az resource list`, `az storage account list`,
`az keyvault list`. All three came back empty. That was the tell, not a dead end:
my user had no management-plane (ARM) rights, so the way in was never "enumerate
as myself." It was "what does the kiosk itself trust to reach into storage?"

So I read the kiosk's front-end, view-source then its `app.js`, the same move I
used on the AWS Complimentary box. It hardcoded a Storage Shared Access Signature
(SAS) token. Decoding the token told the whole story: blob service, resource types
service plus container plus object, permissions read and list, expiring years in
the future. The app only ever needed to *write* a backup, yet the token granted
*read and list across the entire storage account*. An over-permissioned,
client-side credential.

## What worked

With that SAS I listed the account's containers: `$web`, `backups`, and `vault`.
The page never mentioned `vault`. Inside it were two blobs: a service principal
credential file (client id, secret, tenant, and the Key Vault's name) and a decoy
seed phrase.

I logged in as that service principal, which held the Key Vault access my user
lacked, and listed its secrets: three "key shards" and a master key. Shards one
and three were the outer pieces of the answer. Shard two's *current* value was a
note admitting it had been rotated. Azure Key Vault keeps every version of a
secret, and rotation supersedes rather than deletes, so I listed shard two's
versions and read the older one. That was the real middle piece.

The trust chain end to end: a leaked SAS token, to storage, to a stolen service
principal, to Key Vault, to an old secret version.

## Finding & fix

**Finding:** a hardcoded, over-permissioned SAS token in public JavaScript exposed
read and list over an entire storage account. That storage held a service
principal's credentials, which unlocked a Key Vault whose "rotated" secret still
served its original value from version history.

**Fix:** never embed storage credentials in client-side code; scope SAS tokens to
least privilege (write only, a single container, short expiry) or route writes
through a backend. Never store credentials in reachable storage; use a managed
identity so there is no secret to steal. And treat rotation as insufficient for a
leaked secret: disable or delete old versions and revoke the value at source,
because Key Vault serves superseded versions by default.
