-- Asyntai AI chatbot for Quarto.
--
-- Adds the Asyntai chat widget to every HTML page that Quarto renders:
-- websites, books, blogs, single documents, reveal.js slides and dashboards.
-- The filter writes the ordinary embed snippet after the body of the page.
-- PDF, Word and other non-HTML formats are left as they are.
--
-- Settings, in _quarto.yml or in the front matter of a document:
--
--   filters:
--     - ai-chatbot
--   asyntai:
--     widget-id: asyntai_1a2b3c4d5e6f
--     enabled: true          # optional, false keeps the widget off
--     script-url: https://... # optional, advanced

local DEFAULT_SCRIPT_URL = "https://widget.asyntai.com/static/js/chat-widget.js"

local function text(value)
  if value == nil then
    return ""
  end
  if type(value) == "boolean" then
    return tostring(value)
  end
  if type(value) == "string" then
    return value
  end
  return pandoc.utils.stringify(value)
end

local function escape_attr(value)
  return (value:gsub("&", "&amp;"):gsub('"', "&quot;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

local function is_disabled(value)
  if value == nil then
    return false
  end
  if type(value) == "boolean" then
    return not value
  end
  local s = text(value):lower()
  return s == "false" or s == "no" or s == "off" or s == "0"
end

-- Quarto prints an error and goes on with the render, so a wrong setting
-- shows a red ERROR line for each page and the page gets no widget.
local function fail(message)
  quarto.log.error("ai-chatbot: " .. message)
  return nil
end

-- data-external="1" stops Pandoc from copying the widget code into the page
-- when embed-resources is on. The page then always loads the current widget.
local function build_tag(widget_id, script_url)
  return '<script async src="' .. escape_attr(script_url)
    .. '" data-asyntai-id="' .. widget_id .. '" data-external="1"></script>'
end

function Meta(meta)
  -- Only formats that run JavaScript can show the widget.
  if not quarto.doc.is_format("html:js") then
    return nil
  end

  local settings = meta["asyntai"]
  if settings == nil then
    return fail('add your widget ID under "asyntai:" in _quarto.yml, '
      .. 'for example\n\nasyntai:\n  widget-id: asyntai_1a2b3c4d5e6f\n\n'
      .. 'Copy it from the Install page of your Asyntai dashboard.')
  end

  if is_disabled(settings["enabled"]) then
    return nil
  end

  local widget_id = text(settings["widget-id"]):gsub("^%s+", ""):gsub("%s+$", "")
  if widget_id == "" then
    return fail('"widget-id" is required. Copy it from the Install page '
      .. 'of your Asyntai dashboard, for example asyntai_1a2b3c4d5e6f.')
  end
  if not widget_id:match("^asyntai_[%w]+$") then
    return fail('"' .. widget_id .. '" does not look like a widget ID. '
      .. 'It starts with asyntai_, for example asyntai_1a2b3c4d5e6f.')
  end

  local script_url = text(settings["script-url"]):gsub("^%s+", ""):gsub("%s+$", "")
  if script_url == "" then
    script_url = DEFAULT_SCRIPT_URL
  end

  quarto.doc.include_text("after-body", build_tag(widget_id, script_url))
  return nil
end
