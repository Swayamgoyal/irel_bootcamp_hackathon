%% Fallback sdqbeamer class (compatibility shim)
%%
%% This repository does not vendor the official KIT sdqbeamer template.
%% If you have the official template installed, DELETE this file so LaTeX
%% uses the real KIT design instead.
%%
%% Goal: provide the commands used by docs/presentation.tex so the deck
%% compiles everywhere with standard Beamer.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{sdqbeamer}[2026/05/18 Fallback sdqbeamer compatibility class]

\LoadClass{beamer}

\RequirePackage{graphicx}
\RequirePackage{etoolbox}

% -------- Title image / group metadata --------
\newcommand{\sdq@titleimage}{}
\newcommand{\sdq@groupname}{}
\newcommand{\sdq@grouplogo}{}
\newcommand{\sdq@groupnamewidth}{50mm}

\newcommand{\titleimage}[1]{\renewcommand{\sdq@titleimage}{#1}}
\newcommand{\groupname}[1]{\renewcommand{\sdq@groupname}{#1}}
\newcommand{\grouplogo}[1]{\renewcommand{\sdq@grouplogo}{#1}}
\newcommand{\groupnamewidth}[1]{\renewcommand{\sdq@groupnamewidth}{#1}}

% -------- KIT title frame shim --------
\newcommand{\KITtitleframe}{%
  \begin{frame}[plain]
    \vspace*{-2mm}
    \begingroup
    \centering
    \ifstrempty{\sdq@titleimage}{}{%
      % Try common extensions; ignore if missing.
      \IfFileExists{\sdq@titleimage.pdf}{\includegraphics[width=\linewidth]{\sdq@titleimage}}{%
        \IfFileExists{\sdq@titleimage.png}{\includegraphics[width=\linewidth]{\sdq@titleimage}}{%
          \IfFileExists{\sdq@titleimage.jpg}{\includegraphics[width=\linewidth]{\sdq@titleimage}}{}%
        }%
      }%
      \vspace{3mm}
    }
    {\usebeamerfont{title}\inserttitle\par}
    \vspace{1mm}
    {\usebeamerfont{subtitle}\insertsubtitle\par}
    \vspace{2mm}
    \ifstrempty{\sdq@groupname}{}{\footnotesize \sdq@groupname\par\vspace{1mm}}
    \footnotesize \insertauthor\par
    \footnotesize \insertdate\par
    \endgroup
  \end{frame}
}

% -------- Backup slide numbering shim --------
\newcounter{sdq@framenumberbeforebackup}
\newcommand{\beginbackup}{\setcounter{sdq@framenumberbeforebackup}{\value{framenumber}}}
\newcommand{\backupend}{\setcounter{framenumber}{\value{sdq@framenumberbeforebackup}}}

% -------- Reasonable defaults (generic beamer) --------
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}[frame number]

\endinput
