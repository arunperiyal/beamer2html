-- tex2html.nvim: commands and tex-buffer mappings. See :help tex2html.
if vim.g.loaded_tex2html then return end
vim.g.loaded_tex2html = true

local t = function() return require("tex2html") end
local cmd = vim.api.nvim_create_user_command

cmd("Tex2Html", function() t().build() end, { desc = "tex2html: build slides.html" })
cmd("Tex2HtmlWatch", function() t().watch_toggle() end, { desc = "tex2html: watch on/off" })
cmd("Tex2HtmlStop", function() t().watch_stop() end, { desc = "tex2html: stop watching" })
cmd("Tex2HtmlOpen", function() t().open() end, { desc = "tex2html: open deck at cursor" })
cmd("Tex2HtmlSync", function() t().sync(false) end, { desc = "tex2html: move the deck to the cursor" })
cmd("Tex2HtmlPack", function(o) t().pack(o.args) end,
    { nargs = "?", complete = "file", desc = "tex2html: zip for presenting" })
cmd("Tex2HtmlLog", function() t().log() end, { desc = "tex2html: show the last output" })
cmd("Tex2HtmlNew", function(o) t().new(o.args) end,
    { nargs = 1, complete = "dir", desc = "tex2html: new deck from the template" })

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "tex", "plaintex" },
  group = vim.api.nvim_create_augroup("tex2html", { clear = true }),
  callback = function(ev) t().buffer_setup(ev.buf) end,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  group = "tex2html",
  callback = function()
    local s = package.loaded["tex2html"] and require("tex2html")._state
    if s and s.watch then vim.fn.jobstop(s.watch.id) end
  end,
})

-- snippets for the deck templates (frame, cols, rows, stab, lit, prog, ...),
-- when LuaSnip is installed
pcall(require, "tex2html.snippets")
