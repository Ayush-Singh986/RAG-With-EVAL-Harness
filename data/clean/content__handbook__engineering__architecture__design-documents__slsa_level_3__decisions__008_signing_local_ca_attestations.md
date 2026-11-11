## Context

[ADR 007](/handbook/engineering/architecture/design-documents/slsa_level_3/decisions/007_attestations_private_dedicated_self_hosted/)
decided that attestations which can't use public Sigstore infrastructure are
signed by a certificate authority (CA) whose key is stored in PostgreSQL. We
call this the `LOCAL_CA` attest method. Each project has its own CA, and every
attestation is signed with a new key. A leaf certificate issued by the
project's CA binds that key to the project, the CI configuration file and the
ref.

This ADR records how we build that leaf certificate and how we sign with it.
The goal is for `LOCAL_CA` signing to work the same way on GitLab.com, GitLab
Dedicated and self-managed instances, including offline ones. On GitLab.com,
public projects use Sigstore by default, as described in ADR 007.

Two things about cosign shaped most of the decisions below. First, cosign v3
is built around a signing configuration. It reads the Sigstore services to use,
such as Fulcio, Rekor and timestamp authorities, from a signing configuration,
and uses the public Sigstore one if none is given. Older versions skipped the
transparency log with `--tlog-upload=false`. cosign v3 deprecates that flag in
favor of a signing configuration with no log, so that's what we pass, and we
don't use the flag. Second, cosign works with files, so the key, the
certificate, the trusted root and the signing configuration all have to be on
disk before cosign can use them.

## Decision

We sign each `LOCAL_CA` attestation with cosign, offline, using a new key and a
leaf certificate issued by the project's CA. The sections below go through each
part of that.

### Signing identity in a URI SAN

The leaf certificate has an empty subject and a single, critical URI Subject
Alternative Name (SAN). For example:

```plaintext
Subject: (empty)
X509v3 Subject Alternative Name: critical
    URI:https://gitlab.example.com/my-group/my-project//.gitlab-ci.yml@refs/heads/main
```

The URI is the pipeline's `ci_config_ref_uri`, prefixed with the instance's
protocol. GitLab generates this value, not the job, and it has the same format
as the `ci_config_ref_uri` claim in
[CI/CD ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/).

We put the identity in a URI SAN rather than the CN for a few reasons:

- The identity is a URI, and
  [RFC 5280 section 4.2.1.6](https://www.rfc-editor.org/rfc/rfc5280.html#section-4.2.1.6)
  defines the URI SAN for this purpose.
- It's what [Fulcio's certificate profile](https://github.com/sigstore/fulcio/blob/main/docs/certificate-specification.md#issued-certificate)
  does. cosign reads the identity from the SAN and doesn't fall back to the CN,
  so `cosign --certificate-identity` works on our certificates as they are.
- [RFC 5280 Appendix A.1](https://www.rfc-editor.org/rfc/rfc5280.html#appendix-A.1)
  limits a CN to 64 characters, and the example above is already 78.
- A URI inside a distinguished name has to be escaped when we issue the
  certificate and parsed carefully when we verify it. A typed SAN avoids that.

We always issue exactly one absolute URI in the SAN, and mark the extension
critical, as RFC 5280 requires when the subject is empty. The CN is never used
for the identity. Verifiers compare the SAN with an identity they work out for
themselves, never with a value read from the certificate itself.

The leaf certificate also carries the Fulcio issuer extension (OID
`1.3.6.1.4.1.57264.1.8`), set to the instance URL, for example
`https://gitlab.example.com`. No Fulcio server or OIDC exchange is involved.
GitLab sets the value itself, so verifiers can check it with
`--certificate-oidc-issuer` in the same way they do for Sigstore attestations.

### Long-lived leaf certificates

Leaf certificates are valid for several years, so an attestation stays
verifiable for several years after it's signed.

The certificate is stored in the attestation's Sigstore bundle, which GitLab
keeps with the attestation and users download with the
[Attestations API](https://docs.gitlab.com/api/attestations/). The private key
is ephemeral. We generate a new one for each attestation, use it once and
discard it, and it's never stored.

A CA only issues a leaf certificate if the CA itself stays valid for at least
the leaf certificate's lifetime.

### A new key and certificate for every attestation

We generate a new leaf key and certificate for every attestation, including one
for each artifact when a job produces several. A key signs one attestation and
is never reused.

The main benefit is that there's no long-lived signing key to store or protect.
The CA key is the only key that needs long-term protection. It also matches
Sigstore, which uses a new key for every signature, so both attest methods
behave the same from a user's point of view. And because each attestation
carries its own certificate, attestations don't depend on each other.

### Offline signing with an explicit signing configuration

We create a signing configuration with
[`cosign signing-config create`](https://github.com/sigstore/cosign/blob/main/doc/cosign_signing-config_create.md),
with no service flags, and pass it to cosign with `--signing-config`. The
configuration lists no transparency log and no timestamp authority:

```json
{"mediaType":"application/vnd.dev.sigstore.signingconfig.v0.2+json", "rekorTlogConfig":{}, "tsaConfig":{}}
```

We also unset `COSIGN_FULCIO_URL` and `COSIGN_REKOR_URL` for the
`cosign attest-blob` command. cosign reads `COSIGN_<FLAG>` variables as flags
and won't accept service URLs next to `--signing-config`, so a Sigstore URL set
on the host would otherwise break `LOCAL_CA` signing.

`LOCAL_CA` signing makes no network calls, so it works the same on an air-gapped
self-managed instance as on GitLab.com, and nothing about a private project
reaches a public log. If we later add a transparency log or timestamp authority
that GitLab runs, that's a change to the signing configuration rather than to
the signing flow.

### Certificate chain check at signing time

We build a trusted root that contains only the project's CA, with
[`cosign trusted-root create`](https://github.com/sigstore/cosign/blob/main/doc/cosign_trusted-root_create.md),
and pass it to `cosign attest-blob` with `--trusted-root`:

```shell
cosign trusted-root create \
  --fulcio 'url=https://gitlab.example.com,certificate-chain=ca.crt.pem' \
  --no-default-fulcio --no-default-rekor --no-default-ctfe --no-default-tsa \
  --out trusted-root.json
```

| Flag | Why |
|---|---|
| `--fulcio url=...,certificate-chain=...` | Adds the project's CA as the only certificate authority. The URL is the instance URL, the same value as the leaf certificate's issuer extension. |
| `--no-default-fulcio`, `--no-default-rekor`, `--no-default-ctfe`, `--no-default-tsa` | Leave out public Sigstore's certificate authority, transparency logs and timestamp authorities, so the trusted root contains nothing but the project's CA. |
| `--out` | Writes the trusted root next to the other signing material. |

cosign splits the `--fulcio` value on commas, so we reject a file path or
instance URL that contains one.

With the trusted root in place, cosign checks the leaf certificate against the
project's CA before it writes the bundle. A leaf certificate that doesn't chain
to that CA fails at signing time, so we never store an attestation that can't
be verified. Because the trusted root holds only the project's CA, a
certificate from public Sigstore or from another project's CA can't pass the
check. Signing and verification also use the same trust material in the same
format (ADR 009).

### Leaf certificate embedded in the bundle

We pass the leaf certificate to `cosign attest-blob` with `--certificate`, so
the Sigstore bundle carries it. This follows from the verification approach in
ADR 009, where cosign checks the certificate and the identity.

The bundle ends up self-contained: one file holds the signed provenance and the
certificate that ties it to an identity. We don't need a separate store or API
for leaf certificates or public keys, and `LOCAL_CA` bundles have the same
format as Sigstore bundles, so the same tools read both.

### Private, short-lived signing material

Because cosign works with files, we prepare the signing material for each
attestation like this:

- Each attestation gets its own new temporary directory, which only the
  operating system user running GitLab can open. It's deleted when signing
  finishes, whether signing succeeds or fails.
- The leaf key is converted to cosign's encrypted key format with
  [`cosign import-key-pair`](https://github.com/sigstore/cosign/blob/main/doc/cosign_import-key-pair.md).
  We write the plaintext key to cosign's standard input, so it never touches
  disk. The encrypted copy is protected by a random password generated for that
  one attestation.
- The password reaches cosign through its environment, not on the command line,
  where other users of the host could see it.
- The provenance reaches cosign on standard input, so it isn't written to disk
  either.
- cosign always runs directly from an argument list, never through a shell, and
  every value we pass to it, such as digests, file names and paths, is
  validated first. Sigstore signing uses the same pattern, which follows the
  [shell command development guidelines](https://docs.gitlab.com/development/shell_commands/).

Key material only exists while one attestation is being signed, in a directory
other users on the host can't read, and it's gone afterwards even when signing
fails.

### Signing method and issuing CA on every attestation

Every attestation records its `signing_method`, which is `sigstore` or
`local_ca`. A successful `LOCAL_CA` attestation also records
`signing_certificate_id`, a reference to the CA that issued its leaf
certificate.

Failed attestations record the method too, but no CA reference. Signing logs
include the method as well.

If a CA is ever deleted, its attestations keep their history, lose only the
reference, and still say `local_ca`. While its CA exists, every successful
`LOCAL_CA` attestation points at the CA that vouches for it, even when a project
has had more than one CA. A verifier can choose between the Sigstore and
`LOCAL_CA` verification paths from the attestation alone (ADR 009), and
failures can be grouped by method, so a problem with one path stands out.

## Certificate profile

Each leaf certificate has:

| Field | Value |
|---|---|
| Subject | Empty |
| Subject Alternative Name | One URI, critical |
| Issuer | The project's CA |
| Validity | Long-lived, see [Long-lived leaf certificates](#long-lived-leaf-certificates) |
| Public key | ECDSA P-256, new for each attestation |
| Signature | ECDSA with SHA-256, by the project's CA |
| Basic constraints | Not a CA |
| Key usage | Digital signature |
| Extended key usage | Code signing |
| `1.3.6.1.4.1.57264.1.8` | The instance URL |

The example below builds a leaf certificate with this profile. It continues
from the CA example in ADR 007, so run it in the same Ruby session. The
validity periods are only examples.

```ruby
require 'openssl'
require 'securerandom'

# ca_cert and ca_key come from the CA example in ADR 007.
# Example values, in seconds. The leaf certificate must expire before the CA.
leaf_validity = 3 * 365 * 24 * 60 * 60 # 3 years
clock_skew = 5 * 60 # 5 minutes, backdates not_before

identity = 'https://gitlab.example.com/my-group/my-project//.gitlab-ci.yml@refs/heads/main'
instance_url = 'https://gitlab.example.com'

leaf_key = OpenSSL::PKey::EC.generate('prime256v1')

leaf_cert = OpenSSL::X509::Certificate.new
leaf_cert.version = 2 # X.509 v3
leaf_cert.serial = SecureRandom.random_number(1...(2**159))
leaf_cert.not_before = Time.now - clock_skew
leaf_cert.not_after = Time.now + leaf_validity
leaf_cert.public_key = leaf_key
leaf_cert.subject = OpenSSL::X509::Name.new([])
leaf_cert.issuer = ca_cert.subject

extension_factory = OpenSSL::X509::ExtensionFactory.new
extension_factory.subject_certificate = leaf_cert
extension_factory.issuer_certificate = ca_cert

leaf_cert.add_extension(extension_factory.create_extension('basicConstraints', 'CA:FALSE', true))
leaf_cert.add_extension(extension_factory.create_extension('keyUsage', 'digitalSignature', true))
leaf_cert.add_extension(extension_factory.create_extension('extendedKeyUsage', 'codeSigning'))
leaf_cert.add_extension(extension_factory.create_extension('subjectKeyIdentifier', 'hash'))
leaf_cert.add_extension(extension_factory.create_extension('authorityKeyIdentifier', 'keyid:always'))

# Built as ASN.1, so the URI is never parsed as an OpenSSL config string.
san = OpenSSL::ASN1::Sequence.new([OpenSSL::ASN1::ASN1Data.new(identity, 6, :CONTEXT_SPECIFIC)])
leaf_cert.add_extension(OpenSSL::X509::Extension.new('subjectAltName', san.to_der, true))

issuer = OpenSSL::ASN1::UTF8String.new(instance_url)
leaf_cert.add_extension(OpenSSL::X509::Extension.new('1.3.6.1.4.1.57264.1.8', issuer.to_der, false))

leaf_cert.sign(ca_key, OpenSSL::Digest.new('SHA256'))
```

## Signing command

For each artifact or image digest, we get a new leaf key and certificate from
the project's CA, prepare the
[signing material](#private-short-lived-signing-material), and sign the
provenance:

```shell
cosign attest-blob \
  --new-bundle-format \
  --predicate - \
  --type slsaprovenance1 \
  --hash <SHA-256 digest> \
  --key cosign.key \
  --certificate leaf.crt.pem \
  --trusted-root trusted-root.json \
  --signing-config signing-config.json \
  --yes \
  --bundle attestation.bundle \
  -- ./<artifact name or digest>
```

| Flag | Why |
|---|---|
| `--key` | The leaf key, new for this attestation and in cosign's encrypted format. |
| `--certificate` | Embeds the leaf certificate in the bundle. |
| `--trusted-root` | Makes cosign check the leaf certificate against the project's CA before writing the bundle. |
| `--signing-config` | Keeps signing offline, with no transparency log and no timestamp authority. |
| `--predicate -` | Reads the SLSA provenance from standard input, so it isn't written to disk. |
| `--type slsaprovenance1` | Marks the predicate as SLSA provenance v1. |
| `--hash` | Signs the SHA-256 digest that GitLab computed, so cosign doesn't need to read the artifact. |
| `--new-bundle-format` | Writes a standard Sigstore bundle. |
| `--bundle` | Where cosign writes the bundle, which GitLab then stores with the attestation. |
| `--yes` | Skips cosign's confirmation prompt, because signing runs in the background. |
| `-- ./<name>` | The subject name in the provenance: the artifact's file name, or the image digest. The `--` and `./` stop a name from being read as a flag. |

Compared with Sigstore signing, `LOCAL_CA` replaces `--identity-token`,
`--oidc-issuer` and `--use-signing-config=false` with `--key`,
`--certificate`, `--trusted-root` and `--signing-config`. Everything else is
shared, so both methods produce the same kind of bundle from the same
provenance. We don't pass the job's CI/CD ID token to cosign for `LOCAL_CA`,
because the identity comes from the certificate GitLab issues.

## Consequences

### Positive

- `LOCAL_CA` signing works the same on GitLab.com, GitLab Dedicated and
  self-managed instances, including air-gapped ones, with no external service
  and no setup.
- Details of private projects don't reach a public log.
- Attestations are standard Sigstore bundles that cosign verifies with one
  trusted root, so users don't need any GitLab-specific tooling.
- cosign's existing identity checks work on `LOCAL_CA` certificates, because
  we follow Fulcio's certificate profile. Anyone who knows Sigstore will find
  the certificates familiar, and standard X.509 tools can read them.
- The CA key is the only long-lived secret. Leaf keys exist only while one
  attestation is being signed, and never leave a private, temporary directory.
- Each attestation is signed with its own key and certificate, so attestations
  don't depend on each other.
- Mistakes surface at signing time, through the chain check, instead of when a
  user tries to verify.
- Every attestation can be traced to the method that signed it, and every
  successful `LOCAL_CA` attestation to the CA that issued its certificate,
  while that CA exists.

### Negative

- An attestation verifies only until its leaf certificate expires. Keeping it
  verifiable for longer would need re-signing. A leaked leaf key or CA key
  could also produce certificates that verify until they expire. Short-lived
  leaf certificates would reduce both (see
  [Future considerations](#future-considerations)).
- A CA must outlive every leaf certificate it issues, so it stops issuing well
  before its own expiry and has to be replaced before then. Key rotation is out
  of scope for ADR 007 and this ADR.
- Each artifact needs a few extra local cosign commands, the encrypted leaf key
  is briefly on local disk, bundles are slightly larger, and signing relies on
  cosign v3.

### Future considerations

As a follow-up, we want to move to short-lived leaf certificates, paired with a
trusted signing time from a timestamp authority (TSA,
[RFC 3161](https://www.rfc-editor.org/rfc/rfc3161.html)) or a transparency log.
Verifiers would then check that the certificate was valid when the attestation
was signed, rather than when it's verified. This would:

- Limit how long a leaked leaf key stays useful.
- Let the CA lifetime shrink too.
- Keep attestations signed after the change verifiable once their leaf
  certificates expire.

It needs a TSA or log that self-managed and Dedicated instances can run, so
we'll pick it up together with the transparency log decision in ADR 007.

## Alternatives considered

### Identity in the subject CN

The identity could go in the CN, as `/CN=<identity>/DC=gitlab`. But the
identity is a URI that's usually longer than a CN allows, it would need
escaping inside the distinguished name, and cosign doesn't read identities from
the CN, so its identity checks wouldn't work.

### Skipping the transparency log with `--tlog-upload=false`

This is the older way to sign without Rekor, and it's deprecated in cosign v3.
It also leaves cosign's other defaults in place, and in that mode cosign signs
without checking the certificate chain at all. A signing configuration on its
own isn't enough either: without `--trusted-root`, cosign checks the leaf
certificate against public Sigstore's trust root, which doesn't contain the
project's CA. We pass a signing configuration with no log and a trusted root
with only the project's CA instead.

### Storing the public key with the attestation

We could store the leaf's public key with the attestation, verify the
signature with `cosign --key`, and check the certificate separately. That needs
separate storage and an API for keys or certificates, and certificate checks
that GitLab would own. Embedding the certificate avoids both. ADR 009 compares
the two verification approaches.

### Inferring the signing method

We could infer the method from whether an attestation references a CA, but
deleting a CA clears that reference, and its attestations would then look like
Sigstore ones. We could also read it from the certificate in the bundle, but
that needs every bundle to be downloaded and parsed, so it can't be queried.
Recording the method explicitly avoids both problems.

## References

- [ADR 007: Attestations for private repositories, GitLab dedicated and self-managed instances](/handbook/engineering/architecture/design-documents/slsa_level_3/decisions/007_attestations_private_dedicated_self_hosted/)
- [cosign attest-blob](https://github.com/sigstore/cosign/blob/main/doc/cosign_attest-blob.md)
- [cosign import-key-pair](https://github.com/sigstore/cosign/blob/main/doc/cosign_import-key-pair.md)
- [cosign signing-config create](https://github.com/sigstore/cosign/blob/main/doc/cosign_signing-config_create.md)
- [cosign trusted-root create](https://github.com/sigstore/cosign/blob/main/doc/cosign_trusted-root_create.md)
- [Fulcio certificate specification](https://github.com/sigstore/fulcio/blob/main/docs/certificate-specification.md)
- [RFC 5280: Internet X.509 Public Key Infrastructure Certificate and CRL Profile](https://www.rfc-editor.org/rfc/rfc5280.html)
- [Shell command development guidelines](https://docs.gitlab.com/development/shell_commands/)
- [Sigstore: Trusted time](https://blog.sigstore.dev/trusted-time/)
