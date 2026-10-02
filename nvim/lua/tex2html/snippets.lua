-- LuaSnip snippets for tex2html decks (titletemplates.sty), filetype tex.
-- Loaded by plugin/tex2html.lua when LuaSnip is installed. Type the trigger,
-- pick it from the completion menu (or expand it), then <Tab> through the
-- fields; default values can be accepted or typed over.

local ok, ls = pcall(require, "luasnip")
if not ok then return end
local s, i = ls.snippet, ls.insert_node
local fmta = require("luasnip.extras.fmt").fmta

local function snip(trig, desc, body, nodes)
  return s({ trig = trig, desc = "tex2html: " .. desc }, fmta(body, nodes))
end

local snippets = {
  snip("frame", "frame with a title", [[
\begin{frame}{<>}
	<>
\end{frame}]], { i(1, "Title"), i(0) }),

  snip("framesub", "frame with title and subtitle", [[
\begin{frame}{<>}{<>}
	<>
\end{frame}]], { i(1, "Title"), i(2, "Subtitle"), i(0) }),

  snip("cols", "two columns", [[
\begin{columns}[T]
	\begin{column}{<>\textwidth}
		<>
	\end{column}
	\begin{column}{<>\textwidth}
		<>
	\end{column}
\end{columns}]], { i(1, "0.48"), i(2), i(3, "0.48"), i(0) }),

  snip("rows", "two rows (share of the slide height)", [[
\begin{rows}
	\begin{row}{<>}
		<>
	\end{row}
	\begin{row}{<>}
		<>
	\end{row}
\end{rows}]], { i(1, "0.4"), i(2), i(3, "0.6"), i(0) }),

  snip("block", "block with a title", [[
\begin{block}{<>}
	<>
\end{block}]], { i(1, "Title"), i(0) }),

  snip("stab", "slidetable: style plain|lines|header|striped, first row = header", [[
\begin{slidetable}[<>]{<>}
	<> \\
	<> \\
\end{slidetable}]], { i(1, "striped"), i(2, "lcc"), i(3, "Case & A & B"), i(0, "row & 0 & 0") }),

  snip("lit", "literature table", [[
\begin{litreview}
	\study{<>}{<>}
\end{litreview}]], { i(1, "bibkey"), i(0, "What the study found.") }),

  snip("study", "literature table row", [[\study{<>}{<>}]],
       { i(1, "bibkey"), i(0, "What the study found.") }),

  snip("prog", "progress timeline: status done|ongoing|planned", [[
\begin{progress}
	\task[<>]{<>}{<>}
\end{progress}]], { i(1, "done"), i(2, "What"), i(0, "When") }),

  snip("task", "progress task: status done|ongoing|planned", [[\task[<>]{<>}{<>}]],
       { i(1, "done"), i(2, "What"), i(0, "When") }),

  snip("pubs", "publications: status published|accepted|review|submitted|preparation", [[
\begin{publications}
	\pubsection{<>}
	\pub[<>]{<>}
\end{publications}]], { i(1, "Journal articles"), i(2, "published"), i(0, "bibkey") }),

  snip("pub", "publication from the .bib", [[\pub[<>]{<>}]], { i(1, "published"), i(0, "bibkey") }),

  snip("note", "speaker note (presenter view only)", [[\note{<>}]], { i(0) }),

  snip("fig", "figure filling the width", [[\includegraphics[width=<>]{figures/<>}]],
       { i(1, "\\linewidth"), i(0, "file") }),

  snip("anim", "animation from numbered frames (several panels play in sync)", [[
\begin{animateinline}[autoplay, loop, controls]{<>}
	\multiframe{<>}{iT=<>+<>}{%
		\includegraphics[width=<>\linewidth]{figures/<>_\iT}%
	}
\end{animateinline}]], { i(1, "3"), i(2, "41"), i(3, "3000"), i(4, "50"), i(5, "0.48"), i(0, "frame") }),
}

ls.add_snippets("tex", snippets, { key = "tex2html" })
