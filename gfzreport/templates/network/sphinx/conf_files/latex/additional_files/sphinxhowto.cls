%
% sphinxhowto.cls for Sphinx (http://sphinx-doc.org/)
% EDITED FOR THE REPORT GENERATION (SEE maketitle)
%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{sphinxhowto}[2009/06/02 Document class (Sphinx HOWTO)]

% 'oneside' option overriding the 'twoside' default
\newif\if@oneside
\DeclareOption{oneside}{\@onesidetrue}
% Pass remaining document options to the parent class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{\sphinxdocclass}}
\ProcessOptions\relax

% Default to two-side document
\if@oneside
% nothing to do (oneside is the default)
\else
\PassOptionsToClass{twoside}{\sphinxdocclass}
\fi

\LoadClass{\sphinxdocclass}

% Set some sane defaults for section numbering depth and TOC depth.  You can
% reset these counters in your preamble.
%
\setcounter{secnumdepth}{2}

% OVERRIDDEN FOR THE GFZ REPORT GENERATION TO MATCH GFZ STYLE
%
% create the command that makes the title string:
% arguments width, y. E.g. \maketitlestring{.8\linewidth}{20em}
% Note: the title box right side will be fixed to the right page side, so the
% title will be right aligned if width < \textwidth
\newcommand{\maketitletext}[2]{
	% leave the space below!! (problems ith vspace?) otherwise 

	\vspace*{#2}%
	\hfill\begin{tabular}{@{}p{#1}@{}}
		%\multicolumn{1}{@{}c@{}}{Some title} \\  % this is if we wanted to center the title inside the tabular (we don't)
		{\large \par \@author \par} \\
		{\LARGE \sffamily \bfseries \color{gfzblue} \@title \par}\\
	  	{\Large \sffamily \bfseries \color{gfzblue} \rstSubtitle \par} \\
	  	{\large \sffamily \bfseries \color{gfzblue} \rstSubSubtitle \par} \\
	  	{\Large Scientific Technical Report \rstStrNum} \\
	  	{\par \normalsize GIPP Experiment- and Data Archive}
	\end{tabular}
	% add a space below for the same reason (unkwnown) we added one above (FIXME. check why)

}

% reset the maketitle command:
\renewcommand{\maketitle}{
	% 1) copied from sphinxhowto.cls (the original one)
	\ifsphinxpdfoutput
		\begingroup
		% These \defs are required to deal with multi-line authors; it
		% changes \\ to ', ' (comma-space), making it pass muster for
		% generating document info in the PDF file.
		\def\\{, }
		\def\and{and }
		\pdfinfo{
		  /Author (\@author)
		  /Title (\@title)
		}
		\endgroup
	\fi

  	% 2) title page
  	% custom make title:
  	% print background picture:
	\tikz[remember picture,overlay] \node[opacity=1,inner sep=0pt] at (current page.center){\includegraphics[width=\paperwidth]{Cover_STR-Data_en_DH.front.pdf}};
	% make title text (preformatted, choose width and y of the title box as
	% arguments):
	\maketitletext{.8\linewidth}{20em}
	% FIXME: what are these? (uncomment all but setcounter, which makes sense)
  	% \py@authoraddress \par
  	% \@thanks
 
  	\setcounter{footnote}{0}
  	% \let\thanks\relax\let\maketitle\relax
	\clearpage
  
	% 3) second title page, with citations and stuff in the lower right corner:	  
	{\footnotesize
		
		Recommended citation:		 									\newline\newline
		\@author\ (\rstPublicationYear): \@title. Scientific Technical Report \rstStrNum, GFZ German Research Centre for Geosciences. doi: \rstDoi 				\newline\newline\newline
		\if\relax\rstSupplDatasets\relax\else{Supplementary datasets:}\fi   \newline\newline
		\rstSupplDatasets 													\newline\newline\newline
		\if\relax\rstCitationChapter\relax\else{Recommended citation for chapter:}\fi   \newline\newline
		\rstCitationChapter 													\newline\newline\newline
		\if\relax\rstSupplementsTo\relax\else{The report and the datasets are supplements to:}\fi   \newline\newline
		\rstSupplementsTo 													\newline\newline\newline
		
		% lower right corner:
		\begin{flushright}\vfill
			\begin{tabular}{r}
				{\normalsize Imprint} \\
				\\
				\includegraphics{gfz_wordmark_blue.png} \\
				\\
				Telegrafenberg \\
				D-14473 Potsdam  \\ 
				\\
				Published in Potsdam, Germany \\
				\rstPublicationMonth\ \rstPublicationYear \\
				ISSN \rstIssn \\
				DOI: \rstDoi \\
				URN: \rstUrn \\
				\\
				This work is published in the GFZ series \\
				Scientific Technical Report (STR) \\
				and electronically available at GFZ website \\
				www.gfz-potsdam.de \\
				\\
				\href{http://creativecommons.org/licenses/by-sa/4.0/}{\includegraphics{creativecommon_80x15.png}}
			\end{tabular}
		\end{flushright}
	}
	% no header and footer, and then clear page
	\thispagestyle{empty}
	\clearpage

	% 4) third page title, the same as the first but no background
	% (and a little bit left-shifted)
	\maketitletext{.85\linewidth}{20em}
	\thispagestyle{empty}
	\clearpage
}


\let\py@OldTableofcontents=\tableofcontents
\renewcommand{\tableofcontents}{
  \begingroup
    \parskip = 0mm
    \py@OldTableofcontents
  \endgroup
  \rule{\textwidth}{1pt}
  \vspace{12pt}
}  

\@ifundefined{fancyhf}{
  \pagestyle{plain}}{
  \pagestyle{normal}}		% start this way; change for
\pagenumbering{arabic}		% ToC & chapters

\thispagestyle{empty}

% Fix the bibliography environment to add an entry to the Table of
% Contents.
% For an article document class this environment is a section,
% so no page break before it.
\let\py@OldThebibliography=\thebibliography
\renewcommand{\thebibliography}[1]{
  \phantomsection
  \py@OldThebibliography{1}
  \addcontentsline{toc}{section}{\bibname}
}

% Same for the indices.
% The memoir class already does this, so we don't duplicate it in that case.
%
\@ifclassloaded{memoir}{}{
  \let\py@OldTheindex=\theindex
  \renewcommand{\theindex}{
    \phantomsection
    \py@OldTheindex
    \addcontentsline{toc}{section}{\indexname}
  }
}
