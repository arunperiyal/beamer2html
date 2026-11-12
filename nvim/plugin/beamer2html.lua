-- beamer2html.nvim: commands and tex-buffer mappings. See :help beamer2html.
if vim.g.loaded_beamer2html then return end
vim.g.loaded_beamer2html = true

local t = function() return require("beamer2html") end
local cmd = vim.api.nvim_create_user_command

cmd("Beamer2Html", function() t().build() end, { desc = "beamer2html: build slides.html" })
cmd("Beamer2HtmlWatch", function() t().watch_toggle() end, { desc = "beamer2html: watch on/off" })
cmd("Beamer2HtmlStop", function() t().watch_stop() end, { desc = "beamer2html: stop watching" })
cmd("Beamer2HtmlOpen", function() t().open() end, { desc = "beamer2html: open deck at cursor" })
cmd("Beamer2HtmlSync", function() t().sync(false) end, { desc = "beamer2html: move the deck to the cursor" })
cmd("Beamer2HtmlPack", function(o) t().pack(o.args) end,
    { nargs = "?", complete = "file", desc = "beamer2html: zip for presenting" })
cmd("Beamer2HtmlLog", function() t().log() end, { desc = "beamer2html: show the last output" })
cmd("Beamer2HtmlNew", function(o) t().new(o.args) end,
    { nargs = 1, complete = "dir", desc = "beamer2html: new deck from the template" })

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "tex", "plaintex" },
  group = vim.api.nvim_create_augroup("beamer2html", { clear = true }),
  callback = function(ev) t().buffer_setup(ev.buf) end,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  group = "beamer2html",
  callback = function()
    local s = package.loaded["beamer2html"] and require("beamer2html")._state
    if s and s.watch then vim.fn.jobstop(s.watch.id) end
  end,
})

-- snippets for the deck templates (frame, cols, rows, stab, lit, prog, ...),
-- when LuaSnip is installed
pcall(require, "beamer2html.snippets")
