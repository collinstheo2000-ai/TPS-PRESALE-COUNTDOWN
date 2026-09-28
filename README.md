# Email countdown timer for Mailchimp

A tiny web service that draws a countdown GIF every time an email is opened. Hosting it on Vercel is free.

## 1. Deploy (about 5 minutes)
1. Create a free account at vercel.com (signing in with GitHub is easiest).
2. Put this folder in a GitHub repo, or install the Vercel CLI and run `vercel` inside this folder.
3. In Vercel, click **Add New → Project**, pick the repo and click **Deploy**. You don't need to change any settings.
4. You'll get a URL like `https://countdown-timer-xyz.vercel.app`.

Test it in a browser:
`https://YOUR-APP.vercel.app/api/countdown?end=2026-10-15T18:00:00Z`

## 2. Add to Mailchimp
Drag a **Code** block into your email and paste:

```html
<img src="https://YOUR-APP.vercel.app/api/countdown?end=2026-10-15T18:00:00%2B01:00"
     width="600" alt="Time left" style="display:block;max-width:100%;height:auto;margin:0 auto;">
```

To make the whole timer clickable, wrap it in `<a href="https://your-link">…</a>`.

## Options
Add any of these to the URL with `&`:

| Parameter | What it does | Example |
|---|---|---|
| `end` | Deadline (required). `Z` means UTC. For BST, use `%2B01:00` | `2026-10-15T18:00:00%2B01:00` |
| `theme` | Colour preset: `cream` (default), `midnight`, `punch`, `electric`, `blue` | `theme=punch` |
| `bg` | Background colour (default white, to match the email body) | `bg=ffffff` |
| `box` | Box gradient start (overrides the theme) | `box=c75ca5` |
| `box2` | Box gradient end (overrides the theme). Use `none` for solid boxes | `box2=none` |
| `fg` | Number colour (overrides the theme) | `fg=ffffff` |
| `label` | Label colour (overrides the theme) | `label=ffffff` |
| `endfg` | Colour of the text shown after the deadline (overrides the theme) | `endfg=ee8232` |
| `width` | Width in px, from 300 to 800 | `width=500` |
| `expired` | Text shown after the deadline (default PRESALE CLOSED) | `expired=SOLD%20OUT` |

All the presets use the TPS27 campaign palette, so usually you only need `end` and `theme`. The font is Space Grotesk (in `api/fonts`, under the SIL Open Font License).

## Good to know
- The timer ticks for 60 seconds and then holds. Every reopen redraws it with the correct time.
- Outlook desktop shows only the first frame. The time is still right, it just doesn't tick.
- UK clocks go back on 25 Oct 2026. For deadlines after that date, use `Z` or `%2B00:00`, not `%2B01:00`.
