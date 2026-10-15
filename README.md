# Asyntai AI Chatbot for Quarto

Add the [Asyntai](https://asyntai.com) AI chat assistant to your Quarto
website, book, blog or slides. It answers reader questions from your own
content, day and night.

Works with every HTML format: websites, books, blogs, single documents,
reveal.js slides and dashboards. PDF, Word and other formats are left as they
are.

## Install

Run this in your project folder:

```bash
quarto add asyntai/quarto-ai-chatbot
```

Then add the filter and your widget ID to `_quarto.yml`:

```yaml
filters:
  - ai-chatbot

asyntai:
  widget-id: asyntai_1a2b3c4d5e6f
```

Render the project. The chat bubble is on every page.

For a single document, put the same lines in its front matter:

```yaml
---
title: My report
format: html
filters:
  - ai-chatbot
asyntai:
  widget-id: asyntai_1a2b3c4d5e6f
---
```

## Where the widget ID comes from

Open the Install page in your [Asyntai dashboard](https://asyntai.com/dashboard).
The widget ID is the value of `data-asyntai-id` in the snippet shown there. It
starts with `asyntai_`.

Creating an account is free, and the Free plan is enough to try the widget.

## Options

All options go under `asyntai:`.

| Option | Type | Default | What it does |
| --- | --- | --- | --- |
| `widget-id` | string | required | Your Asyntai widget ID |
| `enabled` | boolean | `true` | Set to `false` to keep the widget off |
| `script-url` | string | the Asyntai CDN | Advanced. Load the widget from another URL |

A page can turn the widget off in its own front matter:

```yaml
---
title: Internal notes
asyntai:
  enabled: false
---
```

A missing or malformed `widget-id` prints an error line that says how to fix
it, and that page gets no widget.

## What the extension does

- It adds one `async` script tag at the end of every HTML page, so your content
  renders first.
- The 404 page and blog listing pages get the chat too.
- With `embed-resources: true`, the page still loads the widget from the
  Asyntai CDN, so it always runs the current version.
- It changes nothing else. No templates are overridden and no CSS is added.

Requires Quarto 1.4 or later.

## Answering from your content

Asyntai reads your published pages. Add your site URL in the dashboard, and the
assistant answers from the same pages the widget sits on. You can also add
documents, and question and answer pairs.

## Removing it

Delete `ai-chatbot` from `filters` and render again. The widget is gone.

## Support

Email [hello@asyntai.com](mailto:hello@asyntai.com), or read the
[Quarto guide](https://asyntai.com/documentation/integrations/quarto/).

## Licence

MIT. See [LICENSE](LICENSE).
