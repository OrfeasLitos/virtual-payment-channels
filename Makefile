all: virtual-channels.pdf transactions-overview.pdf

#.ONESHELL:
virtual-channels.pdf: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log

transactions-overview.pdf: src/transactions-overview/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode transactions-overview.tex; \
	rm -rf transactions-overview.aux transactions-overview.log transactions-overview.out transactions-overview.toc transactions-overview.lof transactions-overview.lot transactions-overview.bbl transactions-overview.blg transactions-overview-autopp.out transactions-overview-pics.pdf transactions-overview-autopp.log

bib: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	bibtex virtual-channels.aux; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.pdf
