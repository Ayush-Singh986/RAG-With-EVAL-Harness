## Overview

A validity check asks a vendor's API whether a detected secret is still active. For most vendors,
no hand-written code is needed. A YAML definition describes the vendor's verification endpoint, and
the generator produces the client class and its spec from it.

This page covers adding one vendor: research, definition, generation, live-token testing, and review.
A finding is routed to its check by the id of the detection rule that matched it. The rule itself is
covered by the [rule development process](rule-development-process).

Prerequisites:

- A detection rule for the token type exists in
  [secret-detection-rules](https://gitlab.com/gitlab-org/security-products/secret-detection/secret-detection-rules).
- The vendor has an authenticated endpoint that returns different status codes for an active token and
  a revoked token.

If either prerequisite is missing, see [when the generator is not enough](#when-the-generator-is-not-enough).

## 1. Research the vendor

Record the source for each answer. The answers go in the MR description in step 5.

- Rule id: the exact `id` from the rule's TOML file, including case and spaces. The registry routes on
  this value, so a mismatch means the check never runs. A vendor with several token types needs one
  definition per rule id.
- Endpoint: the cheapest authenticated call that works without any scope. Account or "who am I"
  endpoints usually qualify. Do not use endpoints that create or modify data, incur charges, or record
  analytics. For example, a list endpoint that counts a view on every returned item is not suitable.
- Auth style: how the token is sent. Supported values:
  - `bearer`: `Authorization: Bearer <token>`.
  - `header`: a custom header named in `auth_param`, with an optional scheme in `auth_prefix`.
  - `basic_username`: HTTP basic auth with the token as the username.
  - `basic_password`: HTTP basic auth with the token as the password and a fixed username in `auth_param`.
- Status codes: the code for an active token, the code for a revoked token, and the code for an active
  token with limited scopes. Send a well-formed but invalid token with curl and record the code. Map a
  code only when it always means the same outcome. Unmapped codes resolve to `unknown`.
- Regional hosts and self-hosted editions: if the vendor runs per-region APIs, or a self-hosted edition
  uses the same token format, an active token can receive `401` from the wrong host. Test the
  cross-region case. If `401` then has to map to `unknown` and no other code means revoked, the
  generator rejects the definition. See [when the generator is not enough](#when-the-generator-is-not-enough).
- Rate limits: the vendor's documented limit, and whether verification calls count against the token
  owner's quota.

## 2. Write the definition

Create `ee/lib/security/secret_detection/partner_tokens/generator/definitions/<vendor>.yml`. The
[example definition](https://gitlab.com/gitlab-org/gitlab/-/blob/master/ee/lib/security/secret_detection/partner_tokens/generator/examples/example_vendor.yml)
documents every field. `VendorDefinition` rejects unsafe or incomplete definitions when the generator runs.

```yaml
---
token_type: "Acme API token"              # the rule id, verbatim
class_name: "AcmeClient"
partner_name: "acme"                      # metrics label, lowercase; optional, derived from class_name
endpoint: "https://api.acme.dev/v1/whoami"
http_method: "get"
auth_style: "bearer"
# For a scheme in front of the token, such as "Authorization: AccessKey <token>":
# auth_style: "header"
# auth_param: "Authorization"
# auth_prefix: "AccessKey "
token_pattern: '\Aacme_[a-z0-9]{20}\z'   # anchored, same shape as the rule regex
sample_token: "acme_aaaaaaaaaaaaaaaaaaaa"   # filler that matches token_pattern
rate_limit_key: "partner_acme_api"
doc_url: "https://docs.acme.dev/api/authentication"
# Fixed headers the vendor needs on every request. Quote the values.
# extra_headers:
#   Acme-Version: "2024-01-01"
status_map:
  "200": "active"
  "401": "inactive"
  "429": "rate_limit"
  "500": "network_error"
  "502": "network_error"
  "503": "network_error"
  "504": "network_error"
```

Rules for the definition:

- `sample_token` must match `token_pattern`. It also matches the detection rule, which is expected.
  The definitions directory and the client specs are allowlisted in `config/gitleaks.toml`.
- If an active token with limited scopes can receive `403`, map `403` to `unknown` explicitly. The
  generator then emits a spec example for it. Map `403` to `active` only after confirming that a revoked
  token receives `401` and an active unscoped token receives `403`.
- Token types that share an endpoint share one `rate_limit_key` and one `partner_name`.

## 3. Generate and wire up

```shell
bundle exec rake "gitlab:secret_detection:validity_checks:generate[ee/lib/security/secret_detection/partner_tokens/generator/definitions/<vendor>.yml]"
```

To regenerate after editing the YAML, set `FORCE=true`. The task prints the registry entry and the
remaining manual steps:

1. Add the entry to `PARTNERS` in `ee/lib/security/secret_detection/partner_tokens/registry.rb`.
1. Add the same entry to the three tables in `ee/spec/services/security/secret_detection/partner_tokens/registry_spec.rb`.
1. Add a `partner_<vendor>_api` rule in `ee/lib/ee/gitlab/application_rate_limiter/labkit_adapter/supported_rate_limits.rb`.
   Use 50 requests per minute per project unless the vendor's limit is lower.
1. Add the token type, and the endpoint URL if it is new, to `doc/user/application_security/vulnerabilities/validity_check.md`.
   Keep alphabetical order and use the vendor's own product naming.

Do not edit a generated client or spec by hand. `generated_client_sync_spec.rb` regenerates every
definition and fails if the committed files differ. Run:

```shell
bundle exec rspec ee/spec/lib/security/secret_detection/partner_tokens/<vendor>_client_spec.rb \
  ee/spec/services/security/secret_detection/partner_tokens/registry_spec.rb \
  ee/spec/lib/security/secret_detection/partner_tokens/generator/generated_client_sync_spec.rb
```

## 4. Test with a live token

Reviewers expect the `active` path confirmed with a real token before the MR is marked ready. Vendor
documentation alone is not sufficient.

Create the vendor account:

- Register with the team's shared mailbox, `secrets@gitlab.com`, so teammates can reset the password.
- Generate the password in 1Password. Save the login to the Engineering vault with the vendor name, the
  email used, and the validity check it supports. If the vendor requires two-factor auth, save the TOTP
  secret and recovery codes in the same item.
- If the vendor has no email registration, sign in with a GitHub account created the same way, or use a
  passkey saved to the shared vault.
- If the vendor requires a payment method or a restricted email domain, ask in the team channel before
  paying. A teammate may already have access.

Create a token with the smallest scope offered. A read-only or unrelated scope proves the endpoint needs
no specific permission. Then:

```shell
read -s TOKEN
curl -sS -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" https://api.example.com/v1/me
```

Expect the `active` code. Revoke the token in the vendor UI and repeat the request. Expect the `inactive`
code. Adjust the header for the auth style. For POST endpoints, add `-d ''`, because some vendors return
`411` to a curl request without a body. The generated client sends `Content-Length: 0`, so it is unaffected.

If you cannot obtain a token, state this in the MR. Only unmapped codes resolve to `unknown`. If the
vendor returns `200` for some revoked tokens, a `200: active` mapping reports them as active. The reviewer
decides whether documentation alone is enough evidence for this vendor.

Revoke or delete the test token when done. Keep the account.

## 5. Open the MR

Use one commit per vendor. Commit subject: `Add a validity check for <Vendor> <token type>`. Commit body:
`Changelog: added` and `EE: true`. If secret push protection blocks the push because the sample token
matches a blocking rule, add `[skip secret push protection]` to the commit body and push again. Do not add
it by default. Open the MR as `Draft: [skip ci]` until the live test is done. Then remove both markers from
the title and select **Run pipeline** on the **Pipelines** tab of the MR.

MR description sections:

- Verification: the status code for the invalid token, and the status codes for the live token before and
  after revocation.
- Notes: why this endpoint was chosen, every non-default status mapping and its source, token types left
  out and why, regional or self-hosted caveats, and the vendor's rate limit.
- `Resolves <full issue URL>`.

Assign a Secret Detection reviewer. Each push to the branch resets approvals, so finish all fixes before
requesting final approval.

## Reviewer checklist

These points have come up in review on recent vendor MRs. Check them before opening the MR.

- The token type matches a rule id exactly. The MR covers every rule id for the vendor that the endpoint
  can verify, and lists the ones it cannot verify, such as publishable keys, refresh tokens, or auth keys,
  with the reason.
- `token_pattern` matches the character set and length of the rule regex.
- No code maps to `inactive` unless an active token can never produce it. An active token with limited
  scopes receiving `403`, a wrong region, or a self-hosted edition must not resolve to `inactive`.
- Codes discussed in the MR description have explicit `unknown` entries, so the spec pins them.
- The endpoint does not create data, charge the account, or consume quota the token owner would notice.
  If it consumes quota, the user docs say so.
- The docs entry and MR title use the vendor's product naming and cover renamed credential types.
- The rate-limit key appears in the YAML, the registry, the registry spec, and the rate-limit rules.
- `doc_url` resolves and describes the endpoint used.

## When the generator is not enough

The generator rejects a definition that can never produce `inactive`. Write the client by hand when:

- The verdict depends on the response body, because the vendor returns the same status code for a revoked
  token and for some active tokens.
- The vendor needs a request body or query-parameter auth. These are tracked as generator capability
  issues under [#631759](https://gitlab.com/gitlab-org/gitlab/-/work_items/631759).
- The vendor runs region-split hosts. Generator support is tracked in
  [#631945](https://gitlab.com/gitlab-org/gitlab/-/work_items/631945).
- Verification needs more than one captured value, such as a key id and secret pair. This is tracked in
  the [multi-part token spike](https://gitlab.com/gitlab-org/gitlab/-/work_items/631961).

A hand-written client extends `BaseClient`, keeps the fallback where unmapped codes resolve to `unknown`,
and includes the `a partner token client` shared examples. Remove the generated header comment and the
YAML definition so the sync spec ignores the client, and explain why in a short comment at the top of the
class.

## References

- [Validity checks design document](/handbook/engineering/architecture/design-documents/secret_detection_validity_checks/) and
  [ADR 006](/handbook/engineering/architecture/design-documents/secret_detection_validity_checks/decisions/006_map_token_types_directly_to_verifiers/)
- [Parity assessment](https://gitlab.com/gitlab-org/gitlab/-/work_items/631759) listing every rule and whether it is verifiable today
- [Validity checks troubleshooting runbook](runbooks/secret-detection-validity-check-troubleshooting)
