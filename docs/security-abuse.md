# Security And Abuse

## Reports

Reports never automatically hide or down-rank content. They create admin review priority only.

## Submissions

- Login required.
- Daily limit.
- Duplicate URL checks.
- AI first-pass review.
- Admin approval before publishing.

## Verified Reviews

- Login required.
- Purchase record or receipt/order image.
- AI first-pass review.
- Admin approval before `VERIFIED`.
- Only verified reviews are strong AI purchase-check evidence.

## Favorites

- `unique(user_id, target_type, target_id)`.
- Product, deal, and auction favorites are distinct targets.

## External URLs

- Validate URLs.
- Use allowlist/blocklist policy.
- Do not expose unapproved suspicious links.

## AI

- Rate-limit AI requests.
- Validate structured outputs.
- Never let AI approve publishing by itself.

## Admin

- Enforce `ADMIN` role.
- Keep audit logs for admin actions.
