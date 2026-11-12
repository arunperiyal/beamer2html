-- beamer2html.nvim -- build, watch, open and sync beamer2html decks in Neovim.
-- See :help beamer2html.

local M = {}

-- repository root: this file is <repo>/nvim/lua/beamer2html/init.lua
local REPO = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h:h:h")

M.config = {
  python = "python3",
  tool = REPO,                -- path given to python: the beamer2html package folder
  main = nil,                 -- main .tex file; nil = found automatically
  output = "slides.html",
  browser = nil,              -- command to open the deck; nil = xdg-open / open
  autosync = false,           -- while watching, follow the cursor in the browser
  mappings = true,            -- <localleader>m... in tex buffers
}

local state = { watch = nil, log = {}, qf = {}, flush = nil, slides = 0, last_goto = nil }

local function notify(msg, level)
  vim.notify(msg, level or vim.log.levels.INFO, { title = "beamer2html" })
end

-- ============================================================ project files

local function has_documentclass(file)
  local ok, lines = pcall(vim.fn.readfile, file, "", 60)
  if not ok then return false end
  for _, l in ipairs(lines) do
    if l:match("^%s*\\documentclass") then return true end
  end
  return false
end

-- The deck's main .tex file: g/b:beamer2html_main or setup{main}, the current
-- file if it has \documentclass, else main.tex in this folder or a parent.
function M.main_file()
  local set = vim.b.beamer2html_main or vim.g.beamer2html_main or M.config.main
  if set then return vim.fn.fnamemodify(set, ":p") end
  local cur = vim.api.nvim_buf_get_name(0)
  if cur:match("%.tex$") and has_documentclass(cur) then return cur end
  local dir = cur ~= "" and vim.fn.fnamemodify(cur, ":p:h") or vim.fn.getcwd()
  while dir and dir ~= "" do
    local cand = dir .. "/main.tex"
    if vim.fn.filereadable(cand) == 1 then return cand end
    local parent = vim.fn.fnamemodify(dir, ":h")
    if parent == dir then break end
    dir = parent
  end
  return nil
end

local function root_of(main) return vim.fn.fnamemodify(main, ":h") end

-- ============================================================ slide map
-- Walk the sources in document order (following \input / \include) and
-- record where each slide starts, as beamer2html numbers them: every frame and
-- every template slide (\SeminarTitleFrame, \OverviewFrame, ...).

local TEMPLATE_CMDS = {
  SeminarTitleFrame = true, ConferenceTitleFrame = true, OverviewFrame = true,
  ReferencesFrame = true, ThankYouFrame = true,
}

local function strip_comment(line)
  local out, i = {}, 1
  while i <= #line do
    local c = line:sub(i, i)
    if c == "\\" then
      table.insert(out, line:sub(i, i + 1)); i = i + 2
    elseif c == "%" then
      break
    else
      table.insert(out, c); i = i + 1
    end
  end
  return table.concat(out)
end

-- returns slides = { {file=, line=, col=}, ... }, pauses = { {file=, line=, col=}, ... }
function M.scan(main)
  local root = root_of(main)
  local slides, pauses, seen = {}, {}, {}
  local in_doc = false

  local function walk(path)
    local full = path:match("^/") and path or (root .. "/" .. path)
    if not full:match("%.tex$") then full = full .. ".tex" end
    if seen[full] or vim.fn.filereadable(full) == 0 then return end
    seen[full] = true
    for lnum, raw in ipairs(vim.fn.readfile(full)) do
      local line = strip_comment(raw)
      local events = {}
      for s, arg in line:gmatch("()\\input%s*{([^}]*)}") do table.insert(events, { s, "input", arg }) end
      for s, arg in line:gmatch("()\\include%s*{([^}]*)}") do table.insert(events, { s, "input", arg }) end
      for s in line:gmatch("()\\begin%s*{document}") do table.insert(events, { s, "document" }) end
      for s in line:gmatch("()\\begin%s*{frame}") do table.insert(events, { s, "slide" }) end
      for s, name in line:gmatch("()\\(%a+)") do
        if TEMPLATE_CMDS[name] then table.insert(events, { s, "slide" }) end
        if name == "pause" then table.insert(events, { s, "pause" }) end
      end
      table.sort(events, function(a, b) return a[1] < b[1] end)
      for _, e in ipairs(events) do
        if e[2] == "input" then
          walk(e[3])
        elseif e[2] == "document" then
          in_doc = true
        elseif in_doc and e[2] == "slide" then
          table.insert(slides, { file = full, line = lnum, col = e[1] })
        elseif in_doc and e[2] == "pause" then
          table.insert(pauses, { file = full, line = lnum, col = e[1], slide = #slides })
        end
      end
    end
  end

  walk(main)
  return slides, pauses
end

-- Slide (1-based) and step under the cursor, or nil.
function M.cursor_slide(main)
  local slides, pauses = M.scan(main)
  local file = vim.fn.fnamemodify(vim.api.nvim_buf_get_name(0), ":p")
  local cur = vim.api.nvim_win_get_cursor(0)
  local before = function(p) return p.line < cur[1] or (p.line == cur[1] and p.col <= cur[2] + 1) end
  local slide
  for i, s in ipairs(slides) do
    if s.file == file and before(s) then slide = i end
  end
  if not slide then                        -- before the first slide of this file
    for i, s in ipairs(slides) do
      if s.file == file then slide = i; break end
    end
  end
  if not slide then return nil end
  local step = 0                           -- \pause's of this slide above the cursor
  for _, p in ipairs(pauses) do
    if p.slide == slide and p.file == file and before(p) then step = step + 1 end
  end
  return slide, step
end

-- ============================================================ jobs & output

local function tool_cmd(main, extra)
  local cmd = { M.config.python, "-u", M.config.tool, vim.fn.fnamemodify(main, ":t"),
                "-o", M.config.output }
  vim.list_extend(cmd, extra or {})
  return cmd
end

-- 'warning: slide 5 "Title": message' -> quickfix item at that slide
local function qf_item(text, main)
  local n, msg = text:match('^warning: slide (%d+) "[^"]*": (.*)$')
  if n then
    local s = M.scan(main)[tonumber(n)]
    if s then return { filename = s.file, lnum = s.line, col = s.col, text = msg, type = "W" } end
  end
  local w = text:match("^warning: (.*)$") or text
  local file = w:match("\\input{([^}]*)}")
  return { filename = file and (root_of(main) .. "/" .. file .. ".tex") or nil,
           lnum = 1, text = w, type = text:match("^warning") and "W" or "E" }
end

local function set_qf(main, items)
  vim.fn.setqflist({}, "r", { title = "beamer2html", items = items })
  state.qf = items
end

-- Collect a build's output: "wrote ... (N slides)" starts a build, the
-- warning lines that follow belong to it; shown shortly after the last one.
local function on_line(main, line)
  line = line:gsub("\r", "")
  if line == "" then return end
  table.insert(state.log, line)
  local n = line:match("wrote .- %((%d+) slides%)")
  if n then
    state.slides = tonumber(n)
    state.pending = {}
  elseif line:match("^warning:") then
    state.pending = state.pending or {}
    table.insert(state.pending, qf_item(line, main))
  elseif line:match("build failed") then
    notify((line:gsub("^%[[%d:]+%] ", "")), vim.log.levels.ERROR)
    return
  elseif line:match("^packed ") then
    notify(line)
    return
  else
    return
  end
  if state.flush then state.flush:stop() end
  state.flush = vim.defer_fn(function()
    local items = state.pending or {}
    set_qf(main, items)
    local w = #items > 0 and (", %d warning%s -- :copen"):format(#items, #items == 1 and "" or "s") or ""
    notify(("%d slides%s"):format(state.slides, w), #items > 0 and vim.log.levels.WARN or nil)
    vim.cmd("redrawstatus")
  end, 150)
end

local function run(main, extra, opts)
  opts = opts or {}
  local buf = ""
  local function feed(_, data)
    if not data then return end
    data[1] = buf .. data[1]
    buf = table.remove(data)
    for _, l in ipairs(data) do vim.schedule(function() on_line(main, l) end) end
  end
  return vim.fn.jobstart(tool_cmd(main, extra), {
    cwd = root_of(main),
    on_stdout = feed, on_stderr = feed,
    on_exit = function(_, code)
      vim.schedule(function()
        if buf ~= "" then on_line(main, buf); buf = "" end
        if opts.on_exit then opts.on_exit(code) end
      end)
    end,
  })
end

local function need_main()
  local main = M.main_file()
  if not main then
    notify("no main .tex file found (set g:beamer2html_main or open main.tex)", vim.log.levels.ERROR)
  end
  return main
end

-- ============================================================ commands

function M.build()
  local main = need_main(); if not main then return end
  vim.cmd("silent! wall")
  state.log = {}
  run(main, {}, { on_exit = function(code)
    if code ~= 0 then notify("build failed -- :Beamer2HtmlLog", vim.log.levels.ERROR) end
  end })
end

function M.watch_start()
  if state.watch then notify("already watching " .. state.watch.main); return end
  local main = need_main(); if not main then return end
  state.log = {}
  local id = run(main, { "--watch" }, { on_exit = function()
    state.watch = nil
    vim.cmd("redrawstatus")
  end })
  if id <= 0 then notify("could not start beamer2html", vim.log.levels.ERROR); return end
  state.watch = { id = id, main = main }
  notify("watching " .. vim.fn.fnamemodify(main, ":~:."))
  vim.cmd("redrawstatus")
end

function M.watch_stop()
  if not state.watch then notify("not watching"); return end
  vim.fn.jobstop(state.watch.id)
  state.watch = nil
  notify("stopped watching")
  vim.cmd("redrawstatus")
end

function M.watch_toggle()
  if state.watch then M.watch_stop() else M.watch_start() end
end

function M.pack(dest)
  local main = need_main(); if not main then return end
  vim.cmd("silent! wall")
  local extra = { "--pack" }
  if dest and dest ~= "" then table.insert(extra, vim.fn.fnamemodify(dest, ":p")) end
  run(main, extra)
end

local function open_url(url)
  local cmd = M.config.browser
  if not cmd then cmd = vim.fn.has("mac") == 1 and "open" or "xdg-open" end
  vim.fn.jobstart({ cmd, url }, { detach = true })
end

local function deck_path(main) return root_of(main) .. "/" .. M.config.output end

-- open the deck in the browser at the slide under the cursor
function M.open()
  local main = need_main(); if not main then return end
  local deck = deck_path(main)
  if vim.fn.filereadable(deck) == 0 then
    notify(M.config.output .. " not built yet -- :Beamer2Html", vim.log.levels.WARN); return
  end
  local slide, step = M.cursor_slide(main)
  local hash = slide and ("#" .. slide .. (step > 0 and ("." .. step) or "")) or ""
  open_url("file://" .. deck .. hash)
end

-- move the open deck to the slide under the cursor (needs :Beamer2HtmlWatch)
function M.sync(quiet)
  local main = (state.watch and state.watch.main) or need_main(); if not main then return end
  if not state.watch then
    if not quiet then notify("sync needs :Beamer2HtmlWatch (the deck must be built in watch mode)", vim.log.levels.WARN) end
    return
  end
  local slide, step = M.cursor_slide(main)
  if not slide then return end
  local key = slide .. "." .. step
  if quiet and key == state.last_goto then return end
  state.last_goto = key
  local stamp = tostring(vim.uv.hrtime())
  vim.fn.writefile({ ("window.TEX2HTML_GOTO = { slide: %d, step: %d, t: %q };"):format(slide, step, stamp) },
                   root_of(main) .. "/html/goto.js")
  if not quiet then notify(("deck -> slide %d%s"):format(slide, step > 0 and (", step " .. step) or "")) end
end

function M.log()
  vim.cmd("botright new")
  local b = vim.api.nvim_get_current_buf()
  vim.bo[b].buftype, vim.bo[b].bufhidden, vim.bo[b].swapfile = "nofile", "wipe", false
  vim.api.nvim_buf_set_name(b, "beamer2html://log")
  vim.api.nvim_buf_set_lines(b, 0, -1, false, #state.log > 0 and state.log or { "(no output yet)" })
  vim.bo[b].modifiable = false
end

-- copy the starter template to `dir` and open its main.tex
function M.new(dir)
  if not dir or dir == "" then notify("usage: :Beamer2HtmlNew {directory}", vim.log.levels.ERROR); return end
  dir = vim.fn.fnamemodify(dir, ":p"):gsub("/$", "")
  if vim.fn.isdirectory(dir) == 1 and #vim.fn.readdir(dir) > 0 then
    notify(dir .. " exists and is not empty", vim.log.levels.ERROR); return
  end
  vim.fn.mkdir(vim.fn.fnamemodify(dir, ":h"), "p")
  local out = vim.fn.system({ "cp", "-r", REPO .. "/template", dir })
  if vim.v.shell_error ~= 0 then notify("copy failed: " .. out, vim.log.levels.ERROR); return end
  vim.cmd("edit " .. vim.fn.fnameescape(dir .. "/main.tex"))
  notify("new deck in " .. vim.fn.fnamemodify(dir, ":~"))
end

-- statusline component: "beamer2html: watching" while --watch runs
function M.status()
  return state.watch and "beamer2html: watching" or ""
end

-- ============================================================ setup

function M.setup(opts)
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})
end

function M.buffer_setup(buf)
  if M.config.mappings then
    local map = function(lhs, fn, desc)
      vim.keymap.set("n", "<localleader>m" .. lhs, fn, { buffer = buf, desc = "beamer2html: " .. desc })
    end
    map("b", M.build, "build slides.html")
    map("w", M.watch_toggle, "watch on/off")
    map("o", M.open, "open deck at cursor")
    map("s", function() M.sync(false) end, "sync deck to cursor")
    map("p", function() M.pack() end, "pack zip")
    map("l", M.log, "show log")
  end
  if M.config.autosync then
    vim.api.nvim_create_autocmd("CursorHold", {
      buffer = buf, callback = function() M.sync(true) end,
    })
  end
end

M._state = state
return M
