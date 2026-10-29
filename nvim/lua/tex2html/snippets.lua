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

  snip("figcap", "figure with numbered caption and label", [[
\begin{figure}
	\includegraphics[width=<>]{figures/<>}
	\caption{<>}\label{fig:<>}
\end{figure}]], { i(1, "0.8\\linewidth"), i(2, "file"), i(3, "Caption."), i(0, "name") }),

  snip("tabcap", "table with numbered caption (above) and label", [[
\begin{table}
	\caption{<>}\label{tab:<>}
	\begin{slidetable}[<>]{<>}
		<> \\
		<> \\
	\end{slidetable}
\end{table}]], { i(1, "Caption."), i(2, "name"), i(3, "plain"), i(4, "lcc"), i(5, "Case & A & B"), i(0, "row & 0 & 0") }),

  snip("anim", "animation: panels in sync (\\N = frame number), with caption and label", [[
\begin{figure}
	\begin{animation}[fps=<>, frames=<>]
		\animpanel{<>}{figures/<>_\N}
	\end{animation}
	\caption{<>}\label{fig:<>}
\end{figure}]], { i(1, "3"), i(2, "3000:5000:50"), i(3, "Label"), i(4, "frame"), i(5, "Caption."), i(0, "name") }),

  snip("video", "slidevideo: a video with a poster, in a figure with caption and label", [[
\begin{figure}
	\slidevideo[width=<>, poster=figures/<>]{figures/<>}
	\caption{<>}\label{fig:<>}
\end{figure}]], { i(1, "0.8\\linewidth"), i(2, "poster.png"), i(3, "video.mp4"), i(4, "Caption."), i(0, "name") }),

  snip("plot", "slideplot: lines from a data file, interactive in the HTML deck", [[
\begin{slideplot}[xlabel={<>}, ylabel={<>}, height=<>]
	\plotline[x=<>, y=<>, label={<>}]{<>}
\end{slideplot}]], { i(1, "$t$"), i(2, "$y$"), i(3, "5cm"), i(4, "time"), i(5, "y"), i(6, "Case 1"), i(0, "data/file.csv") }),

  snip("panels", "slideplot with panels (shared axes, one legend)", [[
\begin{slideplot}[columns=<>, xlabel={<>}, ylabel={<>}, legend=outer north]
	\plotpanel[title={<>}]
		\plotline[x=<>, y=<>, label={<>}]{<>}
\end{slideplot}]], { i(1, "2"), i(2, "$t$"), i(3, "$y$"), i(4, "Case 1"), i(5, "time"), i(6, "y"), i(7, "Label"), i(0, "data/file.csv") }),

  snip("annot", "annotate: shapes over a figure (grid shows the 0..1 coordinates)", [[
\begin{figure}
	\begin{annotate}[grid]
		\includegraphics[width=\textwidth]{figures/<>}
		\shape[color=<>]{<>}{<>}{<>}
	\end{annotate}
	\caption{<>}\label{fig:<>}
\end{figure}]], { i(1, "file"), i(2, "red"), i(3, "rect"), i(4, "0.4,0.1"), i(5, "0.6,0.9"), i(6, "Caption."), i(0, "name") }),

  snip("shape", "\\shape inside annotate: rect, ellipse, line, arrow, text", [[
\shape[color=<>]{<>}{<>}{<>}]], { i(1, "red"), i(2, "rect"), i(3, "0.4,0.1"), i(0, "0.6,0.9") }),

  snip("axes", "\\shape axes: coordinate indicator (origin, length as a fraction of the width)", [[
\shape[color=<>, xlabel=<>, ylabel=<>]{axes}{<>}{<>}]], { i(1, "black"), i(2, "$x$"), i(3, "$y$"), i(4, "0.1,0.1"), i(0, "0.1") }),

  snip("flow", "TikZ flowchart with the deck's flow styles", [[
\begin{tikzpicture}[flow]
	\node[flowstart] (start) {<>};
	\node[flowbox, below=of start] (step) {<>};
	\draw[flowarrow] (start) -- (step);<>
\end{tikzpicture}]], { i(1, "Start"), i(2, "Step"), i(0, "") }),

  snip("sshape", "\\slideshape: a shape placed on the whole slide", [[
\slideshape[color=<>]{<>}{<>}{<>}]], { i(1, "red"), i(2, "rect"), i(3, "0.1,0.1"), i(0, "0.3,0.3") }),
}

ls.add_snippets("tex", snippets, { key = "tex2html" })
